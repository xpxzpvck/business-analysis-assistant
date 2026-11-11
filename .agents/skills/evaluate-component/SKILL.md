---
name: evaluate-component
description: Define and run evaluations when adding or changing NLP components, prompts, or models. Compare baseline and errors; exclude documentation-only changes.
---

# Evaluate component

Read evals/PLAN.md, relevant cases in evals/SCENARIOS.md, component contracts in docs/ARCHITECTURE.md and relevant IDs in docs/REQUIREMENTS.md. Use the run record template in evals/PLAN.md.

Identify the behavior, evaluation data and executable harness. If a component, gold data, configuration or command is missing, describe the evaluation design and mark it as not run. Never invent scores or call an unconfigured API.

For executable evaluation:
- Record code, dataset, prompt, model and parameters.
- Select affected component and end-to-end cases; preserve held-out test data.
- Run structural checks and semantic assessment separately.
- Compare baseline and candidate on identical cases; label the first run as baseline if none exists.
- Report denominators, failures, representative errors and latency/usage where available.
- Use human assessment as primary; calibrate any supplementary LLM judge against human ratings.

Output the run record or evaluation design, actual evidence, unexecuted checks, limitations and next experiment. Update docs/STATUS.md with actual results. Keep keys and private traces outside tracked artifacts.