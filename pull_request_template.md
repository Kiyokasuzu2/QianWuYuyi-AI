---
title: "feat(runtime): inject IMMUTABLE agreements-first context into Orchestrator and integrate RuntimeContext"
---

This PR integrates a RuntimeContext that prioritizes IMMUTABLE agreements (such as the Yuyi Manifesto) and injects them as system-level messages before building the prompt for the ResponseEngine.

Why
- Prevent prompt-injection or normal conversation from overriding core agreements and beliefs.
- Centralize context assembly in a single place (agreements -> self_model -> relationship -> memory -> recent turns).

What
- Add `src/runtime/runtime_context.py` — loads `src/storage/agreements/*.json`, filters IMMUTABLE entries, and assembles a prioritized context with `prompt_blocks` and `trace`.
- Add `src/runtime/yuyi_runtime_integration.py` — a minimal integration shim showing how to call `RuntimeContext` from a runtime lifecycle entrypoint.
- Modify `src/orchestrator.py` — call `RuntimeContext.assemble_context()` early in `process()` and pass `context_prompt_blocks` to `ResponseEngine.generate(...)` (falling back if unavailable).
- Persist initial `self_model.json`, `narrative_history.json`, and `agreements/manifesto.json` as initial data.
- Add `tests/test_manifesto_persistence.py` to assert manifesto exists and is IMMUTABLE.

Testing
- Unit tests included to validate the manifesto persistence. Additional integration tests recommended after deployment.

Rollback
- Close this PR or revert the merge commit to roll back.
