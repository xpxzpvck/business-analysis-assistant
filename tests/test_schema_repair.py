import asyncio
import json

import httpx
import pytest

from ba_assistant.models import Analysis
from ba_assistant.openrouter import FreeProviderConfig, OpenRouter, ProviderError
from ba_assistant.runtime import refresh_workflow
from ba_assistant.session import Session
from ba_assistant.workflow import Workflow, WorkflowError
from test_openrouter import MESSAGES, success


def fixture():
    requests = []

    def handler(request):
        payload = json.loads(request.content)
        requests.append(payload)
        body = success()
        if len(requests) == 1:
            body["choices"][0]["message"]["content"] = '{"facts":[],"issues":[],"questions":[],"confirmed":true,"PRIVATE_EXTRA":"untrusted"}'
        return httpx.Response(200, json=body)

    return OpenRouter(FreeProviderConfig(api_key="dummy"), transport=httpx.MockTransport(handler)), requests


def test_explicit_retry_repairs_after_rerun_without_auto_confirm_or_duplicate_turn():
    provider, requests = fixture()
    flow = Workflow(Session(), provider)
    with pytest.raises(WorkflowError, match="output_schema"):
        asyncio.run(flow.submit("Brief"))
    assert len(requests) == 1
    before = flow.session.state
    assert before.reviews == [] and before.pending_analysis
    flow = refresh_workflow(flow)
    asyncio.run(flow.analyze_pending())
    assert len(requests) == 2
    repair = requests[1]["messages"]
    assert repair[-2]["role"] == "system" and "Remove every additional property" in repair[-2]["content"]
    assert "PRIVATE_EXTRA" in json.loads(repair[-1]["content"])["schema_repair_data"]["previous_output"]
    assert "PRIVATE_EXTRA" not in repr(flow.records)
    assert flow.records[-1].repair_prompt_sha256
    assert len([m for m in flow.session.state.messages if m.role == "user"]) == 1
    assert not flow.session.state.pending_analysis and flow.session.state.reviews == []
    assert flow.provider._schema_failure is None
    assert requests[1]["provider"]["max_price"]["completion"] == 0


def test_changed_request_does_not_reuse_failed_private_output():
    provider, requests = fixture()
    with pytest.raises(ProviderError):
        asyncio.run(provider.complete(MESSAGES, Analysis))
    asyncio.run(provider.complete([{"role": "user", "content": "Different project"}], Analysis))
    assert len(requests[1]["messages"]) == 1
    assert provider._schema_failure is None


def test_existing_failure_without_cached_body_still_receives_repair_instruction():
    provider, requests = fixture()
    flow = Workflow(Session(), provider)
    with pytest.raises(WorkflowError):
        asyncio.run(flow.submit("Brief"))
    provider._schema_failure = None
    asyncio.run(flow.analyze_pending())
    assert requests[1]["messages"][-1]["role"] == "system"
    assert len(requests[1]["messages"]) == len(requests[0]["messages"]) + 1
