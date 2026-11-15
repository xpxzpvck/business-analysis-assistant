import asyncio
import json

import httpx
import pytest
from streamlit.testing.v1 import AppTest

from ba_assistant.models import Analysis
from ba_assistant.openrouter import FreeProviderConfig, OpenRouter
from ba_assistant.workflow import Workflow
from test_domain import ready_session
from test_ui_exports import APP


def pending_session():
    session = ready_session()
    session.user_message("Local or cloud?")
    session.apply_analysis({"issues": [{"kind": "conflict", "description": "Local or cloud?",
                                        "fact_ids": ["REQ-003"]}]}, session.state.version)
    session.user_message("Only local. No cloud.")
    return session


def resolution(session):
    return {"issue_id": "ISS-001", "explanation": "User selected local only.",
            "evidence": [{"message_id": session.state.messages[-1].id,
                          "quote": "Only local. No cloud."}]}


def test_grounded_answer_resolves_issue_without_confirming_new_facts():
    session = pending_session()
    before = session.state
    session.apply_analysis({"resolutions": [resolution(session)]}, before.version)
    issue = session.state.issues[0]
    assert issue.resolved and issue.resolution_message_id == before.messages[-1].id
    assert session.state.reviews == before.reviews
    assert session.state.artifacts is None
    session.request_generation()  # Existing confirmed facts + now answered conflict.


@pytest.mark.parametrize("change", ["unknown", "invented", "old", "assistant", "duplicate"])
def test_invalid_resolution_is_rejected_atomically(change):
    session = pending_session()
    item = resolution(session)
    if change == "unknown":
        item["issue_id"] = "ISS-999"
    elif change == "invented":
        item["evidence"][0]["quote"] = "Invented"
    elif change == "old":
        item["evidence"] = [{"message_id": "MSG-001", "quote": "Developer."}]
    elif change == "assistant":
        item["evidence"] = [{"message_id": "MSG-002", "quote": "Перевірте"}]
    before = session.state
    with pytest.raises(ValueError):
        session.apply_analysis({"resolutions": [item, item] if change == "duplicate" else [item]},
                               before.version)
    assert session.state == before


def test_reassessment_of_existing_chat_removes_legacy_blocker_without_duplicate_turn():
    session = pending_session()
    item = resolution(session)
    session.apply_analysis({}, session.state.version)  # Old analyzer left the issue open.
    calls = []

    def handler(request):
        calls.append(json.loads(request.content))
        result = Analysis(resolutions=[item])
        return httpx.Response(200, json={"choices": [{"finish_reason": "stop", "message": {
            "content": result.model_dump_json()}}]})

    app = AppTest.from_file(APP).run()
    app.session_state.workflow = Workflow(session, OpenRouter(FreeProviderConfig(api_key="dummy"),
                                            transport=httpx.MockTransport(handler)))
    app.session_state.live_mode = True
    app.run()
    user_count = sum(m.role == "user" for m in session.state.messages)
    app.button(key="reassess").click().run()
    assert not app.exception
    state = app.session_state.workflow.session.state
    assert sum(m.role == "user" for m in state.messages) == user_count
    assert state.issues[0].resolved and not state.pending_analysis
    assert not app.button(key="generate").disabled
    assert not app.tabs[1].selectbox
    assert not any(b.key == "resolve_selected" for b in app.button)
    assert len(calls) == 1
    assert app.session_state.workflow.records[-1].prompt_version == "analyzer_v3"


def test_unanswered_blocker_is_asked_in_chat_if_model_supplies_no_question():
    session = pending_session()
    provider = OpenRouter(FreeProviderConfig(api_key="dummy"), transport=httpx.MockTransport(
        lambda request: httpx.Response(200, json={"choices": [{"finish_reason": "stop", "message": {
            "content": Analysis().model_dump_json()}}]})))
    flow = Workflow(session, provider)
    asyncio.run(flow.analyze_pending())
    assert "Local or cloud?" in flow.session.state.messages[-1].text
    assert not flow.session.state.issues[0].resolved
