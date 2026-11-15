"""Evaluate an exported artifact, without inventing missing session evidence or API telemetry."""

import argparse
import hashlib
import json
from pathlib import Path

from ba_assistant.models import ArtifactBundle


def evaluate(data):
    bundle = ArtifactBundle.model_validate(data["artifacts"])
    facts = data["confirmed_facts"]
    fact_ids = {f["id"] for f in facts}
    requirements = {f["id"] for f in facts if f["category"] == "requirements"}
    roles = {f["id"] for f in facts if f["category"] == "team_roles"}
    tasks = {t.id for t in bundle.tasks}
    covered = {r for t in bundle.tasks for r in t.requirement_ids}
    valid_tasks = sum(set(t.requirement_ids) <= requirements for t in bundle.tasks)
    valid_sections = sum(set(s.fact_ids) <= fact_ids for s in bundle.specification)
    valid_raci = 0
    for activity in bundle.raci:
        duties = [d for assignment in activity.assignments for d in assignment.duties]
        assigned = [a.role_id for a in activity.assignments]
        valid_raci += (activity.task_id in tasks and set(assigned) <= roles
                       and len(assigned) == len(set(assigned))
                       and all(len(a.duties) == len(set(a.duties)) for a in activity.assignments)
                       and duties.count("A") == 1 and duties.count("R") >= 1)
    checks = {
        "unique_fact_ids": len(fact_ids) == len(facts),
        "unique_task_ids": len(tasks) == len(bundle.tasks),
        "unique_activity_ids": len({a.id for a in bundle.raci}) == len(bundle.raci),
        "all_requirements_covered": bool(requirements) and covered == requirements,
        "task_references_valid": valid_tasks == len(bundle.tasks),
        "specification_references_valid": valid_sections == len(bundle.specification),
        "raci_valid": valid_raci == len(bundle.raci),
        "raci_covers_tasks": {a.task_id for a in bundle.raci} == tasks,
        "proposals_preserved": set(bundle.proposal_ids) == {p["id"] for p in data["proposals"]},
        "questions_preserved": set(bundle.open_issue_ids) == {q["id"] for q in data["open_questions"]},
    }
    return {
        "checks": checks,
        "counts": {"facts": len(facts), "requirements_covered": len(requirements & covered),
                   "requirements_total": len(requirements), "valid_tasks": valid_tasks,
                   "tasks_total": len(bundle.tasks), "valid_sections": valid_sections,
                   "sections_total": len(bundle.specification), "valid_raci": valid_raci,
                   "raci_total": len(bundle.raci)},
        "limitations": "Export-only structural checks; confirmation provenance, semantic quality, "
                       "latency, model identity and live success rate are not established.",
    }


def main():
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("export", type=Path)
    args = parser.parse_args()
    raw = args.export.read_bytes()
    result = evaluate(json.loads(raw.decode("utf-8-sig")))
    result["input_sha256"] = hashlib.sha256(raw).hexdigest()
    print(json.dumps(result, ensure_ascii=False, indent=2))
    return 0 if all(result["checks"].values()) else 1


if __name__ == "__main__":
    raise SystemExit(main())
