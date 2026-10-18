import importlib.util
from pathlib import Path
import unittest

SCRIPT = Path(__file__).parents[1] / "scripts" / "verify-stepful-actions-evidence.py"
spec = importlib.util.spec_from_file_location("actions_evidence", SCRIPT)
module = importlib.util.module_from_spec(spec)
assert spec.loader is not None
spec.loader.exec_module(module)

class StepfulEvidenceTests(unittest.TestCase):
    def test_null_steps_is_not_executed(self):
        result = module.classify({"jobs": [{
            "id": 1, "name": "contract", "conclusion": "failure",
            "runner_id": 0, "steps": None,
        }]})
        self.assertEqual(result["classification"], "NOT_EXECUTED")
        self.assertEqual(result["source_verdict"], "NONE")

    def test_empty_steps_is_not_executed(self):
        result = module.classify({"jobs": [{
            "id": 2, "name": "contract", "conclusion": "failure",
            "runner_id": None, "steps": [],
        }]})
        self.assertEqual(result["classification"], "NOT_EXECUTED")

    def test_stepful_job_defers_to_real_job_result(self):
        result = module.classify({"jobs": [{
            "id": 3, "name": "contract", "conclusion": "failure",
            "runner_id": 99,
            "steps": [{"name": "checkout", "conclusion": "success"}],
        }]})
        self.assertEqual(result["classification"], "STEPFUL")
        self.assertEqual(result["source_verdict"], "DEFER_TO_EXECUTED_JOB")

if __name__ == "__main__":
    unittest.main()
