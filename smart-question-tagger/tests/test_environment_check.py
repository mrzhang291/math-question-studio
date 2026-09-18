import importlib.util
import json
import sys
import tempfile
import unittest
from pathlib import Path


SCRIPT = Path(__file__).resolve().parents[1] / "scripts" / "check_environment.py"
SPEC = importlib.util.spec_from_file_location("check_environment", SCRIPT)
assert SPEC and SPEC.loader
MODULE = importlib.util.module_from_spec(SPEC)
sys.modules[SPEC.name] = MODULE
SPEC.loader.exec_module(MODULE)


class EnvironmentCheckTests(unittest.TestCase):
    def test_bank_check_reports_question_count_and_missing_recommended_artifacts(self) -> None:
        with tempfile.TemporaryDirectory() as directory:
            bank = Path(directory)
            (bank / "tags").mkdir()
            (bank / "review").mkdir()
            (bank / "tags" / "all_question_tags.json").write_text(json.dumps([{"question_id": "q1"}]), encoding="utf-8")
            (bank / "review" / "index.html").write_text("<html></html>", encoding="utf-8")

            result = MODULE.check_bank(bank)

            self.assertEqual(result["status"], "warn")
            self.assertEqual(result["question_count"], 1)
            self.assertIn("manifest.json", result["missing_recommended"])


if __name__ == "__main__":
    unittest.main()
