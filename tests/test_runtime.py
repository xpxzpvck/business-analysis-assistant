import asyncio
from types import SimpleNamespace

import httpx
import pytest

from ba_assistant.openrouter import FreeProviderConfig, OpenRouter, ProviderConfig
from ba_assistant.runtime import refresh_workflow
from ba_assistant.session import Session
from ba_assistant.workflow import Workflow, WorkflowError
from test_domain import ready_session
from test_openrouter import success
from test_ui_exports import APP
from streamlit.testing.v1 import AppTest


def test_existing_ling_session_migrates_to_free_router_without_request():
    session = ready_session()
    session.user_message("Уточнення.")
    requests = []
    provider = OpenRouter(
        ProviderConfig(api_key="dummy", model="inclusionai/ling-3.2-flash:free", max_attempts=1),
        transport=httpx.MockTransport(lambda request: requests.append(request)),
    )
    previous = Workflow(session, provider)
    current = refresh_workflow(previous)
    assert current.provider.config.model == "openrouter/free"
    assert current.provider.config.api_key.get_secret_value() == "dummy"
    assert current.provider.config.max_attempts == 1
    assert current.session.state == session.state
    assert current.records == previous.records
    assert requests == []


def test_refresh_preserves_review_and_pending_turn_with_current_classes():
    session = ready_session()
    session.user_message("Уточнення.")
    provider = OpenRouter(FreeProviderConfig(api_key="dummy"),
                          transport=httpx.MockTransport(lambda request: httpx.Response(200, json=success())))
    old_class = type("OpenRouter", (), {"__module__": "ba_assistant.openrouter"})
    old = old_class()
    old.config, old.transport, old.sleep = provider.config, provider.transport, provider.sleep
    previous = SimpleNamespace(session=session, provider=old, records=())
    current = refresh_workflow(previous)
    assert type(current) is Workflow and type(current.provider) is OpenRouter
    assert current.session.state == session.state
    assert current.provider.config.api_key.get_secret_value() == "dummy"
    asyncio.run(current.analyze_pending())
    assert not current.session.state.pending_analysis
    assert len(current.session.state.reviews) == 5


def test_refreshed_ui_handles_validation_failure_without_traceback():
    session = ready_session()
    session.user_message("Уточнення.")
    body = success()
    body["choices"][0]["message"]["content"] = '''{"facts":[{"category":"users","text":"Invented",
        "evidence":[{"message_id":"MSG-001","quote":"PRIVATE invented quote"}]}],"issues":[],"questions":[]}'''
    provider = OpenRouter(FreeProviderConfig(api_key="dummy"),
                          transport=httpx.MockTransport(lambda request: httpx.Response(200, json=body)))
    app = AppTest.from_file(APP).run()
    app.session_state.workflow = SimpleNamespace(session=session, provider=provider, records=())
    app.session_state.live_mode = True
    app.run()
    app.button(key="retry").click().run()
    assert not app.exception
    assert "цитату" in app.error[0].value
    assert "PRIVATE" not in app.error[0].value
    assert app.session_state.workflow.session.state == session.state


def test_unknown_validation_message_is_not_exposed():
    class Provider:
        async def complete(self, messages, output):
            raise ValueError("PRIVATE content")

    flow = Workflow(Session(), Provider())
    with pytest.raises(WorkflowError, match="^validation_error$"):
        asyncio.run(flow.submit("Brief"))
