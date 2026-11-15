"""Validated document exports, deliberately excluding conversation and review history."""

import html
import json
import re

from .models import SessionState
from .validation import validate_artifacts


def document_data(state: SessionState) -> dict:
    if state.artifacts is None:
        raise ValueError("No current documents")
    validate_artifacts(state, state.artifacts)
    return {
        "format_version": 1,
        "demonstration": False,
        "artifacts": state.artifacts.model_dump(),
        "confirmed_facts": [f.model_dump(include={"id", "category", "text", "revision"})
                            for f in state.facts if f.status == "confirmed"],
        "proposals": [f.model_dump(include={"id", "category", "text"})
                      for f in state.facts if f.status == "proposed"],
        "open_questions": [i.model_dump(include={"id", "kind", "description", "blocking"})
                           for i in state.issues if not i.resolved],
    }


def export_json(state: SessionState) -> str:
    return json.dumps(document_data(state), ensure_ascii=False, indent=2)


def escape(value: str) -> str:
    # Quotes are plain text here, never HTML attributes. Escaping apostrophes
    # produces numeric entities whose # is then escaped as Markdown punctuation.
    text = html.escape(value, quote=False).replace("\n", " ").replace("\r", " ")
    return re.sub(r"([\\`*_{}\[\]()#+.!|>~-])", r"\\\1", text)


def export_markdown(state: SessionState) -> str:
    data = document_data(state)
    bundle = data["artifacts"]
    lines = ["# Бізнес-вимоги", ""]
    lines += [f"Версія стану: {state.version}", "", "## Підтверджені факти", ""]
    for fact in data["confirmed_facts"]:
        lines += [f"- {escape(fact['id'])}: {escape(fact['text'])}"]
    lines += ["", "## Специфікація", ""]
    for section in bundle["specification"]:
        lines += [f"### {escape(section['title'])}", "", escape(section["text"]), "",
                  "Джерела: " + ", ".join(map(escape, section["fact_ids"])), ""]
    lines += ["## Завдання та критерії приймання", "",
              "Завдання й RACI — згенеровані рекомендації, які потребують перегляду.", ""]
    for task in bundle["tasks"]:
        lines += [f"### {escape(task['id'])}: {escape(task['title'])}", "",
                  "Вимоги: " + ", ".join(map(escape, task["requirement_ids"])), ""]
        lines += [f"- {escape(item)}" for item in task["acceptance_criteria"]]
        lines += [""]
    roles = {f["id"]: f["text"] for f in data["confirmed_facts"]}
    lines += ["## RACI", "", "R — виконує; A — відповідає за результат; C — консультує; I — поінформований.", "",
              "### Ролі", ""]
    used_roles = dict.fromkeys(assignment["role_id"] for activity in bundle["raci"]
                               for assignment in activity["assignments"])
    lines += [f"- {escape(role)}: {escape(roles[role])}" for role in used_roles]
    lines += ["", "| Дія | Завдання | Роль | Участь |", "|---|---|---|---|"]
    for activity in bundle["raci"]:
        for assignment in activity["assignments"]:
            role = assignment["role_id"]
            cells = [activity["id"], activity["task_id"], role, ", ".join(assignment["duties"])]
            lines += ["| " + " | ".join(map(escape, cells)) + " |"]
    for title, items, field in [("Непідтверджені пропозиції", data["proposals"], "text"),
                                 ("Відкриті питання", data["open_questions"], "description")]:
        lines += ["", f"## {title}", ""]
        lines += [f"- {escape(item['id'])}: {escape(item[field])}" for item in items] or ["Немає."]
    return "\n".join(lines) + "\n"
