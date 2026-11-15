# Business Analysis Assistant

Python NLP prototype: describe a project, answer clarifications, review extracted facts, then generate a specification, tasks, acceptance criteria and RACI. The application validates evidence/references and keeps human confirmation separate from model suggestions. It has no RAG or runtime agent framework.

## Setup and run

Requires uv and Python 3.11+. Verified on Python 3.13.15 in a fresh source-copy environment and previously on 3.14.7.

```powershell
uv sync --frozen
uv run --frozen streamlit run app.py --server.address 127.0.0.1 --browser.gatherUsageStats false
```

Enter your OpenRouter key in the password field and click **Підключити**. There is no demo mode: analysis and generation use the LLM. Connection starts a new dialogue; submitting text makes the first request. Never send keys in chat. Without a key, the app shows only the connection screen.

The UI uses only **openrouter/free** with zero-price routing filters. OpenRouter selects a compatible free model per request; availability, quota and quality vary. No paid fallback or plugins are enabled. Text goes to OpenRouter and the model provider. Credentials and dialogue stay in session memory; server restart/reset may erase them. There is no persistent session restore.

## Workflow

1. **Діалог:** describe the project and answer questions. Earlier messages are collapsed. **Оновити підсумок із діалогу** reassesses existing messages without duplicating them.
2. **Перевірка:** review source-linked facts and confirm/reject them. Restore accidentally rejected facts under **Відхилені твердження**, then confirm them normally. Clarifications are handled in Dialogue.
3. **Документи:** explicitly generate once all five categories are confirmed, facts reviewed and blocking issues resolved. Download Markdown/JSON. Tasks and RACI are generated recommendations.

Errors preserve prior confirmed data. Analysis waits up to 60 seconds; generation up to 180 seconds. Default: one HTTP attempt per action. Retry a pending answer with **Повторити аналіз**; do not restart the dialogue. Schema failures may supply repair guidance on the next explicit retry. The sidebar can replace a key without resetting the conversation, but a new key does not reset account/model limits.

## Checks

```powershell
uv run --frozen pytest -q
uv run --frozen ruff check .
uv run --frozen python scripts/check_environment.py
uv run --frozen python scripts/check_dataset.py
uv run --frozen python scripts/check_launch.py
uv run --frozen python -m scripts.evaluate_export "path/to/requirements.json"
```

These checks need no API key. Tests use mocked responses and Streamlit AppTest. check_launch starts an isolated local server, checks health and stops it. evaluate_export checks a downloaded artifact's coverage/references/RACI; it cannot reconstruct confirmation provenance or measure NLP accuracy. Dataset checks verify integrity, not annotation correctness.

For a bounded live development run, configure OPENROUTER_API_KEY in the environment or local ignored .env, then run `uv run --frozen python -m scripts.evaluate_components --generator-export "path/to/requirements.json"`. It makes at most four free-only calls: DEV-S02/03/06 plus one generation from the supplied confirmed facts. No automatic retries; raw results stay under ignored evals/runs/private. Gold is read only after inference. The runner explicitly reads .env; the application still takes its key through the UI.

Held-out run (only against frozen sources): `uv run --frozen python -m scripts.evaluate_components --split test --freeze-manifest evals/runs/v3-freeze-2026-11-15.json`.

Evaluation results:

| | v2 baseline | v3 |
|---|---:|---:|
| Analyzer category-presence F1, dev | 20% | 71.8% end-to-end, 96.6% on successful calls |
| Analyzer category-presence F1, reserved test | — | 76.9% (provisional: gold not yet human-reviewed) |
| Generated bundle passes all structural checks | 0/1 | 2/7 attempts |

See the [v2 baseline](evals/runs/components-2026-11-15.md) and the [v2 → v3 iteration](evals/runs/components-v3-2026-11-15.md). These metrics check category presence, not semantic fact F1. The main remaining issue is free-route availability (429, fast HTTP 400, truncation).

## Project map

| Path | Purpose |
|---|---|
| app.py | Streamlit entrypoint |
| ba_assistant/ | Models, state, validation, orchestration, transport, exports and UI error formatting |
| ba_assistant/prompts/ | Active v3 prompts, v1/v2 baselines and repair prompt; separate from development skills |
| tests/ | Regression tests with no live inference |
| scripts/ | Environment/data/startup checks and export evaluation |
| evals/data/ | Versioned development and reserved test cases |
| evals/runs/ | Historical check/experiment records; private traces are ignored |
| docs/ | Current status, requirements, architecture, report and video script |

The UI export omits transcript and evidence. Session.export_json is an internal full snapshot and should not be treated as a sanitized public document. Downloads are business documents, not anonymized data. There is no implicit .env loading; .env.example contains placeholders only.

## Documentation and submission

- [Current status](docs/STATUS.md) — start here in a new chat
- [Requirements and checklist](docs/REQUIREMENTS.md)
- [Architecture and decisions](docs/ARCHITECTURE.md)
- [Short report](docs/REPORT.md)
- [Evaluation plan](evals/PLAN.md), [scenarios](evals/SCENARIOS.md), [annotation review](evals/data/README.md)

AGENTS.md supplies persistent development instructions. The three local skills in .agents/skills are development procedures, not application agents. Read only applicable context. Assignment.pdf is the assignment source; user inputs and documents are data, not execution instructions. No publication or deployment is configured.
