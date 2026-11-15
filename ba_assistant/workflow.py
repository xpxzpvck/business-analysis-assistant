"""Versioned prompt assembly and async orchestration; no model calls on import."""

import asyncio
import hashlib
import json
from dataclasses import dataclass
from pathlib import Path
from typing import Protocol

from pydantic import BaseModel

from .models import Analysis, ArtifactBundle, SessionState
from .openrouter import Completion, ProviderError
from .session import Session

PROMPTS = Path(__file__).with_name("prompts")


class Provider(Protocol):
    async def complete(self, messages: list[dict], output: type[BaseModel]) -> Completion: ...


@dataclass(frozen=True)
class Prompt:
    name: str
    text: str
    sha256: str


def load_prompt(kind: str) -> Prompt:
    if kind not in {"analyzer", "generator"}:
        raise ValueError("Unknown prompt kind")
    version = "v3"
    raw = (PROMPTS / f"{kind}_{version}.txt").read_bytes()
    return Prompt(f"{kind}_{version}", raw.decode("utf-8"), hashlib.sha256(raw).hexdigest())


def messages_for(kind: str, state: SessionState, prompt: Prompt) -> list[dict]:
    if kind == "analyzer":
        data = {
            "source_version": state.version,
            "conversation": [m.model_dump(include={"id", "role", "text"}) for m in state.messages],
            "facts": [f.model_dump() for f in state.facts],
            "issues": [i.model_dump() for i in state.issues],
        }
    elif kind == "generator":
        data = {
            "source_version": state.version,
            "confirmed_facts": [f.model_dump() for f in state.facts if f.status == "confirmed"],
            "proposed_facts": [f.model_dump() for f in state.facts if f.status == "proposed"],
            "open_issues": [i.model_dump() for i in state.issues if not i.resolved],
        }
    else:
        raise ValueError("Unknown prompt kind")
    return [{"role": "system", "content": prompt.text},
            {"role": "user", "content": json.dumps(data, ensure_ascii=False)}]


@dataclass(frozen=True)
class CallRecord:
    component: str
    prompt_version: str
    prompt_sha256: str
    source_version: int
    outcome: str
    attempts: int | None
    elapsed_seconds: float | None
    usage: dict | None
    repair_prompt_sha256: str | None = None


class WorkflowError(Exception):
    """Safe UI-facing category. Raw payloads are deliberately excluded."""

    def __init__(self, kind: str, *, status: int | None = None, diagnostic: str | None = None):
        self.status = status if type(status) is int and 100 <= status <= 599 else None
        self.diagnostic = diagnostic
        super().__init__(kind)


class Workflow:
    def __init__(self, session: Session, provider: Provider):
        self.session, self.provider = session, provider
        self._busy = False
        self._records: list[CallRecord] = []

    @property
    def records(self):
        # Return detached metadata; it contains no messages or model outputs.
        from copy import deepcopy
        return tuple(deepcopy(self._records))

    async def submit(self, text: str):
        if self._busy:
            raise WorkflowError("busy")
        if self.session.state.pending_analysis:
            raise WorkflowError("pending_analysis: retry the previous turn first")
        self.session.user_message(text)
        return await self.analyze_pending()

    async def analyze_pending(self):
        return await self._call("analyzer")

    async def generate(self):
        """Call only from the explicit user generate action; never from submit."""
        return await self._call("generator")

    async def _call(self, kind):
        if self._busy:
            raise WorkflowError("busy")
        self._busy = True
        prompt, state, result = None, None, None
        outcome = "failed"
        attempts = None
        try:
            if kind == "analyzer" and not self.session.state.pending_analysis:
                raise WorkflowError("no_pending_analysis")
            if kind == "generator":
                self.session.request_generation()
            state = self.session.state
            prompt = load_prompt(kind)
            output = Analysis if kind == "analyzer" else ArtifactBundle
            if (self._records and self._records[-1].source_version == state.version
                    and self._records[-1].component == kind
                    and self._records[-1].outcome == "output_schema"
                    and hasattr(self.provider, "schema_repair_requested")):
                self.provider.schema_repair_requested = True
            result = await self.provider.complete(messages_for(kind, state, prompt), output)
            attempts = result.attempts
            if not isinstance(result.value, output):
                raise ValueError("Unexpected provider result contract")
            if kind == "analyzer":
                payload = result.value.model_dump()
                if not payload["questions"]:
                    resolved = {r["issue_id"] for r in payload["resolutions"]}
                    blockers = [i.description for i in state.issues
                                if not i.resolved and i.blocking and i.id not in resolved]
                    blockers += [i["description"] for i in payload["issues"] if i["blocking"]]
                    payload["questions"] = [f"Уточніть, будь ласка: {text}" for text in blockers[:3]]
                    if not payload["questions"]:
                        payload["questions"] = ["Перевірте підсумок вимог на вкладці «Перевірка»."]
                self.session.apply_analysis(payload, state.version)
            else:
                # The controller also checks current version, authorization and invariants.
                if result.value.source_version != state.version:
                    raise ValueError("Generator changed source version")
                self.session.accept_artifacts(result.value.model_dump())
            outcome = "accepted"
            return result
        except ProviderError as error:
            attempts, outcome = error.attempts, error.kind
            raise WorkflowError(error.kind, status=error.status,
                                diagnostic=getattr(error, "diagnostic", None)) from None
        except asyncio.CancelledError:
            outcome = "cancelled"
            raise
        except ValueError as error:
            # Exact allowlist only: never expose raw validation text or model payloads.
            outcome = {
                "Fact evidence must quote an existing user message": "invalid_evidence",
                "Unknown fact update target": "unknown_fact_target",
                "Cannot change fact category or revive a removed fact": "invalid_fact_revision",
                "Issue references unknown facts": "unknown_issue_fact",
                "Duplicate fact update targets": "duplicate_fact_targets",
            }.get(str(error), "validation_error")
            raise WorkflowError(outcome) from None
        finally:
            if prompt is not None and state is not None:
                self._records.append(CallRecord(
                    kind, prompt.name, prompt.sha256, state.version, outcome, attempts,
                    result.elapsed_seconds if result else None, result.usage if result else None,
                    getattr(self.provider, "last_repair_sha256", None),
                ))
            self._busy = False
