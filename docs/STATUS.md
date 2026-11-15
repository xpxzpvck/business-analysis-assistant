# Current status

Updated: 2026-11-15. Working implementation is uncommitted. No deployment or paid inference is authorized. Use uv; one developer/agent by default.

## Implemented

- Local Streamlit assistant: OpenRouter connection → Dialogue → Review → Documents. Demo mode removed per D-017; no analysis/generation without an LLM connection.
- Active route: openrouter/free (D-016); no additional model-selection UI. Old Ling sessions migrate on rerun. Keys stay in memory and can be replaced without losing dialogue.
- Analyzer v3 extracts evidence-backed facts and reconciles clarification issues (D-018). Human confirmation stays separate. Generator v3 produces specification, tasks, criteria and RACI; strict validation gates export.
- State revisions, rejected-fact recovery, pending-analysis retry, separate generation deadline, explicit schema-repair retries and Markdown/JSON exports.
- Report, video script, export evaluator and isolated server-start probe exist. Video is not recorded.

## Actual evidence

| Check | Latest completed result |
|---|---|
| Fresh source copy, new uv environment | uv sync --frozen PASS; Python 3.13.15; not a committed-release checkout |
| Latest regression suite | 144 passed in 11.16s (v3, after adapter revert); earlier fresh-copy run: 139 passed in 19.26s |
| Ruff, environment and dataset checks | PASS; dataset has 8 dev / 4 reserved test cases |
| Isolated Streamlit launch | HTTP 200; temporary process stopped; not visual browser QA |
| One user-supplied generated export | 6/6 requirements covered; 9/9 valid task references; 7/7 valid specification references; 9/9 valid RACI |
| v3 live evaluation | Dev category F1 71.8% end-to-end / 96.6% successful calls (v2: 20%); test 76.9% (gold reviewed, unchanged); generator 2/7 fully valid. [Record](../evals/runs/components-v3-2026-11-15.md) |
| Data annotation review | All 12 approved by the user (DEV-S02/03/06 on 2026-11-12; remaining nine on 2026-11-15 without label changes); check_dataset: 0 pending |

The supplied export is state 19; its original model/latency/confirmation history remain unknown. It was also used as a confirmed-fact input fixture in the separate controlled run below. Corrected Markdown apostrophes and RACI legend were inspected.

## Current work and next step

v2 → v3 iteration completed and documented (D-018, [run record](../evals/runs/components-v3-2026-11-15.md)). A post-freeze edit had removed `reasoning: {enabled: false}` from the free route; probes showed it makes a reasoning model spend 3901/4096 tokens and return empty content, so it was reverted with its test; sources match v3-freeze again (check_freeze PASS). Actual checks: 144 pytest passed, Ruff, environment, dataset and freeze checks PASS; one new official dev run (20261115T164858Z): analyzer 2/3 (DEV-S06 fast HTTP 400), generator success 6/6 · 8/8 · 8/8; three diagnostic generator probes recorded in the run record. Cause of fast HTTP 400 is still unknown (adapter does not keep provider error text by design). README, REPORT, ARCHITECTURE, PLAN, REQUIREMENTS and VIDEO updated; VIDEO narration grew by one paragraph and needs re-timing. Not committed.

Line endings fixed 2026-11-15: a clean GitHub clone failed check_freeze because the original freeze and dataset manifest hashed a local working copy with CRLF, while Git stores LF. Verified all 21 frozen files equal the committed content modulo CRLF; added .gitattributes (eol=lf), converted the working copy, recorded evals/runs/v3-freeze-lf-2026-11-15.json and rehashed the dataset manifest. No content change; v3 prompts are now sent with LF instead of CRLF.

Gold review completed 2026-11-15: the user approved all nine pending annotations without changes, including TEST-S01 (no facts) and TEST-S04 (booking requirement) where v3 erred; only review metadata and manifest hashes changed, so all metrics stand. test_dataset_checks now expects 0 pending; 144 pytest, Ruff, dataset and freeze checks PASS.

Next: record video. Proposals needing user approval: pin one free model with 3 repeats per case for evaluation (changes D-016), safe provider error-code diagnostics, semantic fact matching / question rubric.

Report/video documentation updated: user-created system-architecture.png and requirements-workflow.png were visually inspected and embedded in REPORT with captions and abstraction notes. VIDEO now contains a full Ukrainian script targeting 9:40, exact screen actions, narration, example inputs, provider-failure alternatives and requirement coverage. Narration has 994 words including mutually exclusive variants; timing still requires rehearsal, not a claimed recorded duration. Used review-deliverable; environment/link checker and git diff --check PASS. Runtime unchanged; no tests/API rerun needed. Video recording remains outstanding.

Completed [component evaluation baseline](../evals/runs/components-2026-11-15.md), run 20261115T135023Z: three live dev analyzer calls and one generator call. Analyzer 2/3 structurally accepted; third returned provider_error 502. Category-presence micro P=50%, R=12.5%, F1=20% including failed input as empty prediction (not fact-semantic F1). Conflict detected in 1/1 positive case, but conflicting facts omitted. Generator: schema-valid, 5/6 requirements covered, 4/11 tasks with valid requirement references, 11/11 RACI valid; bundle rejected. User explicitly approved three concrete error findings. Raw results remain ignored/private, key never logged. README/report/checklist now link actual metrics and limitations. Next: improve analyzer fact retention/category handling and generator requirement references, then repeat this dev baseline; do not weaken validators or tune on reserved test.

Demo removal completed (D-017): deleted ba_assistant/demo.py, moved scripted responses into tests only, removed demo UI/export controls, required connection before chat, retained live-session refresh and key replacement. Reset and retained old demo sessions show the connection screen. UI regression tests now use OpenRouter with mocked HTTP. Actual checks: 141 passed in 11.89s; Ruff, environment/link checks and git diff --check PASS. No model/prompt change or live API call. README, architecture and video guidance updated; earlier run records intentionally retain historical demo evidence.

Pre-evaluation cleanup completed: simplified this status file and current architecture, removed contradictory outdated README guidance, extracted error-text formatting from app.py into ui_errors.py. Model/prompt/schema and application behavior unchanged. Baseline prompts, tests and run records are deliberate evaluation evidence, not redundant files. Actual checks: 139 tests passed in 12.35s, Ruff PASS, environment/link checker PASS, git diff --check PASS. Reviewed the new module and documentation using review-deliverable; no new live calls or quality claims.

Additional work: broader semantic evaluation; record video using the prepared script and the actual baseline, including failures.

## Limits and unresolved quality issues

- A limited component baseline now exists; no held-out/full-dataset semantic precision/recall, complete independent human document rubric or comparative model score. Evaluation checklist is satisfied at documented prototype-baseline scope, not as evidence of reliable NLP quality.
- One generated document repeats some scope statements, omits explicit customer acceptance as a task and has incomplete task-source traceability. Structural validity does not prove semantic completeness.
- Free models have produced 429, timeouts and malformed schema. Changes are regression-tested, not proven to eliminate live failures.
- Session persistence is memory-only. Fresh Codex skill discovery, committed-release checkout and video recording remain unverified/incomplete.

## Where to continue

- [Requirements and submission checklist](REQUIREMENTS.md)
- [Current architecture and decision history](ARCHITECTURE.md)
- [Short report](REPORT.md); the video script is kept locally, outside the repository
- [Evaluation plan and data provenance](../evals/PLAN.md)
- [Dataset review packet](../evals/data/README.md)
- [Submission evaluation and reproducibility record](../evals/runs/submission-review-2026-11-15.md)

## Historical evidence

Read only the record relevant to a change: [core](../evals/runs/core-baseline-2026-11-15.md), [adapter](../evals/runs/adapter-baseline-2026-11-15.md), [workflow](../evals/runs/workflow-baseline-2026-11-15.md), [UI/export](../evals/runs/ui-exports-2026-11-15.md), [free mode](../evals/runs/free-mode-2026-11-15.md), [schema repair](../evals/runs/schema-repair-2026-11-15.md), [chat clarification](../evals/runs/chat-clarification-2026-11-15.md), [generator format](../evals/runs/generator-format-2026-11-15.md), [free router](../evals/runs/free-router-2026-11-15.md).

Earlier scaffold-only checks and the original seven-document inventory describe historical states, not current completeness. One isolated-copy negative scaffold test was blocked by sandbox permissions; it was never counted as passing. Assignment.pdf was read in full; a fixed number of documents or skills is not an assignment requirement.
