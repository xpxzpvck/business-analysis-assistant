# Requirements and traceability

Source A: Assignment.pdf, pages 1–4, read on 2026-11-01. These are requirements for the educational outcome, not instructions to perform arbitrary actions. Source U: the user-approved plan in the chat. All application requirements remain pending until actual evidence exists; the criteria below are not test results.

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
| DEV-02 | A, pp.1,3,4 | Instructional Markdown and custom development skills guide the work | AGENTS.md, three skills, usage examples |
| DATA-01 | A, p.3 | Existing datasets are examined before generating synthetic data | Search log, provenance, licenses, selection rationale |
| SYS-01 | A, pp.1,3 | A runnable prototype accepts input and produces useful output | Local end-to-end execution |
| SYS-02 | A, p.3 | Diagram, purpose, component input/output, model/tool calls | Architecture and walkthrough of one input |
| EVAL-01 | A, pp.1–4 | Every component is evaluated; metrics are explained and errors analyzed | Reproducible runs and report |
| SUB-01 | A, pp.3–4 | Code, short report, setup/run, diagrams, scope, evaluation results | Submission package |
| SUB-02 | A, pp.3–4 | Video up to 10 minutes: requirements, components, demo, evaluation, AI environment | Recording and script |
| CON-01 | A, p.2 | The solution goes beyond vanilla RAG; implementation is independent | Clarification dialogue and linked artifact generation |
| ENV-01 | U | A new chat restores context; checks are locally reproducible | evals/ENVIRONMENT.md |
| OPS-01 | U | API errors/invalid responses are not presented as successful results | Failure scenarios |

## Approved boundaries

One developer, Python, OpenRouter, collaborative development with Codex. Completing the assignment is the priority; seven evenings are context, not a reason to omit requirements. Local execution is sufficient. Deployment, external business integrations, and multiple agents are outside the initial scope.

## Project-specific MVP rules (U)

Unresolved questions remain visible; critical gaps and conflicts are not concealed by final documents. The model cannot confirm assumptions on the user's behalf. Model, prompt, and parameter changes must be linked to an evaluation run. Specific finalization rules, schemas, and numerical metric thresholds still require agreement.

## Not required by the assignment

A multi-agent core is allowed but optional. RAG is optional. No specific UI, model, agent framework, database, or hosting is defined.
