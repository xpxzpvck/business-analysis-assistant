# Working with Codex

## Task card

Before starting, specify: goal; requirement IDs; input context; boundaries; expected artifact; acceptance criteria; checks. A card in the chat is sufficient for ordinary approved tasks; keep long-term plans and material decisions in the repository.

Cycle: task definition → investigation → agreement on new important decisions → implementation → diff and behavior verification → status update. Do not require repeated approval of already authorized work.

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

## Handoff template

Date / task / requirement IDs / changes / executed commands and results / unexecuted checks / decisions / open questions / next complete step.

Use a separate chat for a separate task or a substantial context change. Start with AGENTS.md and STATUS.md, then read relevant documents. Leave an updated state on disk at the end.

## Evidence of AI environment impact

Record actual examples: task → applied rule/skill → behavior change or artifact → verification → conclusion. Do not invent before/after comparisons. Keep only sanitized examples without keys or private data.
