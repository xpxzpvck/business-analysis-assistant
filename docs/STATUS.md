# Current status

Updated: 2026-11-15. Implementation, evaluation and documentation are committed and pushed to `main`. Only the video recording remains. No deployment or paid inference is authorized. Use uv; one developer/agent by default.

## Implemented

- Local Streamlit assistant: OpenRouter connection → Dialogue → Review → Documents. No demo mode (D-017); analysis and generation always use the LLM.
- Route: openrouter/free with zero-price filters and reasoning disabled (D-016, D-018); no model-selection UI. Old Ling sessions migrate on rerun. Keys stay in memory and can be replaced without losing dialogue.
- Analyzer v3 extracts evidence-backed facts and reconciles clarification issues. Human confirmation stays separate. Generator v3 produces specification, tasks, criteria and RACI; strict validation gates export (D-018).
- State revisions, rejected-fact recovery, pending-analysis retry, separate generation deadline, explicit schema-repair retries and Markdown/JSON exports.
- Report with two diagrams, evaluation records, export/component evaluators, dataset checker and server-start probe. The video script is kept locally, outside the repository.

## Actual evidence

| Check | Latest result |
|---|---|
| Clean GitHub clone (3e87cf5), new uv environment | uv sync --frozen, 144 pytest, Ruff, environment, dataset, LF freeze and Streamlit launch (HTTP 200) PASS; Python 3.13.15; Windows |
| Regression suite | 144 passed |
| Dataset | 8 dev / 4 reserved test; all 12 annotations approved by the user (3 on 2026-11-12, 9 on 2026-11-15 without label changes) |
| Live evaluation v2 → v3 | Dev category F1 20% → 71.8% end-to-end / 96.6% on successful calls; reserved test 76.9%; conflict with both facts kept 0/1 → 4/4; generator fully valid 0/1 → 2/7 attempts. [v2](../evals/runs/components-2026-11-15.md), [v3](../evals/runs/components-v3-2026-11-15.md) |
| User-supplied export (state 19) | 6/6 requirements covered; 9/9 valid task references; 7/7 specification references; 9/9 valid RACI |

## Next step

Record the video using the local script. Optional improvements that need user approval first: pin one free model with 3 repeats per case for evaluation (changes D-016), safe provider error-code diagnostics, semantic fact matching / question rubric.

## Limits

- Metrics measure category presence, not semantic fact-level F1. The sample is small (3 dev + 4 test cases, 1–3 repeats) and the free router picks a different model per request.
- Free models produce 429, fast HTTP 400 (cause unknown; provider error text is not stored by design) and truncated outputs. Errors are handled safely but not eliminated.
- Remaining semantic errors: occasional false "goal" from a project label, vague input turned into a requirement, one missed requirement on test; a generated task linked to requirements only formally.
- Session persistence is memory-only. Fresh Codex skill discovery is unverified.

## Where to continue

- [Requirements and submission checklist](REQUIREMENTS.md)
- [Current architecture and decision history](ARCHITECTURE.md)
- [Short report](REPORT.md)
- [Evaluation plan and data provenance](../evals/PLAN.md)
- [Dataset review packet](../evals/data/README.md)

## Historical evidence

Earlier increments are recorded in evals/runs and git history; read only the record relevant to a change: [core](../evals/runs/core-baseline-2026-11-15.md), [adapter](../evals/runs/adapter-baseline-2026-11-15.md), [workflow](../evals/runs/workflow-baseline-2026-11-15.md), [UI/export](../evals/runs/ui-exports-2026-11-15.md), [free mode](../evals/runs/free-mode-2026-11-15.md), [schema repair](../evals/runs/schema-repair-2026-11-15.md), [chat clarification](../evals/runs/chat-clarification-2026-11-15.md), [generator format](../evals/runs/generator-format-2026-11-15.md), [free router](../evals/runs/free-router-2026-11-15.md), [submission review](../evals/runs/submission-review-2026-11-15.md). They describe states at the time they were written, not current completeness.
