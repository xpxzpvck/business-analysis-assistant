# Architecture — current implementation

P-001 was approved on 2026-11-12. Current runtime follows D-015 (clarifications in dialogue) and D-016 (free router). The decision log below preserves earlier choices; superseded rows are not runtime instructions. Paid proposal P-002 was never authorized.

## Components and boundaries

| Module | Responsibility |
|---|---|
| app.py | Streamlit tabs, explicit actions, key entry and session memory |
| ui_errors.py | Ukrainian error text; no UI state or network calls |
| models.py | Strict Pydantic contracts for facts, issues, analysis and artifacts |
| session.py | Atomic state changes, evidence validation, revisions and human review |
| workflow.py | Prompt assembly, analyzer/generator calls, metadata and error boundaries |
| openrouter.py | HTTP transport, strict response schema, deadlines and bounded retry policy |
| runtime.py | Refresh retained objects across Streamlit reruns, including old Ling sessions |
| validation.py | Generation gate, reference integrity, task coverage and RACI invariants |
| exports.py | Markdown/JSON documents without transcript, credentials or review history |
| tests/scripted_provider.py | Test-only scripted replies, supplied through mocked HTTP; never imported by application code |

```mermaid
flowchart LR
    UI[Dialogue] --> W[Workflow]
    W --> A[Analyzer via OpenRouter]
    A --> S[Validated Session]
    S --> H[Human fact review]
    H --> G[Finalization gate]
    G --> L[Generator via OpenRouter]
    L --> V[Artifact validation]
    V --> E[Markdown / JSON]
```

Application startup requires an OpenRouter key before exposing dialogue/review/documents. Connecting makes no inference request. Demo mode was removed at the user's request (D-017); reset returns to the connection screen. Retained legacy demo objects are discarded on rerun; existing live workflows are preserved. The legacy JSON demonstration field remains false for export-format compatibility.

## State and contracts

- Facts have stable IDs, category, revision, exact user-message evidence and a separate review status. Categories: goals, users, requirements, constraints, team_roles. Model output cannot confirm facts.
- Analysis proposes new/revised facts, issues, up to three questions and evidence-backed resolutions of existing issues. Citations must match user text. Invalid updates reject the entire analysis. Grounding checks are structural, not semantic proof.
- A revision resets fact confirmation, invalidates documents and reopens resolved dependent issues. Already-open issues retain their opening timestamp. A resolution must cite an eligible user message from the issue opening/reopening turn or later.
- Clarifications and answers belong in Dialogue. Review contains the fact summary, sources, confirmation/rejection and restoration of rejected facts to unreviewed. Reanalysis uses existing messages without duplicating the last answer.
- Finalization requires completed analysis, a clarification/review answer, confirmed facts in all five categories, no unreviewed facts and no unresolved blocking issues. Generation is an explicit user action against a captured state version.
- ArtifactBundle contains source_version, specification sections with fact IDs, tasks with requirement IDs and acceptance criteria, RACI, proposal IDs, open issue IDs and the recommendation notice. Every requirement needs task coverage; every task needs RACI coverage. Each activity has exactly one A and at least one R, using known confirmed team roles.
- Session exposes legacy programmatic review/issue-resolution helpers for regression fixtures; the current UI does not use manual issue closure. Session.export_json is a full internal snapshot; exports.export_json is the user-facing document export.

## Prompts and model

Runtime prompts are separate from development skills. Active: analyzer_v3, generator_v3, schema_repair_v1 (D-018). Retain v1/v2 analyzer/generator as evaluation baselines; they are not loaded by the application. Generator input contains confirmed facts plus proposals/open questions, not the raw transcript or gold annotations. Generator v2 supplies a fictional format example, never project evidence.

The approved route is openrouter/free with zero prompt/completion/request price filters, require_parameters=true and allow_fallbacks=false. The router can select different underlying free models per request; exact model identity and NLP quality are not established by local tests. No tools/plugins, paid fallback, retrieval layer or agent framework. Generic ProviderConfig exists for adapter tests/programmatic use; the UI accepts only FreeProviderConfig.

Python 3.11+, Streamlit, Pydantic and HTTPX; pytest and Ruff for development. Dependencies are pinned in uv.lock. No python-dotenv dependency or implicit .env loading. UI credentials stay in session memory; replacing a key retains the dialogue and makes no request. Initial connection starts a new dialogue. No database or persistent session restore.

## Failure handling and limits

- Input: 8,000 characters per message and 60,000 for accumulated dialogue; reject over-limit input without silently dropping evidence.
- Output: max_tokens=4096. Deadlines: 60 seconds for analysis, 180 for generation. Free UI default: one attempt per action. Adapter configuration permits at most two transient retries/attempts total; Retry-After above five seconds stops retries.
- JSON Schema and local Pydantic validation stay strict. Refusal, empty output, truncation, malformed JSON and schema failures are distinct from HTTP/network/timeout errors. Sanitized diagnostics expose only known field paths and allowlisted codes, never raw bodies or keys.
- Schema failure may cache one bounded failed body in memory (up to 64,000 characters), bound to the messages/schema fingerprint. A later explicit retry can add repair instructions. Cache is not exported/logged; input change, key replacement or reset prevents reuse. No hidden extra inference call.
- A failed analysis remains pending for retry. Failed generation retains reviewed facts and any prior valid artifacts. State-version checks reject stale responses. Runtime refresh preserves session state and approved settings during reruns; server restart may lose them.
- Call records contain prompt hashes, outcomes, attempts and available final-success usage/time. They do not establish full billing, failed-attempt cost or selected router model identity.

## Exports and privacy

Specification is normative only from confirmed facts. Tasks/RACI are labeled recommendations. Exports preserve proposals and nonblocking questions separately. Markdown escapes untrusted HTML/Markdown while preserving plain-text apostrophes; RACI uses one role legend and ID references. Re-exporting existing artifacts makes no model call.

Conversation content is transmitted to OpenRouter and the selected provider. Local UI does not imply offline inference. Secrets, raw private traces and source datasets stay outside versioned artifacts. Downloaded business documents are not anonymized merely because transcript/evidence are excluded.

## Verification and walkthrough

Executable commands are maintained in [README](../README.md). Actual run evidence is in [submission checks](../evals/runs/submission-review-2026-11-15.md) and the [component baseline](../evals/runs/components-2026-11-15.md); data and semantic evaluation rules are in [PLAN](../evals/PLAN.md). scripts/evaluate_export checks exported structure only. scripts/evaluate_components runs three reviewed dev snapshots and an optional generator fixture, one free-only call each, records private outputs/selected model/timing and scores category presence after inference. It explicitly reads a local ignored .env for evaluation only. Neither evaluator reconstructs confirmation provenance or provides semantic fact F1. No runtime prompt/model change was made during the baseline.

The user-supplied example follows: request-tracker brief → questions about fields/access/team → user clarification → human fact review → generation at state 19 → seven specification sections, nine tasks and nine RACI activities covering six requirements. See [REPORT](REPORT.md) for the example, results and limitations. The application itself is not the Django request tracker described in that example.

## Decision log

P-002 proposed a paid GPT-4.1 Mini trial (USD 1 / 20 attempts), but was never approved and was superseded by the user's free-only choice. Historical proposal prices are not current recommendations or authorization. Details of previous checks remain in evals/runs; do not infer completed semantic evaluation from them.

### Recorded decisions

| ID / date | Status | Decision | Rationale and consequences |
|---|---|---|---|
| D-001 / 2026-11-01 | Confirmed: user | Python, one developer, OpenRouter | Use the user's experience; the model will be selected separately |
| D-002 / 2026-11-01 | Confirmed: user | Collaborative development in small steps | The user controls important decisions and can explain the system |
| D-003 / 2026-11-01 | Confirmed: user | Environment and MVP boundaries first | Current work does not approve architecture or UI |
| D-004 / 2026-11-01 | Confirmed: user | Short AGENTS.md, three repo-local skills | Persistent rules are separate from procedures and runtime prompts |
| D-005 / 2026-11-01 | Implementation default | Environment checker uses only the Python standard library | Initial verification without API, dependency installation, or network; Python 3.11+ is the minimum for this scaffold only |
| D-006 / 2026-11-12 | Superseded by D-007 | Consolidate to seven core documents and three repo-local skills; retain three compatibility pointers | Preserve assignment coverage while reducing duplication; decisions now live here; skill files are read-only in this session, so their old document paths remain as pointers |
| D-007 / 2026-11-12 | Confirmed: user | Remove the three compatibility pointers after user updated skill references | Completes D-006 consolidation: seven core documents and three skills; no duplicate routing files |
| D-008 / 2026-11-12 | Confirmed: user (explicit agreement to P-001) | P-001: local chat, two LLM functions, explicit fact review, deterministic finalization/validation and Markdown/JSON export | Approves MVP design and routine implementation; exact model and live-call budget remain open |
| D-009 / 2026-11-12 | Implementation default within P-001 | Draft corpus v0.1 separates runtime messages from gold; inspected source families remain dev-only; checker uses standard library | Prevents accidental gold inclusion and checks split/evidence integrity before NLP runs; human review remains required and no quality score is implied |
| D-010 / 2026-11-15 (recorded) | Confirmed: user | Use uv instead of the original venv/pip commands | User explicitly requested uv during setup; pyproject.toml and uv.lock now define reproducible dependencies |
| D-011 / 2026-11-15 | Implementation default within P-001 | Offline UI initially exposes only a labeled fixed demo; document exports omit conversation/history and preserve referenced fact text | Enables review/export checks without paid calls; does not substitute for live NLP evaluation. Full session export stays separate. |
| D-012 / 2026-11-15 | Superseded by D-013; never approved | P-002: GPT-4.1 Mini via OpenAI on OpenRouter; up to USD 1 and 20 generation attempts for the first development trial | Concrete model/budget selection; provider pinning, budget checks and evaluation runner must precede paid calls |

| D-013 / 2026-11-15 | Superseded by D-016 | Use inclusionai/ling-3.2-flash:free through OpenRouter; no paid fallback | UI uses a fixed free configuration and zero price filters, reasoning disabled, one attempt per action. Paid P-002 is not authorized. Actual availability and quality need a real-key smoke test. |

| D-014 / 2026-11-15 | Manual closure superseded by D-015 | Separate dialogue, review and documents; shared answer review and explicit batch issue confirmation | Removes repeated answers and mixed controls while preserving source ordering, pending-analysis blocks and human authority. No NLP/model change. |

| D-015 / 2026-11-15 | Confirmed: user explicitly demanded change | Clarify and reconcile issues through dialogue; keep only requirement review in Review tab | Supersedes manual issue closure in P-001/D-014. Analyzer proposes evidence-backed resolutions; controller validates provenance, user confirms resulting facts. New prompt requires live evaluation. |

| D-016 / 2026-11-15 | Confirmed: user requested replacement without extra functionality | Replace fixed Ling with openrouter/free; supersedes D-013 model choice | OpenRouter chooses a free model compatible with requested structured output. Keep zero price filters, strict schema/domain checks, one attempt per action and existing UI. Migrate open Ling sessions on rerun without losing state or making a request. Actual selected model can vary between calls; quality and availability are not guaranteed. |

| D-017 / 2026-11-15 | Confirmed: user | Remove non-LLM demo mode; supersedes D-011 demo behavior | Application requires OpenRouter connection. Scripted replies exist only as test fixtures; UI tests exercise OpenRouter via mocked HTTP. Existing real sessions survive rerun. |

| D-018 / 2026-11-15 | Confirmed: user asked to finish and document the v3 iteration | Activate analyzer_v3/generator_v3 (v2 + mandatory self-check block); keep `reasoning: {enabled: false}` in the free route | Addresses user-approved v2 findings (false goal, dropped conflict facts, wrong requirement_ids). Measured on frozen sources ([run record](../evals/runs/components-v3-2026-11-15.md)). An unfrozen post-freeze removal of the reasoning flag was reverted: without it a reasoning model spent 3901/4096 tokens and returned empty content. Cause of fast HTTP 400 remains unknown. v2 prompts retained as baseline. |

New entry: ID, date, confirmed/proposed/superseded, who/what confirmed it, decision, rationale, consequences. An agent proposal does not automatically become confirmed. When superseding a decision, preserve a reference to the previous one.
