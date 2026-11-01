# Application evaluation

Status: evaluation design; no model runs yet. The groups below are capabilities to map to actual components after architecture approval.

| Capability | Evaluation |
|---|---|
| Context collection/extraction | Precision/recall/F1 of facts by category; required-field completeness |
| Gap/conflict detection | Precision/recall on annotated issues; unnecessary clarifications |
| Clarification | Relevance rubric, number of resolved questions, correct ordering before finalization |
| Specification | Confirmed requirement coverage, unsupported claims, provenance correctness |
| Tasks and acceptance criteria | Requirement-link validity; coverage; rubric for specificity and testability of criteria |
| RACI | Fraction of activities with exactly one A; references to known roles; manual suitability assessment |
| Orchestration and API | State/failure scenario pass rate; latency, usage/cost where available |
| End-to-end | Completion of all artifacts and invariants across a full dialogue |

## Data and gold references

Complete DATA-01 before synthetic generation. The search log must contain query, date, URL, license, suitability, and acceptance/rejection rationale. For scenarios, store ID, provenance, split, input/turns, gold facts/issues, expected invariants, and requirement IDs. Current scenarios in SCENARIOS.md are manual test examples, not a collected dataset or evidence of DATA-01 completion.

Separate development and held-out test before tuning. Version annotations. Agree numerical thresholds after component definition and development baseline review, before the final test run; do not fit them to test results. Structural invariants BA-05/06 require 100% validity of issued final artifacts.

## Semantic quality rubric

0 - missing/incorrect result; 1 - substantial errors; 2 - mostly correct but needs correction; 3 - correct and usable. Assess completeness, groundedness, clarity, and practical usability separately; add a concrete example and rationale. Human assessment is primary; an LLM judge may supplement it after calibration against human ratings.

## Experiment record

Use RUN_TEMPLATE.md. Record commit and dirty status, dataset/split version, component, model ID, prompt version/hash, parameters, command, date, raw counts, and metric denominators. Compare baseline/candidate on identical scenarios; explain changes. Do not turn API failures into omitted successful examples. For stochastic responses, report repeat count and variability; do not promise bitwise API reproducibility.

Repeat relevant evaluations after model/prompt/component changes. Analyze false positives, false negatives, and unsupported claims. Sanitize public results; keep private traces in ignored evals/runs/private/.
