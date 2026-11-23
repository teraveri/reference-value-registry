import json
from pathlib import Path
import shutil
import tempfile
import unittest

from validate import validate_entry


SOURCE = Path(__file__).resolve().parents[1]
ENTRY = Path("entries/azure-snp-vtpm-ima-1/azure-genoa-ubuntu2204-kernel-1071-stage")


class RegistryValidationTests(unittest.TestCase):
    def setUp(self):
        self.temp = tempfile.TemporaryDirectory()
        self.addCleanup(self.temp.cleanup)
        self.root = Path(self.temp.name)
        shutil.copytree(SOURCE / ENTRY, self.root / ENTRY)
        self.manifest = self.root / ENTRY / "manifest.json"

    def update_manifest(self, edit):
        value = json.loads(self.manifest.read_text())
        edit(value)
        self.manifest.write_text(json.dumps(value) + "\n")

    def test_valid_entry(self):
        self.assertEqual(validate_entry(self.root, self.manifest)["reference"]["ima_entries"], 45)

    def test_rejects_changed_reference_bytes(self):
        path = self.root / ENTRY / "reference.json"
        path.write_bytes(path.read_bytes() + b" ")
        with self.assertRaisesRegex(ValueError, "digest mismatch"):
            validate_entry(self.root, self.manifest)

    def test_rejects_path_traversal(self):
        self.update_manifest(lambda m: m["reference"].update(path="../../private.json"))
        with self.assertRaisesRegex(ValueError, "unsafe reference path"):
            validate_entry(self.root, self.manifest)

    def test_rejects_overstated_coverage(self):
        self.update_manifest(lambda m: m["coverage"].append("application"))
        with self.assertRaisesRegex(ValueError, "unsupported coverage"):
            validate_entry(self.root, self.manifest)

    def test_rejects_duplicate_json_keys(self):
        self.manifest.write_bytes(self.manifest.read_bytes().replace(b'"schema_version": 1,', b'"schema_version": 1, "schema_version": 1,'))
        with self.assertRaisesRegex(ValueError, "duplicate JSON key"):
            validate_entry(self.root, self.manifest)


if __name__ == "__main__":
    unittest.main()
