"""Structural checks, not semantic proof of model output quality."""

from .models import ArtifactBundle, CATEGORIES, SessionState


def unique(values, label):
    if len(values) != len(set(values)):
        raise ValueError(f"Duplicate {label}")


def finalization_errors(state: SessionState) -> list[str]:
    errors = []
    if state.pending_analysis:
        errors.append("Latest user message has not been analyzed")
    if not state.clarification_answered:
        errors.append("Clarification or review response required")
    confirmed = {f.category for f in state.facts if f.status == "confirmed"}
    if missing := CATEGORIES - confirmed:
        errors.append("Missing confirmed categories: " + ", ".join(sorted(missing)))
    if any(f.status == "unreviewed" for f in state.facts):
        errors.append("Unreviewed facts remain")
    if any(i.blocking and not i.resolved for i in state.issues):
        errors.append("Blocking issues remain")
    return errors


def validate_artifacts(state: SessionState, bundle: ArtifactBundle) -> None:
    if errors := finalization_errors(state):
        raise ValueError("; ".join(errors))
    if bundle.source_version != state.version:
        raise ValueError("Stale artifact version")
    confirmed = {f.id: f for f in state.facts if f.status == "confirmed"}
    requirements = {fid for fid, fact in confirmed.items() if fact.category == "requirements"}
    roles = {fid for fid, fact in confirmed.items() if fact.category == "team_roles"}
    unique([t.id for t in bundle.tasks], "task IDs")
    unique([a.id for a in bundle.raci], "activity IDs")
    used = set()
    for section in bundle.specification:
        if not set(section.fact_ids) <= confirmed.keys():
            raise ValueError("Specification references unconfirmed or unknown facts")
    for task in bundle.tasks:
        if not set(task.requirement_ids) <= requirements:
            raise ValueError("Task references unconfirmed or unknown requirements")
        used.update(task.requirement_ids)
    if used != requirements:
        raise ValueError("Tasks do not cover all confirmed requirements")
    task_ids = {t.id for t in bundle.tasks}
    for activity in bundle.raci:
        if activity.task_id not in task_ids:
            raise ValueError("Unknown RACI task")
        unique([a.role_id for a in activity.assignments], "RACI roles")
        duties = []
        for assignment in activity.assignments:
            if assignment.role_id not in roles:
                raise ValueError("Unknown or unconfirmed team role")
            unique(assignment.duties, "RACI duties")
            duties.extend(assignment.duties)
        if duties.count("A") != 1 or duties.count("R") < 1:
            raise ValueError("RACI requires exactly one A and at least one R")
    if {a.task_id for a in bundle.raci} != task_ids:
        raise ValueError("RACI does not cover all tasks")
    proposals = {f.id for f in state.facts if f.status == "proposed"}
    open_issues = {i.id for i in state.issues if not i.resolved}
    unique(bundle.proposal_ids, "proposal IDs")
    unique(bundle.open_issue_ids, "open issue IDs")
    if set(bundle.proposal_ids) != proposals or set(bundle.open_issue_ids) != open_issues:
        raise ValueError("Proposals or unresolved questions were omitted or invented")
