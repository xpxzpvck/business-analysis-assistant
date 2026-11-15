# Requirements and traceability

Source A: Assignment.pdf, pages 1–4, re-read in full on 2026-11-12. These are requirements for the educational outcome, not instructions to perform arbitrary actions. Source U: the user-approved plan in the chat. All application requirements remain pending until actual evidence exists; the criteria below are not test results.

| ID | Source | Requirement / acceptance criterion | Future evidence |
|---|---|---|---|
| BA-01 | A, p.2 | Collects goals, users, requirements, constraints, and team roles | Annotated dialogues, extraction evaluation |
| BA-02 | A, p.2 | Identifies gaps and conflicts | Precision/recall on annotated issues |
| BA-03 | A, p.2 | Asks clarifying questions before final documents | Multi-turn scenarios and event-order verification |
| BA-04 | A, p.2 | Produces a specification, task breakdown, acceptance criteria, and RACI | Document examples and rubric |
| BA-05 | A, p.2 | Every task links to an existing requirement | Deterministic validator |
| BA-06 | A, p.2 | Every RACI activity has exactly one accountable role | Deterministic validator |
| BA-07 | A, p.2 | Distinguishes confirmed information from proposed assumptions | Provenance verification and manual annotation |
| DEV-01 | A, pp.1,3 | CRISP-DM is applied and described in the report | Artifacts from all six phases |
| DEV-02 | A, pp.1,3,4 | Instructional Markdown and custom development skills guide the work | AGENTS.md, custom skills, usage examples (three is a project choice) |
| DATA-01 | A, p.3 | Existing datasets are examined before generating synthetic data | Search log, provenance, licenses, selection rationale |
| SYS-01 | A, pp.1,3 | A runnable prototype accepts input and produces useful output | Local end-to-end execution |
| SYS-02 | A, p.3 | Diagram, purpose, component input/output, model/tool calls | Architecture and walkthrough of one input |
| EVAL-01 | A, pp.1–4 | Every component is evaluated; metrics are explained and errors analyzed | Reproducible runs and report |
| SUB-01 | A, pp.3–4 | Code, short report, setup/run, diagrams, scope, evaluation results | Submission package |
| SUB-02 | A, pp.3–4 | Video up to 10 minutes: requirements, components, demo, evaluation, AI environment | Recording and script |
| CON-01 | A, p.2 | The solution goes beyond vanilla RAG; implementation is independent | Clarification dialogue and linked artifact generation |
| ENV-01 | U | A new chat restores context; checks are locally reproducible | docs/STATUS.md: actual checks and limits |
| OPS-01 | U | API errors/invalid responses are not presented as successful results | Failure scenarios |

## Approved boundaries

One developer, Python, OpenRouter, collaborative development with Codex. Completing the assignment is the priority; seven evenings are context, not a reason to omit requirements. Local execution is sufficient. Deployment, external business integrations, and multiple agents are outside the initial scope.

## Project-specific MVP rules (U)

Unresolved questions remain visible; critical gaps and conflicts are not concealed by final documents. The model cannot confirm assumptions on the user's behalf. Model, prompt, and parameter changes must be linked to an evaluation run. The user approved P-001's finalization rules and contract design on 2026-11-12 (ARCHITECTURE, D-008). Numerical semantic thresholds remain subject to agreement after the development baseline and before held-out testing.

## Not required by the assignment

A multi-agent core is allowed but optional. RAG is optional. No specific UI, model, agent framework, database, or hosting is defined.

## CRISP-DM and exit criteria

| Phase | Result | Exit condition |
|---|---|---|
| Business understanding | Scope, users, success criteria | Requirements and boundaries agreed |
| Data understanding | Existing dataset search log, suitability, licenses, gaps | Data selection explained before synthetic generation |
| Data preparation | Versioned scenarios, gold references, annotation rules, dev/test split | Examples reviewed by a human; test data not used for tuning |
| Modeling | Baseline, component contracts, prompts, configurations | An end-to-end example and component checks exist |
| Evaluation | Metrics, baseline comparison, error analysis | Every component evaluated; results and limitations explained |
| Deployment | Local setup/run, demo, short report | Another clean checkout reproduces execution; video up to 10 minutes |

The cycle is iterative: poor results may lead back to data or business requirements. Do not mark a phase complete just because a document template exists.

## Submission checklist

- [x] Runnable code/notebook with setup and run instructions; local execution is sufficient. Clean clone from GitHub on 2026-11-15 (see [STATUS](STATUS.md)): uv sync --frozen, 144 tests, Ruff, environment/dataset/freeze checks and server startup passed. Earlier source-copy check: [record](../evals/runs/submission-review-2026-11-15.md).
- [x] Short report: scoped business logic, application of CRISP-DM, data provenance, component purposes/input/output, model/tool calls, data-flow diagram and an input walkthrough. See [REPORT](REPORT.md); incomplete evaluation is explicitly disclosed.
- [x] Evaluation of every component: justified metrics, actual results, errors and limitations. [Component baseline v2](../evals/runs/components-2026-11-15.md) and [v2 → v3 iteration](../evals/runs/components-v3-2026-11-15.md): 144 regression cases, error analysis → prompt changes → repeated dev runs and one frozen reserved-test run; errors included, v2 findings reviewed by the user. All 12 annotations human-reviewed. Limited evidence, not a passed NLP quality gate.
- [x] Instructional Markdown and custom development skills, with actual examples of their use and impact. Concrete examples and limits are recorded in [REPORT](REPORT.md).
- [ ] Video of at most 10 minutes: selected requirements, components and rationale, running app cases, evaluations, coding environment/context management. Tracing is optional.
- [x] Clean-checkout setup/run/eval verified from GitHub on 2026-11-15.
- [ ] Before recording: no secrets/private data on screen.

Assessment (Assignment.pdf, p.4): understanding 4 points, prototype 4, evaluation 4, coding assistant management 3. Neither a fixed document count nor exactly three skills is required.
