# Architecture - not yet approved

Status: the application is not implemented. Python and OpenRouter are confirmed; the remaining items below are questions for the next stage, not an approved design.

## Required capabilities

Context collection → gap/conflict detection → clarification → specification, tasks, acceptance criteria, and RACI generation → structural invariant validation.

This is a sequence of capabilities, not a fixed number of components or LLM calls. Development skills are not runtime components.

## Decisions for the next stage

- UI and local launch method.
- Component boundaries, dialogue state management, and session persistence.
- Input/output contracts, stable requirement IDs, provenance, and export format.
- OpenRouter model, structured output, timeouts, and retry limits.
- Finalization criteria when unresolved questions remain.
- Python dependency manager and lint/test/eval/run commands.

## Component template

For each approved component, record: purpose; related requirement IDs; input; output; LLM/tool calls or their absence; errors; metrics; and how to test it independently. Before implementation, add a Mermaid diagram with actual calls and a walkthrough of one complete example.

## Interfaces

Public APIs and types are not being created at this stage. The configuration keys in `.env.example` are reserved for the next stage; the runtime does not read them yet.

## Decision log

| ID / date | Status | Decision | Rationale and consequences |
|---|---|---|---|
| D-001 / 2026-11-01 | Confirmed: user | Python, one developer, OpenRouter | Use the user's experience; the model will be selected separately |
| D-002 / 2026-11-01 | Confirmed: user | Collaborative development in small steps | The user controls important decisions and can explain the system |
| D-003 / 2026-11-01 | Confirmed: user | Environment and MVP boundaries first | Current work does not approve architecture or UI |
| D-004 / 2026-11-01 | Confirmed: user | Short AGENTS.md, three repo-local skills | Persistent rules are separate from procedures and runtime prompts |
| D-005 / 2026-11-01 | Implementation default | Environment checker uses only the Python standard library | Initial verification without API, dependency installation, or network; Python 3.11+ is the minimum for this scaffold only |
| D-006 / 2026-11-12 | Superseded by D-007 | Consolidate to seven core documents and three repo-local skills; retain three compatibility pointers | Preserve assignment coverage while reducing duplication; decisions now live here; skill files are read-only in this session, so their old document paths remain as pointers |
| D-007 / 2026-11-12 | Confirmed: user | Remove the three compatibility pointers after user updated skill references | Completes D-006 consolidation: seven core documents and three skills; no duplicate routing files |

New entry: ID, date, confirmed/proposed/superseded, who/what confirmed it, decision, rationale, consequences. An agent proposal does not automatically become confirmed. When superseding a decision, preserve a reference to the previous one.
