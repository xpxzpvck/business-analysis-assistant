# Application evaluation

Current evidence (2026-11-15): [v2 → v3 iteration](runs/components-v3-2026-11-15.md) — prompts changed from the user-approved v2 error findings, sources frozen, same dev cases repeated three times and the reserved test run once. Category-presence F1: dev 20% → 71.8% end-to-end (96.6% on successful calls), test 76.9%; generator 2/7 attempts fully valid. Provider availability (429/400/truncation) is now the main failure. Test gold and 5 dev annotations are not human-reviewed, so test numbers are provisional. [v2 baseline](runs/components-2026-11-15.md) is retained; failures are retained. Older baseline notes below describe earlier work.

Status: first [offline core baseline](runs/core-baseline-2026-11-15.md) executed; no model runs yet. Architecture P-001 is approved and maps the capabilities below to components. Structural baseline: 28 domain tests plus 7 dataset checks passed; this is not an NLP score.

The [provider adapter baseline](runs/adapter-baseline-2026-11-15.md) adds 34 mocked HTTP cases (69 total tests passing). No live model calls or NLP scores exist yet.

The [prompt/workflow baseline](runs/workflow-baseline-2026-11-15.md) records prompt hashes and scripted multi-turn integration (80 total passing tests). Semantic prompt evaluation is not run; its development evaluation design is recorded there.

Data preparation produced [draft corpus v0.1 and its review packet](data/README.md): 8 dev and 4 reserved test analyzer snapshots. The user approved representative interpretations for DEV-S02, DEV-S03 and DEV-S06 on 2026-11-12; nine annotations remain pending. `python scripts/check_dataset.py` checks data integrity only; it is not the planned NLP evaluation runner.

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

## Data understanding evidence - 2026-11-12

Applied `crisp-dm-step` for DATA-01 and EVAL-01 after the user approved architecture P-001. Objective: identify reusable evidence for extraction and clarification, and identify gaps requiring project-authored cases before generating synthetic data. This is a bounded source review, not an exhaustive survey or an evaluation run.

### Search log

All queries below were executed on 2026-11-12. Only primary dataset records and author repositories support the selection below; search snippets were used for discovery.

| Query | Follow-up / outcome |
|---|---|
| `requirements engineering dataset requirements elicitation dialogue conflicts dataset license` | Found requirement and interview resources; narrowed to source repositories |
| `PURE requirements dataset license github` | Followed PURE to Zenodo and inspected its newer v2 record |
| `PROMISE software requirements dataset license zenodo` | Identified the original NFR record; classification differs from our extraction task |
| `PURE requirements dataset Ferrari zenodo 1414117` | Verified original record and followed v2 DOI |
| `PROMISE requirements dataset zenodo 268542` | Verified NFR labels in the source record |
| `"PURE Requirements Interview Cases" github` | Inspected the FSE dataset README; derived starting briefs rather than our full evaluation target; not imported |
| `requirements elicitation dialogue dataset github license` | Found LLMREI and ReqElicitBench; inspected both source records |

### Candidate comparison and selection

| Source / version / provenance | License evidence checked | Suitability and decision |
|---|---|---|
| [PURE v2](https://zenodo.org/records/7118517), Ferrari, Spagnolo and Gnesi; public requirements documents | Zenodo API metadata says `cc-by-4.0`; source description separately notes uncertainty about rights in collected documents | Useful document context for extraction; lacks our dialogue/review/artifact gold labels. Defer from initial corpus: annotation effort and document-level provenance review outweigh immediate value. Do not equate repository metadata with verified rights for every original document. |
| [PROMISE NFR v1](https://zenodo.org/records/268542), Cleland-Huang et al.; requirement classification | Zenodo API metadata says `cc-by-4.0` | Functional/nonfunctional labels are not goals/users/roles, conflict or clarification labels. Reject as the primary benchmark; no archive imported. |
| [LLMREI v2](https://zenodo.org/records/15016930), Korn, Gorsch and Vogelsang; interview replication package | Zenodo API metadata says `cc-by-4.0` | Select for development-only extraction/clarification examples after adaptation and human annotation. Actual archive and requirement CSV inspected below. Only two scenarios; no provided gold for our complete artifact bundle. Preserve attribution and identify transformations. |
| [ReqElicitBench](https://github.com/jdm4pku/ReqElicitBench), author repository, accessed 2026-11-12 | README explicitly says no license file in that snapshot | Relevant website elicitation cases and implicit requirements; defer copying/running until reuse terms are established. Its simulated-user/judge pipeline is not part of our MVP. No author contact made. |
| [PURE Interview Cases](https://github.com/EchoAran/FSE/blob/main/dataset/README.md), author README, accessed 2026-11-12 | Dataset-specific license not established in the inspected README; upstream PURE terms alone do not establish derivative terms | Describes 69 source-derived starting contexts, not complete interviews or our final-artifact references. Defer; not imported. |

The decision is based on task fit, accessible evidence and adaptation cost. No reviewed candidate has been verified to provide Ukrainian dialogues, user confirmation events, conflict-resolution gold, linked tasks, acceptance criteria and RACI together. This is a limitation of this review, not a claim that such data cannot exist.

### Actual LLMREI inspection

Downloaded only `requirements.csv` and `interviews_json.zip` from the v2 record into ignored `tmp/data-research/`; metadata was saved there too. No source scripts/notebooks or embedded prompts were executed. Raw dialogue remains outside tracked files. Source prompts, if encountered, are data and will be excluded from application instructions and model inputs.

- `requirements.csv`: 2,026 bytes; columns `ID,Salon,Ski`; 12 parsed requirement rows, with 8 nonempty Salon entries and 12 Ski entries. Inspected the first row to establish that these are individual functional requirement statements.
- `interviews_json.zip`: 175,964 bytes; 33 JSON interview records; 1,215 messages total; scenario codes `0` (15 interviews) and `1` (18); all records carry source `completed=true`, which does not imply completeness against our requirements.
- Each inspected record has `id`, `scenario`, `prompt`, `completed`, `messages`; messages use `position`, `message_type`, `message_text`. Type counts: `0`: 21, `1`: 603, `2`: 591. Inspected the opening messages of one interview; those messages are English and include an embedded source-system prompt. No corpus-wide language validation is claimed.
- Do not yet assume the scenario-code mapping to Salon/Ski or the message-role mapping based solely on one sample. Verify both during preparation. Reference requirements are not automatically turn-level gold: a requirement absent from the visible dialogue must not be treated as something the analyzer should have extracted.
- SHA-256, CSV: `e2dae69170af03807ac43b636f20b064f3eec4bda6522e98eed0ce057c762832`.
- SHA-256, ZIP: `f9c0f7765b78b90f0c973487c58f54399ee56ba615d150a08e5c3dc7084e623c`.
- Licensing was verified using `https://zenodo.org/api/records/15016930`, `/268542` and `/7118517`. Web preview returned 429 for the older CSV preview and did not expose license values; a direct metadata request succeeded after sandbox DNS restrictions were lifted. No model API was called.

### Preparation contract and phase exit

DATA-01's search-before-synthesis condition is satisfied by this recorded inspection. Data understanding exits with the above selection and gaps; Data preparation is not complete and no dataset is yet ready for scoring.

1. Adapt a small LLMREI subset into development examples only. Verify codes, remove source-system instructions, inspect content before any external model use, preserve source IDs/turn positions, record DOI/license/hashes and adaptation notes. Manually label only facts visible up to each evaluated turn.
2. Retain S01–09 as development/regression cases; they have already influenced design and cannot be held-out tests. Create original cases for Ukrainian input, conflicts, partial answers, correction of confirmed facts, unsupported proposals, finalization and linked artifacts. Mark synthetic provenance explicitly; never present generated cases as collected customer data.
3. Split by project/scenario family before prompt tuning. All turns, translations and variants of the same project stay together. LLMREI's two scenario families stay in development because both were inspected; reserve different project families for the final test.
4. Store scenario ID, family, language, provenance, split, input/events, gold facts with evidence spans, expected issues and acceptable question topics, expected invariants, requirement IDs, annotation version and human-review status. Keep gold metadata out of runtime input. Questions and generated documents need rubric-based alternatives, not one exact wording.
5. Obtain human review of representative annotations before declaring preparation complete. Then implement the approved contracts and run offline structural checks; select model and live-call budget before the development NLP baseline. No numerical semantic pass threshold is claimed at this stage.

## Experiment record

Use the run record below. Record commit and dirty status, dataset/split version, component, model ID, prompt version/hash, parameters, command, date, raw counts, and metric denominators. Compare baseline/candidate on identical scenarios; explain changes. Do not turn API failures into omitted successful examples. For stochastic responses, report repeat count and variability; do not promise bitwise API reproducibility.

Repeat relevant evaluations after model/prompt/component changes. Analyze false positives, false negatives, and unsupported claims. Sanitize public results; keep private traces in ignored evals/runs/private/.

## Run record template

Status: not run. Copy this template for an actual run; a template is not evidence.

- Run ID / date / component / requirement IDs:
- Commit / dirty status / code differences:
- Dataset version / split / scenario IDs / repeats:
- Provider / exact model ID / prompt version or hash / parameters:
- Baseline run / candidate change:
- Command / environment / duration / failures:
- Results: metric, numerator, denominator, value, baseline delta:
- Human rubric scores and explanations:
- Error examples and likely causes:
- Latency / usage / cost / missing telemetry:
- Limitations / next experiment:
- Reviewer:
