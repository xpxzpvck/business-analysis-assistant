"""Transactional local controller. UI actions, never model text, authorize review."""

from .models import (
    Analysis, ArtifactBundle, Fact, Issue, Message, ReviewEvent, SessionState,
)
from .validation import finalization_errors, unique, validate_artifacts


class Session:
    def __init__(self):
        self._state = SessionState()

    @property
    def state(self):
        return self._state.model_copy(deep=True)

    def _commit(self, candidate):
        if sum(len(m.text) for m in candidate.messages) > 60000:
            raise ValueError("Dialogue size limit exceeded")
        candidate.version += 1
        candidate.artifacts = None
        candidate.requested_version = None
        self._state = SessionState.model_validate(candidate.model_dump())

    def user_message(self, text: str):
        if len(text) > 8000 or sum(len(m.text) for m in self._state.messages) + len(text) > 60000:
            raise ValueError("Dialogue size limit exceeded")
        candidate = self.state
        candidate.clarification_answered |= any(m.review_question for m in candidate.messages)
        candidate.messages.append(Message(id=f"MSG-{len(candidate.messages) + 1:03}", role="user", text=text))
        candidate.pending_analysis = True
        self._commit(candidate)

    def apply_analysis(self, payload: dict, source_version: int):
        if source_version != self._state.version or not self._state.pending_analysis:
            raise ValueError("Analysis is stale or no user turn is pending")
        result = Analysis.model_validate(payload)
        candidate = self.state
        users = {m.id: m.text for m in candidate.messages if m.role == "user"}
        targets = [d.target_id for d in result.facts if d.target_id is not None]
        unique(targets, "fact update targets")
        original_issue_ids = {i.id for i in candidate.issues}
        for draft in result.facts:
            for evidence in draft.evidence:
                if evidence.message_id not in users or evidence.quote not in users[evidence.message_id]:
                    raise ValueError("Fact evidence must quote an existing user message")
            old = next((f for f in candidate.facts if f.id == draft.target_id), None)
            if draft.target_id and old is None:
                raise ValueError("Unknown fact update target")
            if old and (old.category != draft.category or old.status in {"rejected", "superseded"}):
                raise ValueError("Cannot change fact category or revive a removed fact")
            if old:
                archived = old.model_copy(deep=True)
                archived.status = "superseded"
                candidate.history.append(archived)
                candidate.facts.remove(old)
                # A previously resolved issue must be reviewed again if its facts change.
                for issue in candidate.issues:
                    if issue.resolved and (not issue.fact_ids or old.id in issue.fact_ids):
                        issue.resolved = False
                        issue.raised_at_message_id = next(
                            m.id for m in reversed(candidate.messages) if m.role == "user"
                        )
                        issue.resolution_message_id = None
                        issue.resolution_note = None
            prefix = "REQ" if draft.category == "requirements" else "FACT"
            fact_id = old.id if old else f"{prefix}-{len(candidate.facts) + 1:03}"
            candidate.facts.append(Fact(
                id=fact_id, revision=old.revision + 1 if old else 1,
                category=draft.category, text=draft.text, evidence=draft.evidence,
                status="proposed" if draft.proposal else "unreviewed",
            ))
        fact_ids = {f.id for f in candidate.facts}
        for draft in result.issues:
            if not set(draft.fact_ids) <= fact_ids:
                raise ValueError("Issue references unknown facts")
            fields = draft.model_dump()
            if draft.kind == "conflict":
                fields["blocking"] = True
            candidate.issues.append(Issue(
                id=f"ISS-{len(candidate.issues) + 1:03}",
                raised_at_message_id=next(m.id for m in reversed(candidate.messages) if m.role == "user"),
                **fields,
            ))
        positions = {m.id: n for n, m in enumerate(candidate.messages)}
        unique([r.issue_id for r in result.resolutions], "resolution targets")
        for resolution in result.resolutions:
            if resolution.issue_id not in original_issue_ids:
                raise ValueError("Unknown resolution target")
            issue = next(i for i in candidate.issues if i.id == resolution.issue_id)
            for evidence in resolution.evidence:
                if (evidence.message_id not in users
                        or evidence.quote not in users[evidence.message_id]
                        or positions[evidence.message_id] < positions[issue.raised_at_message_id]):
                    raise ValueError("Issue resolution requires current user evidence")
            issue.resolved = True
            issue.resolution_message_id = max(
                (e.message_id for e in resolution.evidence), key=positions.get)
            issue.resolution_note = resolution.explanation
        for question in result.questions:
            candidate.messages.append(Message(
                id=f"MSG-{len(candidate.messages) + 1:03}", role="assistant", text=question,
                review_question=True,
            ))
        if sum(len(m.text) for m in candidate.messages) > 60000:
            raise ValueError("Dialogue size limit exceeded")
        candidate.pending_analysis = False
        self._commit(candidate)

    def request_reanalysis(self):
        """Reassess existing dialogue without duplicating a user answer."""
        if self._state.pending_analysis:
            return
        if not any(m.role == "user" for m in self._state.messages):
            raise ValueError("No dialogue to analyze")
        candidate = self.state
        candidate.pending_analysis = True
        self._commit(candidate)

    def ask_review(self):
        candidate = self.state
        if candidate.pending_analysis:
            raise ValueError("Analyze the latest message first")
        candidate.messages.append(Message(
            id=f"MSG-{len(candidate.messages) + 1:03}", role="assistant",
            text="Перевірте факти й підтвердьте або відхиліть кожен із них.", review_question=True,
        ))
        self._commit(candidate)

    def review_facts(self, fact_ids: list[str], *, confirm: bool):
        if type(confirm) is not bool:
            raise ValueError("Review action must be a boolean")
        candidate = self.state
        if candidate.pending_analysis or not any(m.review_question for m in candidate.messages):
            raise ValueError("Analysis and a review question are required")
        if not fact_ids:
            raise ValueError("Select at least one fact")
        unique(fact_ids, "review fact IDs")
        for fact_id in fact_ids:
            fact = next((f for f in candidate.facts if f.id == fact_id), None)
            if fact is None or fact.status in {"rejected", "superseded"}:
                raise ValueError("Cannot review unknown or removed fact")
            fact.status = "confirmed" if confirm else "rejected"
            candidate.reviews.append(ReviewEvent(fact_id=fact.id, revision=fact.revision, action="confirm" if confirm else "reject"))
        candidate.clarification_answered = True
        self._commit(candidate)

    def resolve_issue(self, issue_id: str, message_id: str, note: str):
        """Explicit user review action; note explains the chosen resolution."""
        candidate = self.state
        if candidate.pending_analysis:
            raise ValueError("Analyze the resolution answer first")
        if not any(m.id == message_id and m.role == "user" for m in candidate.messages):
            raise ValueError("Resolution needs user-message evidence")
        issue = next((i for i in candidate.issues if i.id == issue_id), None)
        if issue is None:
            raise ValueError("Unknown issue")
        positions = {m.id: i for i, m in enumerate(candidate.messages)}
        if positions[message_id] <= positions[issue.raised_at_message_id]:
            raise ValueError("Resolution needs a new user answer after the issue")
        issue.resolution_note = note
        issue.resolution_message_id = message_id
        issue.resolved = True
        self._commit(candidate)

    def restore_facts(self, fact_ids: list[str]):
        """Explicitly return rejected facts to review; never confirm implicitly."""
        candidate = self.state
        if candidate.pending_analysis:
            raise ValueError("Analyze the latest message first")
        if not fact_ids:
            raise ValueError("Select at least one fact")
        unique(fact_ids, "restore fact IDs")
        for fact_id in fact_ids:
            fact = next((f for f in candidate.facts if f.id == fact_id), None)
            if fact is None or fact.status != "rejected":
                raise ValueError("Only rejected facts can be restored")
            fact.status = "unreviewed"
            candidate.reviews.append(ReviewEvent(fact_id=fact.id, revision=fact.revision,
                                                 action="restore"))
        self._commit(candidate)

    def request_generation(self) -> int:
        if errors := finalization_errors(self._state):
            raise ValueError("; ".join(errors))
        self._state.requested_version = self._state.version
        return self._state.version

    def resolve_issues(self, issue_ids: list[str], message_id: str):
        """One explicit review action; all selections succeed or none are committed."""
        if not issue_ids:
            raise ValueError("Select at least one issue")
        unique(issue_ids, "issue IDs")
        draft = Session()
        draft._state = self.state
        for issue_id in issue_ids:
            draft.resolve_issue(issue_id, message_id,
                                "Користувач підтвердив, що вибрана відповідь уточнює цей пункт.")
        self._state = draft.state

    def accept_artifacts(self, payload: dict):
        bundle = ArtifactBundle.model_validate(payload)
        if self._state.requested_version != self._state.version:
            raise ValueError("Explicit generation request required")
        validate_artifacts(self._state, bundle)
        self._state.artifacts = bundle.model_copy(deep=True)

    def export_json(self) -> str:
        if self._state.artifacts is None:
            raise ValueError("No validated final artifacts")
        validate_artifacts(self._state, self._state.artifacts)
        # Include referenced facts/issues so proposals and open questions are readable.
        return self._state.model_dump_json(indent=2)
