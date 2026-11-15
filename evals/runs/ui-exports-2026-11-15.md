# Offline UI and document exports — 2026-11-15

- Scope: BA-03–07, SYS-01 (partial), OPS-01. Applied review-deliverable to the completed offline increment. No NLP component or runtime prompt changed; demo replies are explicitly fixed fixtures, separate from evaluation gold.
- Environment: Python 3.14.7, Streamlit 1.67.0, uv lock; working tree uncommitted on base `342c006b72f96f49476cc38a5853f91649be8be9`.
- Changes: Ukrainian review UI, evidence/status display, selected confirmation/rejection, retry pending analysis, explicit generation, reset, labeled demo downloads. Validated document exports include referenced fact/role text and separate proposals/open issues, excluding conversation, evidence quotes and review history. Markdown escapes input text; no unsafe HTML rendering.
- `uv run --frozen --no-sync pytest -q`: 86 passed in 6.89s (80 existing + 6 UI/export checks). New checks cover full fixed demo flow, rejection invalidating downloads, failed analysis retry without duplicate messages, export references/privacy boundary, stale/missing export refusal, Markdown escaping.
- `uv run --frozen --no-sync ruff check .`: PASS.
- Environment checker: PASS. Dataset checker: PASS, 8 dev / 4 test, nine pending human reviews. These are not application quality scores.
- Local Streamlit server started on 127.0.0.1:8501; HTTP health endpoint returned `ok`. Initial restricted socket check failed; allowed local check succeeded. Server stopped after smoke check.
- Functional UI checks use [Streamlit AppTest](https://docs.streamlit.io/develop/api-reference/app-testing/st.testing.v1.apptest); downloads use [st.download_button](https://docs.streamlit.io/develop/api-reference/widgets/st.download_button). Browser visual inspection and actual browser download clicks: NOT RUN.
- Review: new UI, demo provider, exports and tests inspected; tracked documentation diff checked. No keys read or live requests made. No model, token usage or semantic accuracy is claimed.
- Remaining: free-text/correction dialogue and issue-resolution UI, selected live model/budget, semantic evaluation, clean-checkout verification, report and video. The demo is partial SYS-01 evidence only, not completion of Modeling/Evaluation/Deployment.
