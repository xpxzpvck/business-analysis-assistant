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
