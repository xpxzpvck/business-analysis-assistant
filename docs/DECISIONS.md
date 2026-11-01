# Decision log

| ID / date | Status | Decision | Rationale and consequences |
|---|---|---|---|
| D-001 / 2026-11-01 | Confirmed: user | Python, one developer, OpenRouter | Use the user's experience; the model will be selected separately |
| D-002 / 2026-11-01 | Confirmed: user | Collaborative development in small steps | The user controls important decisions and can explain the system |
| D-003 / 2026-11-01 | Confirmed: user | Environment and MVP boundaries first | Current work does not approve architecture or UI |
| D-004 / 2026-11-01 | Confirmed: user | Short AGENTS.md, three repo-local skills | Persistent rules are separate from procedures and runtime prompts |
| D-005 / 2026-11-01 | Implementation default | Environment checker uses only the Python standard library | Initial verification without API, dependency installation, or network; Python 3.11+ is the minimum for this scaffold only |

New entry: ID, date, confirmed/proposed/superseded, who/what confirmed it, decision, rationale, consequences. An agent proposal does not automatically become confirmed. When superseding a decision, preserve a reference to the previous one.
