@@
         memories.append(memory)
 
         self._save(memories)
 
+        # publish MemoryCreated event if event_bus is available
+        try:
+            if hasattr(self, 'event_bus') and self.event_bus:
+                ev = {
+                    "type": "MemoryCreated",
+                    "memory_id": memory.get("id"),
+                    "user_id": memory.get("user_id"),
+                    "key": memory.get("metadata", {}).get("key"),
+                    "timestamp": datetime.utcnow().strftime("%Y-%m-%dT%H:%M:%S.%fZ"),
+                }
+                try:
+                    self.event_bus.publish(ev)
+                except Exception:
+                    pass
+        except Exception:
+            pass
+
         return memory
@@
         except Exception as e:
 
             print(
                 f"[MemoryStore] save failed: {e}"
             )
