@@
 class Orchestrator:
     def __init__(self, runtime_context=None):
         self.runtime_context = runtime_context
-        self.event_bus = getattr(runtime_context, 'event_bus', None)
+        self.event_bus = getattr(runtime_context, 'event_bus', None)
@@
         # other initialization...
+
+        # subscribe to events if event_bus is available
+        try:
+            if hasattr(self, "event_bus") and self.event_bus:
+                try:
+                    self.event_bus.subscribe("MemoryCreated", self.on_memory_created)
+                    self.event_bus.subscribe("EmotionChanged", self.on_emotion_changed)
+                    self.event_bus.subscribe("ProposalCreated", self.on_proposal_created)
+                except Exception:
+                    pass
+        except Exception:
+            pass
@@
     def some_existing_method(self):
         pass
+
+    # Event handlers (placeholders)
+    def on_memory_created(self, ev: dict):
+        try:
+            print("[Orchestrator] MemoryCreated event:", ev)
+        except Exception:
+            pass
+
+    def on_emotion_changed(self, ev: dict):
+        try:
+            print("[Orchestrator] EmotionChanged event:", ev)
+        except Exception:
+            pass
+
+    def on_proposal_created(self, ev: dict):
+        try:
+            print("[Orchestrator] ProposalCreated event:", ev)
+        except Exception:
+            pass
