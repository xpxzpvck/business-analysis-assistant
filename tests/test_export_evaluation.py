import json

from ba_assistant.exports import export_json
from scripts.evaluate_export import evaluate
from test_ui_exports import generated


def test_export_evaluation_reports_counts_and_bad_references():
    data = json.loads(export_json(generated().state))
    result = evaluate(data)
    assert all(result["checks"].values())
    assert result["counts"]["requirements_covered"] == 1
    data["artifacts"]["tasks"][0]["requirement_ids"] = ["REQ-999"]
    data["artifacts"]["raci"][0]["assignments"][0]["duties"] = ["R"]
    result = evaluate(data)
    assert not result["checks"]["task_references_valid"]
    assert not result["checks"]["all_requirements_covered"]
    assert not result["checks"]["raci_valid"]
