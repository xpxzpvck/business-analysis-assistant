import asyncio
import json

import httpx
import pytest

from scripts import evaluate_components as evaluation


def test_freeze_rejects_changed_sources_before_test_input_is_opened(tmp_path, monkeypatch):
    path = tmp_path / "freeze.json"
    path.write_text(json.dumps({"sources": {"prompt": "before"}}), encoding="utf-8")
    monkeypatch.setattr(evaluation, "source_fingerprint", lambda: {"prompt": "before"})
    evaluation.check_freeze(path)
    monkeypatch.setattr(evaluation, "source_fingerprint", lambda: {"prompt": "after"})
    with pytest.raises(ValueError, match="Sources changed"):
        evaluation.check_freeze(path)


def test_failed_cases_remain_in_category_denominator():
    rows = [{"id": "ok", "analysis": {"facts": [{"category": "users", "proposal": False}]}},
            {"id": "failed", "outcome": "timeout"}]
    gold = {name: {"facts": [{"category": "users"}], "issues": [], "question_topics": []}
            for name in ("ok", "failed")}
    scores = evaluation.score_analyzers(rows, gold)
    assert (scores["tp"], scores["fp"], scores["fn"]) == (1, 0, 1)
    assert scores["recall"] == 0.5
    gold["failed"]["issues"] = [{"type": "conflict"}]
    evaluation.score_analyzers(rows, gold)
    assert rows[1]["expected_conflict"] is True
    assert rows[1]["predicted_conflict"] is False


def test_analyzer_evaluation_uses_input_only_and_preserves_failure(monkeypatch):
    requests = []

    class Transport(httpx.MockTransport):
        model = "test-only"

    def handler(request):
        payload = json.loads(request.content)
        requests.append(payload)
        return httpx.Response(429)

    monkeypatch.setattr(evaluation, "ModelTelemetry", lambda: Transport(handler))
    row = asyncio.run(evaluation.analyzer_case(
        {"id": "DEV-S02", "messages": [{"id": "m1", "role": "user", "content": "Manager."}]},
        "dummy"))
    assert row["outcome"] == "http_error" and row["status"] == 429
    assert len(requests) == 1 and row["calls"][0]["attempts"] == 1
    envelope = json.loads(requests[0]["messages"][-1]["content"])
    assert set(envelope) == {"source_version", "conversation", "facts", "issues"}
    assert envelope["conversation"][0]["text"] == "Manager."
    assert requests[0]["provider"]["max_price"]["completion"] == 0
