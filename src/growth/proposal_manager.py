"""ProposalManager implementation (MVP)

Implements core lifecycle: create_proposal, get_proposal, list_proposals, accept_proposal, reject_proposal.
Behavior:
- create_proposal: build proposal, dedupe by fingerprint, persist via ProposalStore, audit and event hooks (no-op if absent)
- accept_proposal: idempotent; attempts to apply via PersonalityAdapter.apply_proposal; on success, sets status=accepted, accepted_at timestamp and persists.
- reject_proposal: mark rejected, persist, write audit, publish event.

Notes:
- This is an MVP single-process implementation; concurrency and distributed locks are out of scope.
- auto_accept_enabled defaults to False and is not used unless configured in config passed to ProposalManager.
"""
from __future__ import annotations
from typing import List, Optional, Dict, Any
from datetime import datetime
import json

from src.contracts import growth_schema, audit_schema
from src.growth.proposal_store import ProposalStore
from src.personality.personality_adapter import PersonalityAdapter
from src.runtime.runtime_context import RuntimeContext  # may be None in runtime
from src.growth import proposal_events

def now_iso() -> str:
    return datetime.utcnow().isoformat() + "Z"

class ProposalManager:
    def __init__(self, runtime_context: Optional[RuntimeContext] = None, store: Optional[ProposalStore] = None, config: Optional[Dict[str, Any]] = None):
        self.runtime_context = runtime_context
        self.store = store or ProposalStore()
        self.personality_adapter = PersonalityAdapter(runtime_context=runtime_context)
        self.config = config or {}
        # runtime hooks (may be None)
        self.audit = getattr(runtime_context, "audit_logger", None)
        self.event_bus = getattr(runtime_context, "event_bus", None)
        self.snapshot = getattr(runtime_context, "snapshot_manager", None)
        # default config (auto_accept disabled by default)
        self.auto_accept_enabled = bool(self.config.get("auto_accept_enabled", False))
        self.auto_accept_threshold = float(self.config.get("auto_accept_threshold", 0.95))

    def _compute_fingerprint(self, proposed_changes: List[growth_schema.ChangeItem]) -> str:
        try:
            pcs = [c.__dict__ if hasattr(c, "__dict__") else c for c in proposed_changes]
            return json.dumps(pcs, sort_keys=True, ensure_ascii=False)
        except Exception:
            return str(proposed_changes)

    def create_proposal(self, source_event: Dict[str, Any], proposed_changes: List[growth_schema.ChangeItem], confidence: float, evidence_ids: List[str], evaluator_meta: Dict[str, Any]) -> growth_schema.GrowthProposal:
        """
        Create and persist a GrowthProposal. Returns existing proposal if duplicate detected.
        """
        proposal = growth_schema.GrowthProposal(
            source_event_id=(source_event.get("id") if isinstance(source_event, dict) else None),
            proposed_changes=proposed_changes,
            confidence=confidence,
            evidence_ids=evidence_ids,
            evaluator_meta=evaluator_meta,
        )

        fingerprint = self._compute_fingerprint(proposed_changes)
        existing = None
        try:
            existing_id = self.store.exists_similar(proposal.source_event_id, fingerprint)
            if existing_id:
                existing = self.store.load(existing_id)
        except Exception:
            # best-effort dedupe; ignore failures
            existing = None

        if existing:
            return existing

        # persist
        self.store.save(proposal)

        # audit record for creation
        try:
            entry = audit_schema.AuditEntry(
                component="growth",
                actor="proposal_manager",
                reason="proposal_created",
                source_event_id=proposal.source_event_id,
                evidence_memory_ids=proposal.evidence_ids,
                after={"proposal_id": proposal.id},
            )
            self._record_audit(entry)
        except Exception:
            pass

        # publish event (best-effort)
        try:
            ev = proposal_events.proposal_created_event(proposal)
            self._publish_event(ev)
        except Exception:
            pass

        # auto-accept disabled by default; if enabled and meets threshold, accept
        if self.auto_accept_enabled and proposal.confidence >= self.auto_accept_threshold:
            try:
                self.accept_proposal(proposal.id, actor="system", auto=True)
            except Exception:
                # swallow in MVP
                pass

        return proposal

    def get_proposal(self, proposal_id: str) -> Optional[growth_schema.GrowthProposal]:
        return self.store.load(proposal_id)

    def list_proposals(self, status: Optional[str] = None, limit: int = 50, offset: int = 0) -> List[growth_schema.GrowthProposal]:
        return self.store.list(status=status, limit=limit, offset=offset)

    def accept_proposal(self, proposal_id: str, actor: str = "system", auto: bool = False) -> growth_schema.GrowthProposal:
        """
        Accept proposal: idempotent. Attempts to apply via PersonalityAdapter.
        On successful apply, sets status=accepted, accepted_at timestamp and persists.
        If apply is not performed (adapter returns applied=False), proposal remains in 'proposed'.
        """
        proposal = self.store.load(proposal_id)
        if not proposal:
            raise KeyError(f"Proposal {proposal_id} not found")

        if proposal.status == "accepted":
            return proposal

        # map to evolution record
        try:
            ev_record = self.personality_adapter.map_proposal_to_evolution_record(proposal)
        except NotImplementedError:
            # mapping not implemented in adapter skeleton
            ev_record = None
        except Exception:
            ev_record = None

        applied = False
        before = None
        after = None
        note = None

        try:
            result = self.personality_adapter.apply_proposal(proposal, actor=actor)
            if isinstance(result, dict):
                applied = bool(result.get("applied", False))
                before = result.get("before")
                after = result.get("after")
                note = result.get("note")
        except NotImplementedError:
            # adapter not implemented; treat as not applied
            applied = False
        except Exception as e:
            # record failure but do not change status
            applied = False
            note = f"apply_exception: {e}"

        if applied:
            # mark accepted
            proposal.status = "accepted"
            proposal.accepted_at = now_iso()
            self.store.update(proposal)

            # audit entry for acceptance
            try:
                entry = audit_schema.AuditEntry(
                    component="personality",
                    actor=actor,
                    reason="proposal_accepted",
                    source_event_id=proposal.source_event_id,
                    evidence_memory_ids=proposal.evidence_ids,
                    before=before,
                    after=after,
                )
                self._record_audit(entry)
            except Exception:
                pass

            # snapshot
            try:
                if self.snapshot:
                    # best-effort snapshot API
                    try:
                        self.snapshot.create_snapshot(reason="proposal.accept", evidence_ids=proposal.evidence_ids)
                    except Exception:
                        pass
            except Exception:
                pass

            # publish event
            try:
                ev = proposal_events.proposal_accepted_event(proposal)
                self._publish_event(ev)
            except Exception:
                pass

        else:
            # Not applied: write an audit note indicating manual intervention required
            try:
                entry = audit_schema.AuditEntry(
                    component="personality",
                    actor=actor,
                    reason="proposal_apply_skipped",
                    source_event_id=proposal.source_event_id,
                    evidence_memory_ids=proposal.evidence_ids,
                    after={"note": note} if note else None,
                )
                self._record_audit(entry)
            except Exception:
                pass

        return proposal

    def reject_proposal(self, proposal_id: str, actor: str = "system", reason: Optional[str] = None) -> growth_schema.GrowthProposal:
        proposal = self.store.load(proposal_id)
        if not proposal:
            raise KeyError(f"Proposal {proposal_id} not found")

        if proposal.status == "rejected":
            return proposal

        proposal.status = "rejected"
        proposal.rejected_at = now_iso()
        # Optionally store rejection reason in evaluator_meta
        if reason:
            meta = proposal.evaluator_meta or {}
            meta["rejection_reason"] = reason
            proposal.evaluator_meta = meta

        self.store.update(proposal)

        # audit
        try:
            entry = audit_schema.AuditEntry(
                component="growth",
                actor=actor,
                reason="proposal_rejected",
                source_event_id=proposal.source_event_id,
                evidence_memory_ids=proposal.evidence_ids,
                after={"proposal_id": proposal.id, "rejection_reason": reason},
            )
            self._record_audit(entry)
        except Exception:
            pass

        # publish event
        try:
            ev = proposal_events.proposal_rejected_event(proposal)
            self._publish_event(ev)
        except Exception:
            pass

        return proposal

    # Helper methods (non-invasive; no runtime changes)
    def _publish_event(self, ev):
        if self.event_bus:
            try:
                self.event_bus.publish(ev)
            except Exception:
                # swallow exceptions in MVP; keep system resilient
                if self.audit:
                    try:
                        self.audit.record(audit_schema.AuditEntry(component="runtime", actor="proposal_manager", reason="event_publish_failed", after={"event": getattr(ev, "to_dict", lambda: {})()}))
                    except Exception:
                        pass

    def _record_audit(self, entry: audit_schema.AuditEntry):
        if self.audit:
            try:
                self.audit.record(entry)
            except Exception:
                # no-op on audit failure for MVP
                pass
