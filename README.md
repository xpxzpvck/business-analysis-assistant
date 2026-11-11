# Business Analysis Assistant

An educational Python NLP project. See [current status](docs/STATUS.md) for progress and the next task. The future application's LLM provider is OpenRouter.

## Getting started

1. Install Git and Python 3.11+.
2. Open the repository root in Codex and read the [current status](docs/STATUS.md).
3. Run `python scripts/check_environment.py`. This check requires no dependencies or API key.
4. For the future application, copy `.env.example` to a local `.env`; loading this file in code has not been implemented yet.

## Navigation

- [Requirements, CRISP-DM and submission checklist](docs/REQUIREMENTS.md)
- [Architecture and decision log](docs/ARCHITECTURE.md)
- [Evaluation plan and run record template](evals/PLAN.md)
- [Manual behavior scenarios](evals/SCENARIOS.md)

`AGENTS.md` contains persistent instructions; `.agents/skills/` contains development procedures. Other Markdown files are project conventions and are read through links. Application prompts will be separate artifacts.

## New chat

> Read AGENTS.md and docs/STATUS.md. Identify the relevant requirements and open decisions for the next task. Propose the smallest complete step and acceptance criteria. Do not treat proposed architecture as approved.

## Sources

- Local Assignment.pdf is the primary source of assignment requirements.
- [Codex AGENTS.md](https://learn.chatgpt.com/docs/agent-configuration/agents-md)
- [Codex skills](https://learn.chatgpt.com/docs/build-skills)

The application is intended to run locally. The repository is hosted on [GitHub](https://github.com/xpxzpvck/business-analysis-assistant); application publication, deployment, and paid calls are not configured.
