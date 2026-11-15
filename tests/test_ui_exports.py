import json
from pathlib import Path

import httpx
import pytest
from streamlit.testing.v1 import AppTest

from ba_assistant.exports import escape, export_json, export_markdown
from ba_assistant.models import Analysis, ArtifactBundle
from scripted_provider import BRIEF, ScriptedProvider
from test_domain import bundle, ready_session

APP = str(Path(__file__).resolve().parents[1] / "app.py")


def connected_app(*, fail_first=False):
    app = AppTest.from_file(APP).run()
    app.text_input(key="api_key").input("dummy").run()
    app.button(key="connect").click().run()
    calls = 0

    async def handler(request):
        nonlocal calls
        calls += 1
        if fail_first and calls == 1:
            return httpx.Response(503)
        payload = json.loads(request.content)
        output = Analysis if payload["response_format"]["json_schema"]["name"] == "Analysis" else ArtifactBundle
        reply = await ScriptedProvider().complete(payload["messages"], output)
        return httpx.Response(200, json={"choices": [{"finish_reason": "stop", "message": {
            "content": reply.value.model_dump_json()}}]})

    app.session_state.workflow.provider.transport = httpx.MockTransport(handler)
    return app


def generated():
    session = ready_session()
    session.request_generation()
    session.accept_artifacts(bundle(session))
    return session


def test_exports_exclude_transcript_and_keep_references():
    state = generated().state
    data = json.loads(export_json(state))
    assert data["demonstration"] is False
    assert not {"messages", "history", "reviews", "evidence"} & data.keys()
    assert "evidence" not in data["confirmed_facts"][0]
    assert data["artifacts"]["tasks"][0]["requirement_ids"] == ["REQ-003"]
    markdown = export_markdown(state)
    assert "ДЕМОНСТРАЦІЯ" not in markdown
    assert "Developer" in markdown and "R, A" in markdown
    assert "згенеровані рекомендації" in markdown


def test_export_rejects_stale_and_missing_documents():
    session = generated()
    state = session.state
    state.version += 1
    with pytest.raises(ValueError, match="Stale"):
        export_markdown(state)
    session.user_message("Changed requirements")
    with pytest.raises(ValueError, match="No current"):
        export_json(session.state)


def test_markdown_escapes_untrusted_content():
    value = escape('<script>x</script> ![image](https://example.com) |\n# title')
    assert "<script>" not in value and "![image]" not in value
    assert "\\|" in value and "\n" not in value


def test_export_preserves_apostrophes_without_enabling_html():
    assert escape('Обов\'язкове "ім\'я"') == 'Обов\'язкове "ім\'я"'
    assert escape("<script>&#x27;</script>") == "&lt;script&gt;&amp;\\#x27;&lt;/script&gt;"
    state = generated().state
    state.artifacts.specification[0].text = "Ім'я працівника"
    assert "Ім'я працівника" in export_markdown(state)


def test_raci_describes_each_role_once_and_keeps_assignment_references():
    state = generated().state
    activity = state.artifacts.raci[0].model_copy(deep=True)
    activity.id = "ACT-002"
    state.artifacts.raci.append(activity)
    before = state.model_dump()
    raci = export_markdown(state).split("## RACI\n", 1)[1].split("## Непідтверджені", 1)[0]
    role = next(f for f in state.facts if f.id == activity.assignments[0].role_id)
    assert raci.count(escape(role.text)) == 1
    rows = [line for line in raci.splitlines() if line.startswith("| ACT")]
    assert len(rows) == 2
    assert all(escape(role.id) in row and escape(role.text) not in row for row in rows)
    assert state.model_dump() == before


def test_connected_review_generation_reset():
    app = connected_app()
    assert not app.exception
    assert app.button(key="generate").disabled
    app.chat_input[0].set_value(BRIEF).run()
    assert not app.exception
    state = app.session_state.workflow.session.state
    assert len(state.facts) == 5 and state.artifacts is None
    app.multiselect[0].set_value([f.id for f in state.facts]).run()
    app.button(key="confirm").click().run()
    assert not app.button(key="generate").disabled
    assert app.session_state.workflow.session.state.artifacts is None
    app.button(key="generate").click().run()
    assert not app.exception
    assert len(app.get("download_button")) == 2
    assert app.session_state.workflow.session.state.artifacts is not None
    app.button(key="reset").click().run()
    assert "workflow" not in app.session_state
    assert not app.chat_input
    assert len(app.get("download_button")) == 0


def test_reject_invalidates_downloads_and_blocks_generation():
    app = connected_app()
    app.chat_input[0].set_value(BRIEF).run()
    ids = [f.id for f in app.session_state.workflow.session.state.facts]
    app.multiselect[0].set_value(ids).run()
    app.button(key="confirm").click().run()
    app.button(key="generate").click().run()
    app.multiselect[0].set_value([ids[0]]).run()
    app.button(key="reject").click().run()
    assert not app.exception
    assert app.button(key="generate").disabled
    assert len(app.get("download_button")) == 0
    assert any("відхилених" in item.value for item in app.tabs[2].info)
    app.multiselect[-1].set_value([ids[0]]).run()
    app.button(key="restore_facts").click().run()
    assert not app.exception
    goal = next(f for f in app.session_state.workflow.session.state.facts if f.id == ids[0])
    assert goal.status == "unreviewed"
    assert app.button(key="generate").disabled
    app.multiselect[0].set_value([ids[0]]).run()
    app.button(key="confirm").click().run()
    assert not app.button(key="generate").disabled
    assert app.session_state.workflow.session.state.artifacts is None


def test_failed_analysis_can_retry_without_duplicate_message():
    app = connected_app(fail_first=True)
    app.chat_input[0].set_value(BRIEF).run()
    assert len(app.error) == 1
    assert app.button(key="generate").disabled
    app.button(key="retry").click().run()
    assert not app.exception and not app.error
    state = app.session_state.workflow.session.state
    assert len([m for m in state.messages if m.role == "user"]) == 1
    assert len(state.facts) == 5 and not state.pending_analysis
