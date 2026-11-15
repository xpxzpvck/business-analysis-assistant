"""Negative checks guard against broken evidence and evaluation leakage."""

import hashlib
import json
import shutil
import tempfile
import unittest
from pathlib import Path

from scripts.check_dataset import DEFAULT_DATA, ROOT, check_dataset, load_inputs


class DatasetChecks(unittest.TestCase):
    def setUp(self):
        (ROOT / "tmp").mkdir(exist_ok=True)
        self.temp = tempfile.TemporaryDirectory(dir=ROOT / "tmp")
        self.addCleanup(self.temp.cleanup)
        self.data = Path(self.temp.name) / "data"
        shutil.copytree(DEFAULT_DATA, self.data)

    def change(self, filename, mutate):
        path = self.data / filename
        records = [json.loads(line) for line in path.read_text(encoding="utf-8").splitlines()]
        mutate(records)
        path.write_text("".join(json.dumps(row, ensure_ascii=False) + "\n" for row in records), encoding="utf-8")
        manifest_path = self.data / "manifest.json"
        manifest = json.loads(manifest_path.read_text(encoding="utf-8"))
        manifest["files"][filename] = hashlib.sha256(path.read_bytes()).hexdigest()
        manifest_path.write_text(json.dumps(manifest), encoding="utf-8")

    def test_current_draft_is_valid_and_partially_reviewed(self):
        self.assertEqual(check_dataset(self.data), ({"dev": 8, "test": 4}, 9))

    def test_bad_evidence_is_rejected(self):
        self.change("dev.gold.jsonl", lambda rows: rows[0]["facts"][0]["evidence"][0].update(quote="invented"))
        with self.assertRaisesRegex(ValueError, "Evidence quote mismatch"):
            check_dataset(self.data)

    def test_cross_split_family_is_rejected(self):
        self.change("test.gold.jsonl", lambda rows: rows[0].update(family="request-tracker"))
        with self.assertRaisesRegex(ValueError, "Family leakage"):
            check_dataset(self.data)

    def test_gold_in_input_is_rejected(self):
        self.change("dev.inputs.jsonl", lambda rows: rows[0].update(gold_facts=[]))
        with self.assertRaisesRegex(ValueError, "gold must stay outside"):
            check_dataset(self.data)

    def test_source_system_message_is_rejected(self):
        self.change("dev.inputs.jsonl", lambda rows: rows[0]["messages"][0].update(role="system"))
        with self.assertRaisesRegex(ValueError, "system/tool"):
            check_dataset(self.data)

    def test_stale_hash_is_rejected(self):
        path = self.data / "dev.inputs.jsonl"
        path.write_text(path.read_text(encoding="utf-8").replace("clients", "customers"), encoding="utf-8")
        with self.assertRaisesRegex(ValueError, "Hash mismatch"):
            check_dataset(self.data)

    def test_input_loader_does_not_need_gold_files(self):
        for path in self.data.glob("*.gold.jsonl"):
            path.unlink()
        (self.data / "manifest.json").unlink()
        self.assertEqual(len(load_inputs(self.data, "dev")), 8)


if __name__ == "__main__":
    unittest.main()
