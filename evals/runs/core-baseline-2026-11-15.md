# Offline core baseline

Status: executed 2026-11-15. First structural baseline, not an NLP evaluation.

- Requirements: BA-03, BA-05, BA-06, BA-07; partial OPS-01 (invalid/stale payload handling only).
- Code: HEAD `342c006b72f96f49476cc38a5853f91649be8be9`, dirty working tree. Added `ba_assistant/models.py`, `session.py`, `validation.py`, `tests/test_domain.py`, `pyproject.toml`, `uv.lock`. Earlier data/document changes are also uncommitted. No baseline implementation existed to compare against.
- Environment: Windows, Python 3.14.7, uv 0.12.15, Pydantic 2.14.3; pytest/Ruff versions are locked in uv.lock.
- Data: hand-authored domain fixtures in `tests/test_domain.py`; structural scenarios corresponding to S06/S07 and review/finalization cases. Existing dataset integrity tests inspect v0.1 metadata and evidence; held-out examples were not passed to any model or used for prompt tuning.
- Model, prompt, sampling parameters: not applicable; no LLM or external business API calls. Dependency installation was the only setup network activity.
- Commands: `uv run --frozen --no-sync pytest -q` and `uv run --frozen --no-sync ruff check .`.
- Result: 35/35 tests passed, 0 failures; pytest reported 1.77 seconds. Of these, 28 are domain-core cases (including parameterized cases) and 7 are dataset-checker cases. Ruff reported all checks passed. Timing is for this local test run, not model latency.
- Invariant evidence: rejects unknown/non-requirement task links; zero/two accountable roles; missing responsible role; unknown team roles/tasks; duplicate task/role IDs; stale artifacts; automatic confirmation fields; invalid source quotes; generation without explicit action. Positive fixture exercises reviewed state through validated JSON export.
- State evidence: invalid analysis leaves state unchanged; a new user message invalidates final output; fact revisions preserve IDs/history and require confirmation again; model omission cannot clear an issue; conflict severity cannot be downgraded; returned snapshots do not mutate the session.
- Review finding fixed: reopening an issue after a fact revision previously retained its original temporal boundary, permitting reuse of an old resolution answer. The controller now resets that boundary; regression test requires a new answer. Also rejects string values such as `"false"` for the user-confirmation action. Both regressions are included in the 35-test total.
- Scope limits: tests validate structural rejection/acceptance, not correctness of extracted facts, detection of real contradictions, semantic quality of resolutions, specification completeness or acceptance-criteria quality. RACI roles must be represented atomically; semantic role splitting is not implemented. No HTTP adapter, timeout/429 tests, retry policy, UI, Markdown renderer or full clean-checkout run yet. JSON export includes session history.
- Semantic baseline, human rubric scores, accuracy/F1, API latency/cost: not run/not applicable. No success percentage for generated final documents is claimed from these fixtures.
- Review: Codex used evaluate-component to distinguish structural evidence from pending semantic evaluation, and review-deliverable to inspect implementation and fix the temporal-resolution edge case. This is not independent human code review.
- Next experiment: implement mocked provider failure cases (S08), then run the first analyzer baseline only after model/budget selection and review of the examples used for scoring.
