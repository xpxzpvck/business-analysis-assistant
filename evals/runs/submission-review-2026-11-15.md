# Submission preparation — 2026-11-15

## Export-only evaluation

- Input: user-supplied requirements.json, state 19, non-demo flag. SHA256: `1c4b7694a5a513e863fe76149eeab9bc0bc7b5e45d4e31286fd03de4d1008fc0`. Raw private export is not copied into the repository.
- Command: `uv run --frozen --no-sync python -m scripts.evaluate_export <local-export.json>`.
- Result: all ten structural checks passed. Requirements covered 6/6; tasks with valid requirement references 9/9; specification sections with valid references 7/7; RACI activities with valid references, exactly one A and at least one R 9/9; 19 confirmed facts in the export.
- These are counts for one submitted artifact, not success rates across API requests. Export lacks transcript/review evidence, provider identity, prompt hashes, timing and usage. No claim of independent confirmation verification, exact live model or latency/cost.
- Codex qualitative review: scope generally matches listed facts; redundant requirements/specification sentences, incomplete task source traceability, and missing explicit customer acceptance activity. No human rubric score assigned. Analyzer extraction and clarification metrics NOT RUN.

## Reproducibility

Working tree contains uncommitted implementation over HEAD 342c006. A fresh allowlisted source copy with a separate virtual environment was checked at tmp/submission-check-20261115-151501; this is not a clean Git checkout of a committed release. No .env or existing .venv was copied. Python selected by uv in this copy: 3.13.15. Existing working-environment evidence was collected on Python 3.14.7.

| Command (in isolated copy) | Actual result |
|---|---|
| uv sync --frozen | PASS; new virtual environment, 46 packages installed |
| uv run --frozen --no-sync pytest -q | 139 passed in 19.26s |
| uv run --frozen --no-sync ruff check . | PASS |
| uv run --frozen --no-sync python scripts/check_environment.py | PASS |
| uv run --frozen --no-sync python scripts/check_dataset.py | PASS: 8 dev / 4 test; 9 annotations pending human review |
| uv run --frozen --no-sync python scripts/check_launch.py | PASS: isolated server HTTP 200; process stopped afterward |
| git diff --check (original worktree) | PASS |

The launch probe proves server startup, not visual browser rendering. Streamlit AppTest cases exercise UI interaction without live API calls. Regression suite includes invalid references, RACI cardinality, stale versions, evidence checks, rejected-fact recovery, failed-request preservation and export escaping. The new export evaluator was checked against valid input and deliberately broken requirement/RACI references.

## Submission review

Created docs/REPORT.md and docs/VIDEO.md; updated README navigation and executable evaluation command. Used evaluate-component and review-deliverable, reviewed new scripts/tests and documentation. No new runtime model/prompt changes, no API calls, no paid usage, no publication or commit.

Remaining: independent semantic assessment of analyzer, clarifications and generated artifacts; nine annotation reviews; video recording; committed-release clean checkout. The report explicitly distinguishes missing evidence from passing structural checks. A single exported document is insufficient to close EVAL-01.
