@@
 class EmotionManager:
@@
     def process_event(self, event: EmotionEvent, memory_id: Optional[str] = None):
         """处理情绪事件，更新内部状态并持久化轨迹"""
         delta = self.engine.process(event)
-        self.state = self.state.apply_delta(delta)
-        self.repository.save(self.state)
-
-        trace = self.bridge.bind(event, memory_id=memory_id)
-        self.trace_repository.append(trace)
+        old_state = self.state.to_dict() if hasattr(self.state, 'to_dict') else None
+        self.state = self.state.apply_delta(delta)
+        self.repository.save(self.state)
+
+        trace = self.bridge.bind(event, memory_id=memory_id)
+        self.trace_repository.append(trace)
+
+        # publish EmotionChanged event if event_bus available
+        try:
+            if hasattr(self, 'event_bus') and self.event_bus:
+                ev = {
+                    "type": "EmotionChanged",
+                    "user_id": getattr(event, 'user_id', None),
+                    "old_state": old_state,
+                    "new_state": self.state.to_dict() if hasattr(self.state, 'to_dict') else str(self.state),
+                    "timestamp": datetime.utcnow().strftime("%Y-%m-%dT%H:%M:%S.%fZ"),
+                }
+                try:
+                    self.event_bus.publish(ev)
+                except Exception:
+                    pass
+        except Exception:
+            pass
@@
     def _save_counter(self):
         self._counter_file.parent.mkdir(parents=True, exist_ok=True)
         with open(self._counter_file, "w", encoding="utf-8") as f:
             json.dump({"count": self._analysis_counter}, f)
