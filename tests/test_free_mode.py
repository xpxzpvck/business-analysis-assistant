import asyncio
import json

import httpx
import pytest
from streamlit.testing.v1 import AppTest

from ba_assistant.models import Analysis
from ba_assistant.openrouter import FREE_MODEL, FreeProviderConfig, OpenRouter
from test_openrouter import MESSAGES, success
from test_ui_exports import APP


def test_start_requires_connection_and_exposes_no_demo():
    app = AppTest.from_file(APP).run()
    assert not app.exception
    assert "workflow" not in app.session_state
    assert not app.chat_input and not app.tabs
    assert [button.key for button in app.button] == ["connect"]


def test_retained_legacy_demo_returns_to_connection_screen():
    from types import SimpleNamespace
    from ba_assistant.session import Session
    from ba_assistant.workflow import Workflow

    app = AppTest.from_file(APP).run()
    old_demo = type("DemoProvider", (), {"__module__": "ba_assistant.demo"})()
    app.session_state.workflow = Workflow(Session(), old_demo)
    app.session_state.legacy_extra = SimpleNamespace()
    app.run()
    assert not app.exception
    assert "workflow" not in app.session_state
    assert not app.chat_input
    assert app.button(key="connect")


@pytest.mark.parametrize("model", ["openai/gpt-4.1-mini", "openrouter/auto", "other/model:free"])
def test_free_configuration_rejects_unapproved_models(model):
    with pytest.raises(ValueError):
        FreeProviderConfig(api_key="dummy", model=model)


def test_free_request_has_no_paid_routing_or_plugins():
    requests = []

    def handler(request):
        requests.append(json.loads(request.content))
        return httpx.Response(200, json=success())

    provider = OpenRouter(FreeProviderConfig(api_key="dummy"), transport=httpx.MockTransport(handler))
    asyncio.run(provider.complete(MESSAGES, Analysis))
    payload = requests[0]
    assert payload["model"] == FREE_MODEL == "openrouter/free"
    assert payload["provider"] == {"require_parameters": True, "allow_fallbacks": False,
                                   "max_price": {"prompt": 0, "completion": 0, "request": 0}}
    assert payload["reasoning"] == {"enabled": False}
    assert not {"models", "plugins", "tools"} & payload.keys()


def test_environment_cannot_override_free_model_with_paid(monkeypatch):
    monkeypatch.setenv("OPENROUTER_API_KEY", "dummy")
    monkeypatch.setenv("OPENROUTER_MODEL", "openai/gpt-4.1-mini")
    with pytest.raises(ValueError):
        FreeProviderConfig.from_env()


def test_live_ui_connect_chat_issue_resolution_and_reset():
    app = AppTest.from_file(APP).run()
    app.text_input(key="api_key").input("dummy-secret").run()
    app.button(key="connect").click().run()
    assert not app.exception
    assert len(app.chat_input) == 1
    assert len(app.text_input) == 1 and app.text_input[0].key == "replacement_key"
    assert app.session_state.workflow.session.state.messages == []

    responses = [
        {"facts": [], "questions": ["Де зберігати дані?"],
         "issues": [{"kind": "conflict", "description": "Локально чи SaaS?", "fact_ids": []}]},
        {"facts": [], "issues": [], "questions": ["Перевірте відповідь."],
         "resolutions": [{"issue_id": "ISS-001", "explanation": "SaaS вилучено.",
                          "evidence": [{"message_id": "MSG-003", "quote": "Відмовляюсь від SaaS"}]}]},
    ]

    def handler(request):
        result = Analysis.model_validate(responses.pop(0))
        return httpx.Response(200, json={"choices": [{"finish_reason": "stop", "message": {
            "content": result.model_dump_json()}}]})

    app.session_state.workflow.provider.transport = httpx.MockTransport(handler)
    app.chat_input[0].set_value("Усе локально. Надіслати всі дані до SaaS.").run()
    assert not app.exception
    assert not app.selectbox
    app.chat_input[0].set_value("Відмовляюсь від SaaS, залишаємо локально.").run()
    assert not app.selectbox  # One answer needs no manual source selection.
    assert not app.exception
    assert app.session_state.workflow.session.state.issues[0].resolved
    assert app.session_state.workflow.session.state.issues[0].resolution_message_id == "MSG-003"
    assert app.button(key="generate").disabled  # Missing confirmed facts still blocks.
    app.button(key="reset").click().run()
    assert "workflow" not in app.session_state


def test_blank_key_stays_offline():
    app = AppTest.from_file(APP).run()
    app.button(key="connect").click().run()
    assert not app.exception and len(app.error) == 1
    assert "workflow" not in app.session_state


def test_schema_error_reaches_ui_without_private_input():
    app = AppTest.from_file(APP).run()
    app.text_input(key="api_key").input("dummy-secret").run()
    app.button(key="connect").click().run()
    body = success()
    body["choices"][0]["message"]["content"] = '{"facts":"PRIVATE"}'
    app.session_state.workflow.provider.transport = httpx.MockTransport(
        lambda request: httpx.Response(200, json=body))
    app.chat_input[0].set_value("Test brief").run()
    assert not app.exception
    assert "output_schema" in app.error[0].value
    assert "facts: list_type" in app.error[0].value
    assert "PRIVATE" not in app.error[0].value
    assert app.session_state.workflow.session.state.pending_analysis


def test_existing_live_session_survives_reloaded_class_identity():
    from types import SimpleNamespace
    from ba_assistant.session import Session
    from ba_assistant.workflow import Workflow

    app = AppTest.from_file(APP).run()
    # Simulate an old provider object retained after its module was reloaded.
    old_provider = SimpleNamespace(config=SimpleNamespace(model=FREE_MODEL))
    app.session_state.workflow = Workflow(Session(), old_provider)
    del app.session_state["live_mode"]
    app.run()
    assert not app.exception
    assert len(app.chat_input) == 1
    assert not any("Демонстрація" in item.value for item in app.warning)
    assert app.session_state.live_mode is True


def test_free_price_guard_survives_config_class_identity_change():
    from ba_assistant.openrouter import ProviderConfig

    requests = []

    def handler(request):
        requests.append(json.loads(request.content))
        return httpx.Response(200, json=success())

    adapter = OpenRouter(ProviderConfig(api_key="dummy", model=FREE_MODEL),
                         transport=httpx.MockTransport(handler))
    asyncio.run(adapter.complete(MESSAGES, Analysis))
    assert requests[0]["provider"]["max_price"]["completion"] == 0


@pytest.mark.parametrize("status, expected", [
    (400, "параметри"), (401, "ключ"), (402, "Не поповнюйте"),
    (403, "Доступ заборонено"), (404, "маршрут"), (422, "формат"),
    (429, "ліміт"), (503, "Помилка сервісу"),
])
def test_http_error_diagnostic_is_safe_and_preserves_pending_turn(status, expected):
    app = AppTest.from_file(APP).run()
    app.text_input(key="api_key").input("dummy-secret").run()
    app.button(key="connect").click().run()
    app.session_state.workflow.provider.transport = httpx.MockTransport(
        lambda request: httpx.Response(status, json={"error": {"message": "dummy-secret PRIVATE"}})
    )
    app.chat_input[0].set_value("Проєкт заявок.").run()
    assert not app.exception
    assert f"Код {status}" in app.error[0].value
    assert expected in app.error[0].value
    assert "dummy-secret" not in app.error[0].value and "PRIVATE" not in app.error[0].value
    assert app.session_state.workflow.session.state.pending_analysis
    assert app.button(key="generate").disabled
