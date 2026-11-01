# AI environment verification

Date: 2026-11-01. The following is a desk-check by the current agent against the instructions, not independent execution or a measurement of automatic routing.

| Skill | Positive request / desk-check result | Negative request / expectation |
|---|---|---|
| crisp-dm-step | “Plan Data understanding” → goal DATA-01, inputs: requirements, next artifact: dataset search log, exit: suitability and licenses checked before synthetic data; open: domain/language; phase pending | “Fix a typo in README” → do not apply |
| evaluate-component | “Evaluate conflict detection” → design: precision/recall on gold issues, S03 as seed; blockers: component, contract, dataset, and harness missing; status: not run; no scores | “Add a link to README” → do not apply |
| review-deliverable | “Review the scaffold” → instructions, skills, requirement provenance exist; overall submission pending: runtime, evaluation runs, diagram, video missing | “Explain list comprehension” → do not apply |

This checks procedure boundaries and expected outputs. Negative examples are a manual check against the description, not an actually observed selection by another session.

## Fresh-chat acceptance - not yet performed

In a new chat at the root, ask for loaded instructions, current stage, next task, and unapproved decisions. Check availability of the three skills with one positive and one negative request each from above. Record actual routing/output, distinguishing explicit invocation from implicit selection. If discovery has not refreshed, restart the session.

## Reproduction

`python scripts/check_environment.py` checks artifacts without dependencies/API. The bundled skill-creator quick_validate.py checks skill metadata when the tool is available. Repeat the checker in a clean checkout after the first commit. The existence of files does not prove the model loaded them.
