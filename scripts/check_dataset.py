"""Validate draft corpus structure and provenance; never score NLP quality."""

import argparse
import hashlib
import json
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
DEFAULT_DATA = ROOT / "evals/data/v0.1"
CATEGORIES = {"goals", "users", "requirements", "constraints", "team_roles"}
SPLITS = ("dev", "test")
FILES = {f"{split}.{part}.jsonl" for split in SPLITS for part in ("inputs", "gold")}


def read_jsonl(path):
    return [json.loads(line) for line in path.read_text(encoding="utf-8").splitlines()]


def load_inputs(directory, split):
    """Read only runtime messages, without opening gold or the manifest."""
    if split not in SPLITS:
        raise ValueError("Unknown split")
    records = read_jsonl(Path(directory) / f"{split}.inputs.jsonl")
    for record in records:
        if set(record) != {"id", "messages"}:
            raise ValueError("Unexpected input fields; gold must stay outside inputs")
        if not isinstance(record["id"], str) or not record["id"]:
            raise ValueError("Missing input ID")
        messages = record["messages"]
        if not isinstance(messages, list) or not messages:
            raise ValueError("Empty messages")
        ids = set()
        for message in messages:
            if set(message) != {"id", "role", "content"}:
                raise ValueError("Unexpected message fields")
            if not isinstance(message["id"], str) or not message["id"] or message["id"] in ids:
                raise ValueError("Invalid or duplicate message ID")
            ids.add(message["id"])
            if message["role"] not in {"user", "assistant"}:
                raise ValueError("Source system/tool messages are not allowed")
            if not isinstance(message["content"], str) or not message["content"].strip():
                raise ValueError("Empty message content")
        if messages[-1]["role"] != "user":
            raise ValueError("Analyzer snapshot must end with a user message")
    return records


def check_dataset(directory=DEFAULT_DATA):
    directory = Path(directory)
    manifest = json.loads((directory / "manifest.json").read_text(encoding="utf-8"))
    errors = []
    seen_ids, families, fingerprints = set(), {}, {}
    counts, pending = {}, 0

    def require(condition, message):
        if not condition:
            errors.append(message)

    require(manifest["version"] == "0.1", "Unsupported version")
    require(set(manifest["files"]) == FILES, "Manifest file inventory mismatch")
    for filename in FILES:
        digest = hashlib.sha256((directory / filename).read_bytes()).hexdigest()
        require(manifest["files"].get(filename) == digest, f"Hash mismatch: {filename}")
    for split in SPLITS:
        inputs = load_inputs(directory, split)
        gold = read_jsonl(directory / f"{split}.gold.jsonl")
        require([r["id"] for r in inputs] == [r["id"] for r in gold], f"Input/gold ID mismatch: {split}")
        counts[split] = len(inputs)
        require(len(inputs) == manifest["splits"][split]["count"], f"Count mismatch: {split}")
        actual_families = set()
        for record, annotation in zip(inputs, gold):
            cid = record["id"]
            require(cid not in seen_ids, f"Duplicate scenario ID: {cid}")
            seen_ids.add(cid)
            require(annotation["split"] == split, f"Wrong split: {cid}")
            require(annotation["annotation_version"] == manifest["version"], f"Wrong annotation version: {cid}")
            require(annotation["language"] in {"uk", "en"}, f"Unknown language: {cid}")
            family = annotation["family"]
            actual_families.add(family)
            require(families.get(family, split) == split, f"Family leakage: {family}")
            families[family] = split
            content = json.dumps([(m["role"], m["content"]) for m in record["messages"]], ensure_ascii=False)
            fingerprint = hashlib.sha256(content.encode()).hexdigest()
            require(fingerprints.get(fingerprint, split) == split, f"Duplicate snapshot across splits: {cid}")
            fingerprints[fingerprint] = split
            review = annotation["review"]
            require(review["status"] in {"pending", "approved", "changes_requested"}, f"Invalid review status: {cid}")
            if review["status"] == "pending":
                pending += 1
                require(review["reviewer"] is None, f"Pending review has a reviewer: {cid}")
            else:
                require(isinstance(review["reviewer"], str) and bool(review["reviewer"].strip()), f"Missing reviewer: {cid}")
            provenance = annotation["provenance"]
            require(provenance["kind"] in {"synthetic", "adapted_public"}, f"Invalid provenance: {cid}")
            require(bool(provenance["source"]), f"Missing source: {cid}")
            if provenance["kind"] == "adapted_public":
                for key in ("license", "creators", "archive_sha256", "record_id", "transformation"):
                    require(bool(provenance.get(key)), f"Missing {key}: {cid}")
                require(split == "dev", f"Inspected external family must stay in dev: {cid}")
            messages = {m["id"]: m for m in record["messages"]}
            present = set()
            for fact in annotation["facts"]:
                present.add(fact["category"])
                require(fact["category"] in CATEGORIES, f"Unknown category: {cid}")
                require(fact["status"] == "unreviewed", f"No review event supports confirmation: {cid}")
                require(bool(fact["text"].strip()) and bool(fact["evidence"]), f"Empty fact/evidence: {cid}")
                for evidence in fact["evidence"]:
                    message = messages.get(evidence["message_id"])
                    require(message is not None, f"Unknown evidence message: {cid}")
                    if message is None:
                        continue
                    start, end = evidence["start"], evidence["end"]
                    require(type(start) is int and type(end) is int and 0 <= start < end <= len(message["content"]), f"Invalid evidence offsets: {cid}")
                    require(message["content"][start:end] == evidence["quote"], f"Evidence quote mismatch: {cid}")
                    require(message["role"] == "user", f"Assistant text cannot establish user fact: {cid}")
            require(set(annotation["missing_categories"]) == CATEGORIES - present, f"Missing-category mismatch: {cid}")
            require(set(annotation["question_topics"]) <= CATEGORIES | {"resolve_conflict"}, f"Unknown question topic: {cid}")
            require({"no_automatic_confirmation", "no_final_artifacts_before_review"} <= set(annotation["invariants"]), f"Missing safety invariants: {cid}")
            for issue in annotation["issues"]:
                require(issue["type"] in {"gap", "conflict"} and type(issue["blocking"]) is bool, f"Invalid issue: {cid}")
                require(bool(issue["message_ids"]) and set(issue["message_ids"]) <= set(messages), f"Issue evidence missing: {cid}")
            require(annotation["finalization_allowed"] is False, f"Snapshot lacks user review for finalization: {cid}")
            require(set(annotation["requirement_ids"]) <= {"BA-01", "BA-02", "BA-03", "BA-07"}, f"Unsupported coverage claim: {cid}")
        require(actual_families == set(manifest["splits"][split]["families"]), f"Family manifest mismatch: {split}")
    if errors:
        raise ValueError("\n".join(errors))
    return counts, pending


def main():
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--data-dir", type=Path, default=DEFAULT_DATA)
    args = parser.parse_args()
    try:
        counts, pending = check_dataset(args.data_dir)
    except (OSError, ValueError, KeyError, TypeError) as error:
        print(f"FAIL: {error}")
        return 1
    print(f"PASS: dataset structure, hashes, evidence spans, split isolation; counts={counts}")
    print(f"PENDING HUMAN REVIEW: {pending} annotations")
    print("NOT TESTED: semantic annotation correctness, application behavior, NLP quality")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
