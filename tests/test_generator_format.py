import asyncio
import json
import re

import httpx
import pytest

from ba_assistant.models import ArtifactBundle
from ba_assistant.openrouter import FreeProviderConfig, OpenRouter
from ba_assistant.workflow import Workflow, WorkflowError, load_prompt
from test_domain import ready_session, bundle


def test_generator_example_conforms_to_actual_contract():
    prompt = load_prompt("generator")
    example = re.search(r"<format_example>\s*(.*?)\s*</format_example>", prompt.text, re.S).group(1)
    parsed = ArtifactBundle.model_validate_json(example)
    assert prompt.name == "generator_v3"
    assert isinstance(parsed.specification, list)
    assert parsed.raci[0].assignments[0].duties == ["R", "A"]


def test_reported_generation_shape_failure_stays_rejected_then_explicitly_repairs():
    session = ready_session()
    requests = []

    def handler(request):
        requests.append(json.loads(request.content))
        payload = bundle(session)
        if len(requests) == 1:
            payload.pop("source_version")
            payload["specification"] = "A Markdown specification is the wrong type."
            payload["raci"][0]["assignments"][0].pop("duties")
        return httpx.Response(200, json={"choices": [{"finish_reason": "stop", "message": {
            "content": json.dumps(payload)}}]})

    flow = Workflow(session, OpenRouter(FreeProviderConfig(api_key="dummy"),
                                        transport=httpx.MockTransport(handler)))
    facts = session.state.facts
    with pytest.raises(WorkflowError, match="output_schema") as caught:
        asyncio.run(flow.generate())
    assert caught.value.diagnostic == (
        "source_version: missing; specification: list_type; raci.0.assignments.0.duties: missing")
    assert session.state.artifacts is None and session.state.facts == facts
    assert len(requests) == 1
    asyncio.run(flow.generate())
    assert session.state.artifacts.source_version == session.state.version
    assert len(requests) == 2
    assert flow.records[-1].prompt_version == "generator_v3"
    assert flow.records[-1].repair_prompt_sha256
    assert requests[1]["provider"]["max_price"]["prompt"] == 0
