"""ProposalStore (implementation - MVP)

Append-only JSONL store for GrowthProposal objects.

Behavior (MVP):
- save(proposal): append proposal.to_dict() as a JSON line
- update(proposal): append updated proposal as JSON line (last-wins semantics)
- load(proposal_id): scan file and return latest proposal dict -> GrowthProposal
- list(status=None,...): return latest snapshot per id, optionally filter by status
- exists_similar(source_event_id, fingerprint): scan for matching source_event_id + fingerprint

This is a simple, single-process implementation suitable for MVP. It uses fsync after write
for durability. Concurrency (multi-process) is NOT handled beyond atomic append guarantees of the OS.
"""
from __future__ import annotations
import json
import os
from pathlib import Path
from typing import Optional, List, Dict, Any

from src.contracts import growth_schema


class ProposalStore:
    def __init__(self, path: Optional[str] = None):
        self.path = Path(path or "data/proposals/proposals.jsonl")
        self.path.parent.mkdir(parents=True, exist_ok=True)
        # ensure file exists
        if not self.path.exists():
            self.path.write_text("", encoding="utf-8")
        # in-memory index (id -> last parsed dict)
        self._cache: Dict[str, Dict[str, Any]] = {}
        # lazy-load cache from file
        self._load_index()

    def _load_index(self) -> None:
        """Load the latest version of each proposal into memory cache."""
        self._cache = {}
        try:
            with open(self.path, "r", encoding="utf-8") as f:
                for line in f:
                    line = line.strip()
                    if not line:
                        continue
                    try:
                        obj = json.loads(line)
                        pid = obj.get("id")
                        if pid:
                            self._cache[pid] = obj
                    except json.JSONDecodeError:
                        # skip malformed lines
                        continue
        except FileNotFoundError:
            self._cache = {}

    def _append_line(self, obj: Dict[str, Any]) -> None:
        data = json.dumps(obj, ensure_ascii=False)
        # atomic append with flush + fsync
        with open(self.path, "a", encoding="utf-8") as f:
            f.write(data + "\n")
            f.flush()
            try:
                os.fsync(f.fileno())
            except Exception:
                # fsync may not be available on some platforms; ignore
                pass

    def save(self, proposal: growth_schema.GrowthProposal) -> None:
        """Persist a new proposal by appending a JSON line. Updates in-memory cache."""
        obj = proposal.to_dict()
        # ensure id present
        if not obj.get("id"):
            raise ValueError("proposal must have an id")
        self._append_line(obj)
        self._cache[obj["id"]] = obj

    def update(self, proposal: growth_schema.GrowthProposal) -> None:
        """Append updated proposal record. Last-wins semantics."""
        obj = proposal.to_dict()
        if not obj.get("id"):
            raise ValueError("proposal must have an id")
        self._append_line(obj)
        self._cache[obj["id"]] = obj

    def load(self, proposal_id: str) -> Optional[growth_schema.GrowthProposal]:
        """Return GrowthProposal instance for latest record with proposal_id, or None."""
        data = self._cache.get(proposal_id)
        if not data:
            return None
        try:
            return growth_schema.GrowthProposal.from_dict(data)
        except Exception:
            return growth_schema.GrowthProposal.from_dict(data)

    def list(self, status: Optional[str] = None, limit: int = 50, offset: int = 0) -> List[growth_schema.GrowthProposal]:
        """Return list of latest proposals, optionally filtered by status.
        Offset/limit applied after filtering.
        """
        items = list(self._cache.values())
        if status:
            items = [i for i in items if i.get("status") == status]
        def _ts_key(item: Dict[str, Any]):
            return item.get("timestamp") or item.get("id")
        items.sort(key=_ts_key)
        sliced = items[offset : offset + limit]
        return [growth_schema.GrowthProposal.from_dict(i) for i in sliced]

    def exists_similar(self, source_event_id: str, fingerprint: str) -> Optional[str]:
        """Detect duplicates by source_event_id plus fingerprint of changes.
        Returns existing proposal id if found, else None.
        """
        for pid, obj in self._cache.items():
            if obj.get("source_event_id") == source_event_id:
                pcs = obj.get("proposed_changes", [])
                try:
                    key = json.dumps(pcs, sort_keys=True, ensure_ascii=False)
                except Exception:
                    key = str(pcs)
                if key == fingerprint:
                    return pid
        return None
