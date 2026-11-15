import pytest
from streamlit.testing.v1 import AppTest

from ba_assistant.openrouter import FreeProviderConfig, OpenRouter
from ba_assistant.session import Session
from ba_assistant.workflow import Workflow
from test_ui_exports import APP


def review_session():
    session = Session()
    session.user_message("Initial brief.")
    session.apply_analysis({"issues": [
        {"kind": "gap", "description": name, "fact_ids": []}
        for name in ["Scope?", "Roles?", "Constraints?"]
    ], "questions": ["Scope?", "Roles?", "Constraints?"]}, session.state.version)
    session.user_message("One shared answer for the three questions.")
    session.apply_analysis({}, session.state.version)
    return session


def test_three_tabs_and_one_shared_review_answer():
    session = review_session()
    app = AppTest.from_file(APP).run()
    app.session_state.workflow = Workflow(session, OpenRouter(FreeProviderConfig(api_key="dummy")))
    app.session_state.live_mode = True
    app.run()
    assert not app.exception
    assert [tab.label for tab in app.tabs] == ["Діалог", "Перевірка", "Документи"]
    assert not app.tabs[0].multiselect
    assert not app.tabs[1].chat_input
    assert len(app.tabs[0].chat_input) == 1
    assert not app.tabs[1].selectbox
    assert not app.tabs[1].multiselect
    assert not any(b.key == "resolve_selected" for b in app.button)
    assert app.button(key="generate").disabled
    assert any("Діалог" in item.value for item in app.tabs[2].info)


def test_batch_resolution_is_atomic():
    session = review_session()
    before = session.state
    answer = [m.id for m in before.messages if m.role == "user"][-1]
    with pytest.raises(ValueError, match="Unknown issue"):
        session.resolve_issues(["ISS-001", "ISS-999"], answer)
    assert session.state == before
    session.user_message("Pending changes")
    before = session.state
    with pytest.raises(ValueError, match="Analyze"):
        session.resolve_issues(["ISS-001", "ISS-002"], answer)
    assert session.state == before
