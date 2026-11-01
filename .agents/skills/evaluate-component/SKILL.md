---
name: evaluate-component
description: Define and run evaluations when changing NLP components, prompts, or models. Compare baseline and errors; exclude documentation-only changes.
---

# Evaluate component

Read evals/PLAN.md, relevant SCENARIOS.md cases, component contracts in docs/ARCHITECTURE.md, and requirement IDs. Use evals/RUN_TEMPLATE.md.

Identify behavior, data and executable harness. If component, gold data, configuration or command is missing, produce an evaluation design marked not run; never invent scores or call an unconfigured API.

For executable evaluation, record code/dataset/prompt/model/parameters, select affected component and end-to-end cases, preserve held-out test data, run structural checks and semantic rubric separately, and compare baseline on identical cases. If no baseline exists, label the first run baseline. Report denominators, failures, latency/usage where available, representative errors and next experiment. Human review is primary; calibrate optional LLM judging.

Output run record or design, evidence, unexecuted checks and limitations. Update STATUS with actual results. Keep keys and private traces outside tracked artifacts.
