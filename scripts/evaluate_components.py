"""Bounded free-only development evaluation; gold is read only after inference."""

import argparse
import asyncio
from dataclasses import asdict
from datetime import datetime, timezone
import hashlib
import json
import os
from pathlib import Path
from time import monotonic

import httpx

from ba_assistant.models import ArtifactBundle, Fact, Message, SessionState
from ba_assistant.openrouter import FreeProviderConfig, OpenRouter, ProviderError
from ba_assistant.session import Session
from ba_assistant.workflow import Workflow, WorkflowError, load_prompt, messages_for
from scripts.check_dataset import DEFAULT_DATA, load_inputs, read_jsonl
from scripts.evaluate_export import evaluate

ROOT = Path(__file__).resolve().parents[1]
REVIEWED = {"DEV-S02", "DEV-S03", "DEV-S06"}


def source_fingerprint():
    paths = [p for p in (ROOT / "ba_assistant").rglob("*") if p.suffix in {".py", ".txt"}]
    paths += [ROOT / name for name in ("scripts/evaluate_components.py", "scripts/evaluate_export.py",
                                      "scripts/check_dataset.py", "pyproject.toml", "uv.lock")]
    return {p.relative_to(ROOT).as_posix(): hashlib.sha256(p.read_bytes()).hexdigest()
            for p in sorted(paths)}


def check_freeze(path):
    frozen = json.loads(path.read_text(encoding="utf-8"))
    if frozen["sources"] != source_fingerprint():
        raise ValueError("Sources changed after freeze; do not tune on held-out inputs")


def api_key():
    """Explicit evaluation-only .env read; never print credentials or source lines."""
    if value := os.environ.get("OPENROUTER_API_KEY", "").strip():
        return value
    path = ROOT / ".env"
    if path.exists():
        for line in path.read_text(encoding="utf-8-sig").splitlines():
            name, separator, value = line.strip().partition("=")
            if separator and name == "OPENROUTER_API_KEY":
                return value.strip().strip('"\'')
    return ""


class ModelTelemetry(httpx.AsyncBaseTransport):
    def __init__(self):
        self.inner = httpx.AsyncHTTPTransport()
        self.model = None

    async def handle_async_request(self, request):
        response = await self.inner.handle_async_request(request)
        await response.aread()
        try:
            model = response.json().get("model")
            self.model = model if isinstance(model, str) and len(model) <= 200 else None
        except (ValueError, AttributeError):
            pass
        return response

    async def aclose(self):
        await self.inner.aclose()


def presence_metrics(predicted, expected):
    tp = len(predicted & expected)
    fp, fn = len(predicted - expected), len(expected - predicted)
    return {"tp": tp, "fp": fp, "fn": fn,
            "precision": tp / (tp + fp) if tp + fp else None,
            "recall": tp / (tp + fn) if tp + fn else None,
            "f1": 2 * tp / (2 * tp + fp + fn) if 2 * tp + fp + fn else None}


def score_analyzers(rows, gold):
    """Category presence only: does not claim semantic fact matching."""
    totals = {"tp": 0, "fp": 0, "fn": 0}
    for row in rows:
        expected = {f["category"] for f in gold[row["id"]]["facts"]}
        predicted = {f["category"] for f in row.get("analysis", {}).get("facts", [])
                     if not f["proposal"]}
        score = presence_metrics(predicted, expected)
        row["category_presence"] = score
        row["expected_conflict"] = any(i["type"] == "conflict" for i in gold[row["id"]]["issues"])
        row["predicted_conflict"] = any(i["kind"] == "conflict" for i in row.get("analysis", {}).get("issues", []))
        row["gold_question_topics"] = gold[row["id"]]["question_topics"]
        for key in totals:
            totals[key] += score[key]
    tp, fp, fn = (totals[k] for k in ("tp", "fp", "fn"))
    return {**totals, "precision": tp / (tp + fp) if tp + fp else None,
            "recall": tp / (tp + fn) if tp + fn else None,
            "f1": 2 * tp / (2 * tp + fp + fn) if 2 * tp + fp + fn else None,
            "note": "Micro category-presence only; failed calls count as empty predictions. "
                    "Not semantic fact precision/recall. Question relevance needs human review."}


async def analyzer_case(record, key):
    transport = ModelTelemetry()
    provider = OpenRouter(FreeProviderConfig(api_key=key), transport=transport)
    state = SessionState(version=1, pending_analysis=True, messages=[
        Message(id=m["id"], role=m["role"], text=m["content"]) for m in record["messages"]])
    session = Session()
    session._state = state
    workflow = Workflow(session, provider)
    row = {"id": record["id"], "input": record["messages"]}
    started = monotonic()
    try:
        await workflow.analyze_pending()
        result = session.state
        # Preserve model-produced content and controller outcomes separately.
        row["analysis"] = {
            "facts": [{"category": f.category, "text": f.text, "proposal": f.status == "proposed",
                       "evidence": [e.model_dump() for e in f.evidence]} for f in result.facts],
            "issues": [i.model_dump() for i in result.issues],
            "questions": [m.text for m in result.messages[len(state.messages):]],
        }
        row["automatic_confirmations"] = sum(f.status == "confirmed" for f in result.facts)
        row["outcome"] = "success"
    except WorkflowError as error:
        row.update(outcome=str(error), status=error.status, diagnostic=error.diagnostic)
    row.update(elapsed_seconds=round(monotonic() - started, 3), selected_model=transport.model,
               calls=[asdict(item) for item in workflow.records])
    return row


async def generator_case(data, key):
    transport = ModelTelemetry()
    provider = OpenRouter(FreeProviderConfig(api_key=key), transport=transport)
    # Supplied export is the input fixture, not a reconstructed human-review history.
    if data["proposals"] or data["open_questions"] or data.get("demonstration"):
        raise ValueError("Generator fixture must be a non-demo export without open items")
    state = SessionState(version=data["artifacts"]["source_version"], facts=[
        Fact(**fact, status="confirmed", evidence=[]) for fact in data["confirmed_facts"]])
    prompt = load_prompt("generator")
    row = {"id": "GEN-USER-01", "prompt": prompt.name, "prompt_sha256": prompt.sha256}
    started = monotonic()
    try:
        response = await provider.complete(messages_for("generator", state, prompt), ArtifactBundle)
        candidate = {**data, "artifacts": response.value.model_dump()}
        row["structural"] = evaluate(candidate)
        row["source_version_valid"] = response.value.source_version == state.version
        row["outcome"] = "success" if all(row["structural"]["checks"].values()) and row["source_version_valid"] else "invalid_artifacts"
        row["artifacts"] = response.value.model_dump()
        row["usage"] = response.usage
        row["attempts"] = response.attempts
    except ProviderError as error:
        row.update(outcome=error.kind, status=error.status, diagnostic=error.diagnostic, attempts=error.attempts)
    row.update(elapsed_seconds=round(monotonic() - started, 3), selected_model=transport.model)
    return row


async def run(args, key):
    if args.split == "test":
        if not args.freeze_manifest:
            raise ValueError("Held-out evaluation requires --freeze-manifest")
        check_freeze(args.freeze_manifest)
    records = [r for r in load_inputs(DEFAULT_DATA, args.split)
               if args.split == "test" or r["id"] in REVIEWED]
    fixture_raw = args.generator_export.read_bytes() if args.generator_export else None
    fixture = json.loads(fixture_raw.decode("utf-8-sig")) if fixture_raw else None
    if fixture:
        if not all(evaluate(fixture)["checks"].values()):
            raise ValueError("Invalid generator input export")
    run_id = datetime.now(timezone.utc).strftime("%Y%m%dT%H%M%SZ")
    directory = ROOT / "evals/runs/private" / run_id
    directory.mkdir(parents=True, exist_ok=False)
    result = {"run_id": run_id, "route": "openrouter/free", "split": args.split,
              "dataset": "v0.1", "repeats": 1, "analyzers": [], "generator": None,
              "max_calls": len(records) + bool(fixture), "max_tokens": 4096,
              "sources": source_fingerprint(),
              "input_sha256": hashlib.sha256((DEFAULT_DATA / f"{args.split}.inputs.jsonl").read_bytes()).hexdigest(),
              "generator_input_sha256": hashlib.sha256(fixture_raw).hexdigest() if fixture_raw else None}
    path = directory / "results.json"

    def save():
        path.write_text(json.dumps(result, ensure_ascii=False, indent=2), encoding="utf-8")

    save()
    for record in records:
        row = await analyzer_case(record, key)
        result["analyzers"].append(row)
        save()
        print(f"{row['id']}: {row['outcome']} ({row['elapsed_seconds']}s)", flush=True)
    if fixture:
        result["generator"] = await generator_case(fixture, key)
        save()
        print(f"GEN-USER-01: {result['generator']['outcome']}", flush=True)
    # Gold is never passed into analyzer_case or generator_case.
    gold = {r["id"]: r for r in read_jsonl(DEFAULT_DATA / f"{args.split}.gold.jsonl")}
    result["category_presence"] = score_analyzers(result["analyzers"], gold)
    save()
    print(f"Private results: {path}", flush=True)
    return 0


def main():
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--generator-export", type=Path)
    parser.add_argument("--split", choices=["dev", "test"], default="dev")
    parser.add_argument("--freeze-manifest", type=Path)
    parser.add_argument("--write-freeze", type=Path)
    args = parser.parse_args()
    if args.write_freeze:
        with args.write_freeze.open("x", encoding="utf-8") as output:
            json.dump({"frozen_at": datetime.now(timezone.utc).isoformat(),
                       "sources": source_fingerprint()}, output, indent=2)
        print("Frozen source hashes recorded; no API call.")
        return 0
    key = api_key()
    if not key:
        print("NOT RUN: configure OPENROUTER_API_KEY in environment or local ignored .env.")
        return 2
    return asyncio.run(run(args, key))


if __name__ == "__main__":
    raise SystemExit(main())
