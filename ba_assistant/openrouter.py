"""Non-streaming typed OpenRouter transport; independent of session state."""

import asyncio
import math
import os
import hashlib
import json
from pathlib import Path
from dataclasses import dataclass
from datetime import datetime, timezone
from email.utils import parsedate_to_datetime
from time import monotonic
from typing import Literal, TypeVar

import httpx
from pydantic import BaseModel, ConfigDict, Field, SecretStr, ValidationError, field_validator

from .models import ArtifactBundle

T = TypeVar("T", bound=BaseModel)
URL = "https://openrouter.ai/api/v1/chat/completions"
FREE_MODEL = "openrouter/free"


class ProviderConfig(BaseModel):
    model_config = ConfigDict(extra="forbid", frozen=True)
    api_key: SecretStr
    model: str = Field(min_length=1)
    attempt_timeout: float = Field(default=60, gt=0, le=60, allow_inf_nan=False)
    generation_timeout: float = Field(default=180, gt=0, le=180, allow_inf_nan=False)
    max_attempts: int = Field(default=2, ge=1, le=2, strict=True)
    max_tokens: int = Field(default=4096, gt=0, strict=True)

    @field_validator("api_key")
    @classmethod
    def nonempty_key(cls, value):
        if not value.get_secret_value().strip():
            raise ValueError("API key is required")
        return value

    @field_validator("model")
    @classmethod
    def explicit_model(cls, value):
        if value != value.strip() or "/" not in value or value == "openrouter/auto":
            raise ValueError("An explicit provider/model ID is required")
        return value

    @classmethod
    def from_env(cls):
        # Deliberate environment read; no .env loading or network activity on import.
        return cls(api_key=os.environ.get("OPENROUTER_API_KEY", ""), model=os.environ.get("OPENROUTER_MODEL", ""))


class ProviderError(Exception):
    """Safe error text: never include provider bodies, credentials or prompts."""

    def __init__(self, kind, attempts, status=None, diagnostic=None):
        self.kind, self.attempts, self.status = kind, attempts, status
        self.diagnostic = diagnostic
        super().__init__(f"OpenRouter {kind}; attempts={attempts}; status={status}")


class FreeProviderConfig(ProviderConfig):
    """Approved application configuration; paid models cannot be substituted."""

    model: Literal["openrouter/free"] = FREE_MODEL
    max_attempts: int = Field(default=1, ge=1, le=2, strict=True)

    @classmethod
    def from_env(cls):
        return cls(api_key=os.environ.get("OPENROUTER_API_KEY", ""),
                   model=os.environ.get("OPENROUTER_MODEL") or FREE_MODEL)


@dataclass(frozen=True)
class Completion:
    value: BaseModel
    attempts: int
    elapsed_seconds: float
    usage: dict[str, int | float] | None
    # Only final-success usage is available; failed attempts may also incur charges.


def strict_schema(model: type[BaseModel]) -> dict:
    schema = model.model_json_schema()

    def visit(node):
        if isinstance(node, dict):
            node.pop("default", None)
            if node.get("type") == "object":
                node["additionalProperties"] = False
                node["required"] = list(node.get("properties", {}))
            for value in node.values():
                visit(value)
        elif isinstance(node, list):
            for value in node:
                visit(value)

    visit(schema)
    return schema


def retry_delay(header: str | None) -> float | None:
    """Return bounded delay; None means stop rather than retry earlier than requested."""
    if header is None:
        return 1.0
    try:
        delay = float(header)
    except ValueError:
        try:
            date = parsedate_to_datetime(header)
            if date.tzinfo is None:
                date = date.replace(tzinfo=timezone.utc)
            delay = (date - datetime.now(timezone.utc)).total_seconds()
        except (ValueError, TypeError, OverflowError):
            return 1.0
    if not math.isfinite(delay) or delay > 5:
        return None
    return max(0.0, delay)


def safe_usage(body):
    usage = body.get("usage")
    if not isinstance(usage, dict):
        return None
    return {key: value for key, value in usage.items()
            if key in {"prompt_tokens", "completion_tokens", "total_tokens", "cost"}
            and type(value) in {int, float} and math.isfinite(value) and value >= 0}


def schema_diagnostic(error, output):
    """Only contract field names and Pydantic error codes; never input or messages."""
    names = set()

    def collect(node):
        if isinstance(node, dict):
            names.update(node.get("properties", {}))
            for value in node.values():
                collect(value)
        elif isinstance(node, list):
            for value in node:
                collect(value)

    collect(output.model_json_schema())
    rows = []
    for item in error.errors(include_input=False, include_context=False, include_url=False)[:3]:
        path = ".".join(str(part) if type(part) is int else part if part in names else "?"
                        for part in item["loc"])
        code = item["type"]
        # Library codes are constrained as well; custom validators must not leak messages.
        code = code if code in {"missing", "extra_forbidden", "string_type", "list_type",
                               "literal_error", "too_long", "too_short", "int_type",
                               "bool_type", "model_type", "string_too_short"} else "invalid_value"
        rows.append(f"{path or 'response'}: {code}")
    return "; ".join(rows)


class OpenRouter:
    def __init__(self, config: ProviderConfig, *, transport=None, sleep=asyncio.sleep):
        self.config, self.transport, self.sleep = config, transport, sleep
        self._schema_failure = None
        self.schema_repair_requested = False
        self.last_repair_sha256 = None

    async def complete(self, messages: list[dict], output: type[T]) -> Completion:
        if not messages or any(set(m) != {"role", "content"} or m["role"] not in {"system", "user", "assistant"}
                               or not isinstance(m["content"], str) or not m["content"].strip() for m in messages):
            raise ValueError("Expected nonempty role/content messages only")
        fingerprint = hashlib.sha256(json.dumps(
            [messages, strict_schema(output)], ensure_ascii=False, sort_keys=True,
        ).encode()).hexdigest()
        cached = self._schema_failure
        self._schema_failure = None
        self.last_repair_sha256 = None
        repair = self.schema_repair_requested or (cached is not None and cached[0] == fingerprint)
        self.schema_repair_requested = False
        request_messages = list(messages)
        if repair:
            raw = Path(__file__).with_name("prompts").joinpath("schema_repair_v1.txt").read_bytes()
            self.last_repair_sha256 = hashlib.sha256(raw).hexdigest()
            request_messages.append({"role": "system", "content": raw.decode("utf-8")})
            if cached is not None and cached[0] == fingerprint:
                request_messages.append({"role": "user", "content": json.dumps({
                    "schema_repair_data": {"previous_output": cached[1], "validation": cached[2]},
                }, ensure_ascii=False)})
        payload = dict(
            model=self.config.model, messages=request_messages, stream=False,
            max_tokens=self.config.max_tokens,
            provider={"require_parameters": True, "allow_fallbacks": False},
            response_format={"type": "json_schema", "json_schema": {
                "name": output.__name__, "strict": True, "schema": strict_schema(output),
            }},
        )
        if self.config.model == FREE_MODEL:
            payload["provider"]["max_price"] = {"prompt": 0, "completion": 0, "request": 0}
            payload["reasoning"] = {"enabled": False}
        headers = {"Authorization": f"Bearer {self.config.api_key.get_secret_value()}"}
        started = monotonic()
        generating = output is ArtifactBundle
        timeout = self.config.generation_timeout if generating else self.config.attempt_timeout
        async with httpx.AsyncClient(transport=self.transport, follow_redirects=False, trust_env=False,
                                     timeout=timeout) as client:
            for attempt in range(1, self.config.max_attempts + 1):
                status, delay, retry = None, 1.0, False
                try:
                    response = await asyncio.wait_for(
                        client.post(URL, headers=headers, json=payload), timeout,
                    )
                except (TimeoutError, httpx.TimeoutException):
                    kind, retry = "generation_timeout" if generating else "timeout", True
                except (httpx.NetworkError, httpx.RemoteProtocolError):
                    kind, retry = "network_error", True
                except httpx.RequestError:
                    kind = "request_error"
                else:
                    status = response.status_code
                    if status != 200:
                        kind = "http_error"
                        retry = status == 429 or 500 <= status <= 599
                        delay = retry_delay(response.headers.get("Retry-After"))
                    else:
                        try:
                            body = response.json()
                        except (ValueError, UnicodeError):
                            raise ProviderError("invalid_json", attempt, status) from None
                        if not isinstance(body, dict):
                            raise ProviderError("invalid_envelope", attempt, status)
                        if "error" in body:
                            error = body["error"]
                            code = error.get("code") if isinstance(error, dict) else None
                            status = code if type(code) is int else 200
                            kind = "provider_error"
                            retry = status == 429 or 500 <= status <= 599
                            delay = retry_delay(response.headers.get("Retry-After"))
                        else:
                            try:
                                choices = body["choices"]
                                if not isinstance(choices, list) or len(choices) != 1:
                                    raise ValueError
                                choice = choices[0]
                                if not isinstance(choice, dict):
                                    raise ValueError
                                if choice.get("finish_reason") == "length":
                                    raise ProviderError("output_truncated", attempt, status)
                                if choice.get("finish_reason") == "content_filter":
                                    raise ProviderError("output_refused", attempt, status)
                                if "error" in choice or choice["finish_reason"] != "stop":
                                    raise ValueError
                                message = choice["message"]
                                if not isinstance(message, dict):
                                    raise ValueError
                                if message.get("refusal"):
                                    raise ProviderError("output_refused", attempt, status)
                                if message.get("tool_calls"):
                                    raise ValueError
                                content = message["content"]
                                if not isinstance(content, str):
                                    raise ValueError
                                if not content.strip():
                                    raise ProviderError("output_empty", attempt, status)
                                # Local validation remains required even with provider strict mode.
                                value = output.model_validate_json(content)
                            except ValidationError as error:
                                if any(item["type"] == "json_invalid" for item in error.errors(include_input=False)):
                                    raise ProviderError("output_not_json", attempt, status) from None
                                diagnostic = schema_diagnostic(error, output)
                                if len(content) <= 64000:
                                    self._schema_failure = (fingerprint, content, diagnostic)
                                raise ProviderError("output_schema", attempt, status, diagnostic) from None
                            except (KeyError, IndexError, TypeError, ValueError):
                                raise ProviderError("invalid_output", attempt, status) from None
                            return Completion(value, attempt, monotonic() - started, safe_usage(body))
                if not retry or attempt == self.config.max_attempts or delay is None:
                    raise ProviderError(kind, attempt, status) from None
                await self.sleep(delay)
        raise AssertionError("Unreachable")
