"""Typed contracts; model responses have no authority to confirm user facts."""

from typing import Annotated, Literal

from pydantic import BaseModel, ConfigDict, Field, StringConstraints

Text = Annotated[str, StringConstraints(strip_whitespace=True, min_length=1)]
Category = Literal["goals", "users", "requirements", "constraints", "team_roles"]
CATEGORIES = {"goals", "users", "requirements", "constraints", "team_roles"}


class Contract(BaseModel):
    model_config = ConfigDict(extra="forbid", strict=True, validate_assignment=True)


class Message(Contract):
    id: Text
    role: Literal["user", "assistant"]
    text: Text
    review_question: bool = False


class Evidence(Contract):
    message_id: Text
    quote: Text


class FactDraft(Contract):
    category: Category
    text: Text
    evidence: list[Evidence] = Field(min_length=1)
    proposal: bool = False
    target_id: Text | None = None


class Fact(Contract):
    id: Text
    revision: int = Field(default=1, ge=1)
    category: Category
    text: Text
    evidence: list[Evidence]
    status: Literal["unreviewed", "confirmed", "proposed", "rejected", "superseded"]


class IssueDraft(Contract):
    kind: Literal["gap", "conflict"]
    description: Text
    fact_ids: list[Text]
    blocking: bool = True


class Issue(IssueDraft):
    id: Text
    raised_at_message_id: Text
    resolved: bool = False
    resolution_message_id: Text | None = None
    resolution_note: Text | None = None


class IssueResolution(Contract):
    issue_id: Text
    explanation: Text
    evidence: list[Evidence] = Field(min_length=1)


class Analysis(Contract):
    facts: list[FactDraft] = Field(default_factory=list)
    issues: list[IssueDraft] = Field(default_factory=list)
    questions: list[Text] = Field(default_factory=list, max_length=3)
    resolutions: list[IssueResolution] = Field(default_factory=list)


class Section(Contract):
    title: Text
    text: Text
    fact_ids: list[Text] = Field(min_length=1)


class Task(Contract):
    id: Text
    title: Text
    requirement_ids: list[Text] = Field(min_length=1)
    acceptance_criteria: list[Text] = Field(min_length=1)


class Assignment(Contract):
    role_id: Text
    duties: list[Literal["R", "A", "C", "I"]] = Field(min_length=1)


class Activity(Contract):
    id: Text
    task_id: Text
    assignments: list[Assignment] = Field(min_length=1)


class ArtifactBundle(Contract):
    source_version: int = Field(ge=0)
    specification: list[Section] = Field(min_length=1)
    tasks: list[Task] = Field(min_length=1)
    raci: list[Activity] = Field(min_length=1)
    proposal_ids: list[Text] = Field(default_factory=list)
    open_issue_ids: list[Text] = Field(default_factory=list)
    recommendation_notice: Literal["Tasks and RACI are generated recommendations"] = (
        "Tasks and RACI are generated recommendations"
    )


class ReviewEvent(Contract):
    fact_id: Text
    revision: int
    action: Literal["confirm", "reject", "restore"]


class SessionState(Contract):
    version: int = 0
    messages: list[Message] = Field(default_factory=list)
    facts: list[Fact] = Field(default_factory=list)
    history: list[Fact] = Field(default_factory=list)
    issues: list[Issue] = Field(default_factory=list)
    reviews: list[ReviewEvent] = Field(default_factory=list)
    pending_analysis: bool = False
    clarification_answered: bool = False
    requested_version: int | None = None
    artifacts: ArtifactBundle | None = None
