# Business Analysis Assistant

An educational Python NLP project. The development environment is prepared; the application has not been implemented yet. The future application's LLM provider is OpenRouter.

## Getting started

1. Install Git and Python 3.11+.
2. Open the repository root in Codex and read the [current status](docs/STATUS.md).
3. Run `python scripts/check_environment.py`. This check requires no dependencies or API key.
4. For the future application, copy `.env.example` to a local `.env`; loading this file in code has not been implemented yet.

## Navigation

- [Requirements and completion evidence](docs/REQUIREMENTS.md)
- [Workflow and CRISP-DM](docs/WORKFLOW.md)
- [Architecture: open decisions](docs/ARCHITECTURE.md)
- [Decision log](docs/DECISIONS.md)
- [System evaluation](evals/PLAN.md)
- [Skill verification](evals/ENVIRONMENT.md)
- [Submission preparation](docs/SUBMISSION.md)

`AGENTS.md` contains persistent instructions; `.agents/skills/` contains development procedures. Other Markdown files are project conventions and are read through links. Application prompts will be separate artifacts.

## New chat

> Read AGENTS.md and docs/STATUS.md. Identify the relevant requirements and open decisions for the next task. Propose the smallest complete step and acceptance criteria. Do not treat proposed architecture as approved.

## Sources

- Local Assignment.pdf is the primary source of assignment requirements.
- [Codex AGENTS.md](https://learn.chatgpt.com/docs/agent-configuration/agents-md)
- [Codex skills](https://learn.chatgpt.com/docs/build-skills)

The application is intended to run locally. The repository is hosted on [GitHub](https://github.com/xpxzpvck/business-analysis-assistant); application publication, deployment, and paid calls are not configured.
