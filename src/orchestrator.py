---
*** Begin Patch
*** Update File: src/orchestrator.py
@@
 from src.identity.user_context import UserContext
 from src.identity.user_resolver import UserResolver
+from src.runtime.runtime_context import RuntimeContext
@@
     def __init__(self):
@@
         self._init_memory_index()
+        # RuntimeContext for assembling prioritized context (agreements-first)
+        self.runtime_context = RuntimeContext()
@@
         def process(self, user_message: str) -> str:
@@
-        # Step 3: 获取当前人格
+        # === Assemble prioritized runtime context early (agreements-first) ===
+        try:
+            assembled_context = self.runtime_context.assemble_context(
+                user_id=self.target_user_id,
+                conversation={"recent_turns": self.history[-10:]},
+                self_model_snapshot=self.self_model_context_provider.get_context(),
+                memory_summary={"recent_memories": chat_memories},
+                options={"relationship_summary": getattr(self, "relationship_profile", None)},
+            )
+        except Exception as e:
+            # Fail gracefully: log trace and continue without assembled context
+            print(f"[Orchestrator] runtime context assembly failed: {e}")
+            assembled_context = None
+
+        # Step 3: 获取当前人格
         personality = self.personality_resolver.resolve()
         self.current_personality = personality
         personality_context = self._get_personality_context(personality)
@@
-        # Step 4：生成回复
-        reply = self.engine.generate(
-            user_message=user_message,
-            history=self.history,
-            chat_memories=chat_memories,
-            life_events=life_events,
-            personality_context=personality_context,
-            resolved_behavior=resolved_behavior_data,
-            self_model_context=self_model_ctx,
-            emotion_context=emotion_ctx,
-            relationship_context=relationship_ctx,
-        )
+        # Step 4：生成回复
+        # If assembled_context is available, prefer using its prompt_blocks to build the prompt
+        if assembled_context:
+            prompt_blocks = assembled_context.get("prompt_blocks", [])
+            # The engine.generate API accepts an optional 'context_prompt_blocks' argument
+            # to allow upstream systems to inject system-level messages (agreements first).
+            reply = self.engine.generate(
+                user_message=user_message,
+                history=self.history,
+                chat_memories=chat_memories,
+                life_events=life_events,
+                personality_context=personality_context,
+                resolved_behavior=resolved_behavior_data,
+                self_model_context=self_model_ctx,
+                emotion_context=emotion_ctx,
+                relationship_context=relationship_ctx,
+                context_prompt_blocks=prompt_blocks,
+            )
+        else:
+            reply = self.engine.generate(
+                user_message=user_message,
+                history=self.history,
+                chat_memories=chat_memories,
+                life_events=life_events,
+                personality_context=personality_context,
+                resolved_behavior=resolved_behavior_data,
+                self_model_context=self_model_ctx,
+                emotion_context=emotion_ctx,
+                relationship_context=relationship_ctx,
+            )
*** End Patch
