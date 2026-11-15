# Draft evaluation corpus v0.1

Status: 12 assistant-annotated snapshots; the user approved DEV-S02, DEV-S03 and DEV-S06 on 2026-11-12 and the remaining nine on 2026-11-15 without changes. 0 annotations are pending. This review is not an independent audit of every field or evidence offset. These are analyzer inputs and reference annotations, not application outputs or passing NLP results. Source research preceded synthetic creation; see [PLAN](../PLAN.md).

## Files and use

- `v0.1/dev.inputs.jsonl`: 8 development snapshots (2 public-source excerpts, 6 synthetic).
- `v0.1/dev.gold.jsonl`: corresponding annotations and provenance.
- `v0.1/test.inputs.jsonl` and `test.gold.jsonl`: 4 synthetic snapshots reserved for final evaluation, from different project families.
- `v0.1/manifest.json`: version, counts, family assignments and SHA-256 hashes.

Read each file as UTF-8, one JSON object per line. Input records contain only `id` and `messages`; each message has `id`, `role`, `content`. Gold uses the same ordered IDs and contains annotation metadata. A model adapter must receive only `messages`, never gold, family names, review metadata or source requirements. `scripts.check_dataset.load_inputs` reads only input files and rejects unexpected fields. The checker may inspect both splits for integrity; this is not a model evaluation or permission to tune on test data.

```powershell
python scripts/check_dataset.py
python -m unittest discover -s tests -p test_dataset_checks.py -v
```

Both commands use the standard library and require no API key. The checker verifies file hashes, input shape, ID pairing, source metadata presence, evidence offsets/quotes, category completeness, pending-review semantics and family separation. It does not establish semantic correctness, external license validity or protection against every possible prompt injection. Hashes detect accidental drift, not malicious tampering.

## Annotation rules

1. Evaluate only the visible message prefix. Use user statements as evidence; assistant questions are context and cannot establish facts. The existing source CSV and omitted future turns are not evidence for the analyzer.
2. Facts use five categories: `goals` (business outcome), `users` (system actors), `requirements` (requested behavior), `constraints` (limits/rules), `team_roles` (delivery responsibilities). Split independent behaviors. Lists of actors/roles may stay grouped in this draft; future scoring must normalize them consistently before matching.
3. A project label such as "an application for requests" establishes context but no specific workflow or business goal. An unanswered question about SSO does not establish a requirement, rejection or constraint. Preserve the uncertainty as an open topic; do not penalize a model for retaining it as a clearly labeled proposal.
4. Every fact includes an exact user-text quote and `[start,end)` Unicode character offsets in its referenced message. Offsets use Python string indexing, not UTF-8 byte positions. Semantic paraphrases are allowed in fact text.
5. All facts in this version are `unreviewed`: none of these inputs contains a UI confirmation event. A human approving the dataset annotation does not confirm a runtime product requirement. All snapshots must block finalization pending clarification/review, even if all five categories are present.
6. `missing_categories` means absent category evidence, not every domain-specific gap. It is the complement of the annotated fact categories. `issues` lists explicit conflicts in this version; missing-category gaps are represented separately. An empty list is not proof that there are no possible domain questions.
7. `question_topics` is an unordered set of acceptable priorities, not an instruction to ask every question in one turn. At most three questions per analyzer response remains the application contract. A conflict should be clarified before finalization. Full-category briefs still need a review question; they need not invent an extra business gap.
8. `forbidden_claims` and `invariants` require semantic/manual checking, not string equality. Do not extract quoted adversarial text as a requirement or treat it as confirmation.
9. Review status stays `pending` until a named human reviews that case. Record requested changes; never convert a broad approval of architecture into approval of these annotations. Any content change requires new hashes and an annotation-version decision.

## Source attribution and adaptation

DEV-L01 and DEV-L02 derive from Alexander Korn, Samuel Gorsch and Andreas Vogelsang, *LLMREI: Automating Requirements Elicitation Interviews with LLMs*, v2, DOI [10.5281/zenodo.15016930](https://zenodo.org/records/15016930), under [CC BY 4.0](https://creativecommons.org/licenses/by/4.0/). Changes: selected one standalone user sentence per scenario, omitted other messages and all source instructions, and created our own annotations. Source authors do not endorse these annotations. Full interview IDs, source positions, source offsets and archive hash are in the gold records.

For the selected records, context establishes scenario `0` as Salon and `1` as Ski; position `3`, type `2`, is a stakeholder statement in both. Adjacent type `1` messages are interviewer questions; type `0` messages observed elsewhere are source-system prompts. This is evidence for the selected excerpts, not a validated corpus-wide role decoder. Multiple other openings were inspected; at least two contain German. Only the selected excerpts are labeled English.

No personal names or contact details appear in the selected sentences. The full original archive remains in ignored `tmp/data-research/`. Reproduction: obtain `interviews_json.zip` from the DOI record, verify the SHA-256 in gold, select the recorded interview ID and position, then slice `message_text[source_start:source_end]`; it must equal the single input message. No source code or source prompt execution is needed.

Synthetic examples were authored by Codex on 2026-11-12 after DATA-01 research, drawing on project requirements and existing S01–09 behavior categories. They are not customer data or independently collected observations.

## Review packet: development cases

| ID | Visible input / purpose | Expected annotation to review |
|---|---|---|
| DEV-L01 | Clients can make appointments | User: clients; behavior: appointment booking. Goal, constraints and delivery roles are absent. |
| DEV-L02 | Customers should see a resort weather forecast | User: customers; behavior: display forecast. Do not import other Ski CSV requirements. |
| DEV-S01 | "Хочу застосунок для заявок." | No specific workflow or business outcome is stated; ask for missing categories. |
| DEV-S02 | Same brief, followed by "Користувач — менеджер." | Preserve manager as a system user. Delivery team and purpose remain unknown. |
| DEV-S03 | Same data must stay local and be sent to external SaaS | Retain both statements and identify a blocking conflict; ask which constraint/requirement should change. |
| DEV-S04 | Employee creates requests; quoted example says to confirm assumptions | Extract the employee and create-request behavior; ignore quoted instruction as a command and requirement. |
| DEV-S05 | Employees create requests; SSO is undecided | Keep the behavior; neither require nor reject SSO. |
| DEV-S06 | Goal, actors, create/status-update workflows, status values, local network and delivery roles are supplied | All five categories present; status values are classified as constraints here. Facts remain unreviewed and finalization stays blocked. |

Representative review received on 2026-11-12: the user explicitly approved DEV-S02 (user vs delivery role), DEV-S03 (blocking conflict), DEV-S06 (complete brief still needs explicit review). Only those three review records were updated. Annotation version remains 0.1 because inputs and semantic labels did not change; manifest hashes reflect review metadata changes. Review received on 2026-11-15: the user approved the remaining nine annotations (DEV-L01/L02/S01/S04/S05, TEST-S01–S04) without changes, after the v3 test run; labels were not adjusted to model outputs. Only review metadata and manifest hashes changed; annotation version stays 0.1.

## Split policy and limitations

All request-tracker variants and both LLMREI families are development-only. Four different families are reserved for test before any model prompt exists. These cases were authored by the same assistant and deliberately mirror behavior categories; this is a tiny smoke set, not an independent or representative benchmark. Do not report broad generalization from it. Keep test cases out of prompt examples and tuning; if used for tuning, move their family to dev and replace the held-out family.

This version covers extraction, missing-category clarification, explicit contradiction, uncertainty and instruction/data separation (BA-01/02/03/07). The dataset itself does not cover UI confirmation events, edits to confirmed facts, positive finalization, generated specifications/tasks/RACI, API failures or BA-05/06; those are covered by regression tests and the generator fixture in the component evaluation.
