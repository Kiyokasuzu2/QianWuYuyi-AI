@@
         # publish event (best-effort)
         try:
             ev = proposal_events.proposal_created_event(proposal)
             self._publish_event(ev)
         except Exception:
             pass
+
+        # publish ProposalCreated event if event_bus available
+        try:
+            if hasattr(self, "event_bus") and self.event_bus:
+                actor = "proposal_manager"
+                try:
+                    if isinstance(evaluator_meta, dict) and evaluator_meta.get("author"):
+                        actor = evaluator_meta.get("author")
+                except Exception:
+                    pass
+                ev = {
+                    "type": "ProposalCreated",
+                    "proposal_id": proposal.id,
+                    "source_event_id": proposal.source_event_id,
+                    "confidence": getattr(proposal, "confidence", None),
+                    "evidence_ids": getattr(proposal, "evidence_ids", []),
+                    "actor": actor,
+                    "timestamp": datetime.utcnow().strftime("%Y-%m-%dT%H:%M:%S.%fZ"),
+                }
+                try:
+                    self.event_bus.publish(ev)
+                except Exception:
+                    pass
+        except Exception:
+            pass
@@
         if self.auto_accept_enabled and proposal.confidence >= self.auto_accept_threshold:
             try:
                 self.accept_proposal(proposal.id, actor="system", auto=True)
             except Exception:
                 # swallow in MVP
                 pass
