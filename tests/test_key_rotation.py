import httpx
from streamlit.testing.v1 import AppTest

from test_openrouter import success
from test_ui_exports import APP


def test_key_rotation_preserves_pending_dialogue_and_retries_with_new_key():
    app = AppTest.from_file(APP).run()
    app.text_input(key="api_key").input("old-dummy").run()
    app.button(key="connect").click().run()
    calls = []

    def handler(request):
        calls.append(request.headers["Authorization"])
        return httpx.Response(429) if len(calls) == 1 else httpx.Response(200, json=success())

    app.session_state.workflow.provider.transport = httpx.MockTransport(handler)
    app.chat_input[0].set_value("Employee requests.").run()
    before = app.session_state.workflow.session.state
    records = app.session_state.workflow.records
    app.text_input(key="replacement_key").input(" new-dummy ").run()
    app.button(key="replace_key").click().run()
    assert not app.exception
    assert app.session_state.workflow.session.state == before
    assert app.session_state.workflow.records == records
    assert len(calls) == 1  # Saving a key never calls the service.
    assert app.text_input(key="replacement_key").value == ""
    app.button(key="retry").click().run()
    assert not app.exception
    assert calls == ["Bearer old-dummy", "Bearer new-dummy"]
    state = app.session_state.workflow.session.state
    assert not state.pending_analysis
    assert len([m for m in state.messages if m.role == "user"]) == 1


def test_empty_replacement_keeps_old_key():
    app = AppTest.from_file(APP).run()
    app.text_input(key="api_key").input("old-dummy").run()
    app.button(key="connect").click().run()
    app.text_input(key="replacement_key").input("   ").run()
    app.button(key="replace_key").click().run()
    assert not app.exception
    assert app.session_state.workflow.provider.config.api_key.get_secret_value() == "old-dummy"
    assert "Попередній ключ залишено" in app.session_state.key_notice
