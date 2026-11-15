"""Scripted test responses; never imported by application code."""

import json

from ba_assistant.models import Analysis, ArtifactBundle
from ba_assistant.openrouter import Completion

FACTS = [
    ("goals", "Скоротити ручне опрацювання заявок."),
    ("users", "Користувачі — працівники."),
    ("requirements", "Працівник створює заявку."),
    ("constraints", "Система працює в локальній мережі."),
    ("team_roles", "Розробник."),
]
BRIEF = " ".join(text for _, text in FACTS)


class ScriptedProvider:
    async def complete(self, messages, output):
        data = json.loads(messages[-1]["content"])
        if output is Analysis:
            latest = next(m for m in reversed(data["conversation"]) if m["role"] == "user")
            if latest["text"] != BRIEF or data["facts"]:
                raise ValueError("Demo supports only its fixed brief")
            value = Analysis.model_validate({"facts": [
                {"category": category, "text": text,
                 "evidence": [{"message_id": latest["id"], "quote": text}]}
                for category, text in FACTS
            ], "questions": ["Перевірте кожен факт. Чи відповідає він опису демопроєкту?"]})
        elif output is ArtifactBundle:
            facts = data["confirmed_facts"]
            requirement = next(f["id"] for f in facts if f["category"] == "requirements")
            role = next(f["id"] for f in facts if f["category"] == "team_roles")
            value = ArtifactBundle.model_validate({
                "source_version": data["source_version"],
                "specification": [{"title": "Обсяг демопроєкту", "text": BRIEF,
                                   "fact_ids": [f["id"] for f in facts]}],
                "tasks": [{"id": "TASK-001", "title": "Реалізувати створення заявки",
                           "requirement_ids": [requirement],
                           "acceptance_criteria": ["Після надсилання форми створюється одна заявка."]}],
                "raci": [{"id": "ACT-001", "task_id": "TASK-001",
                          "assignments": [{"role_id": role, "duties": ["R", "A"]}]}],
                "proposal_ids": [f["id"] for f in data["proposed_facts"]],
                "open_issue_ids": [i["id"] for i in data["open_issues"]],
            })
        else:
            raise ValueError("Unsupported demo output")
        return Completion(value=value, attempts=1, elapsed_seconds=0, usage=None)
