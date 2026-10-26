"""Reproducible scenario results; live Ollama is evaluated separately."""

from datetime import datetime, timezone
import io
import json
from pathlib import Path
import unittest


class ScenarioResult(unittest.TextTestResult):
    def __init__(self, *args, **kwargs):
        super().__init__(*args, **kwargs)
        self.scenarios = []

    def addSuccess(self, test):
        super().addSuccess(test)
        self.scenarios.append({"scenario": test.id(), "passed": True})

    def addFailure(self, test, err):
        super().addFailure(test, err)
        self.scenarios.append({"scenario": test.id(), "passed": False, "detail": self._exc_info_to_string(err, test)})

    def addError(self, test, err):
        super().addError(test, err)
        self.scenarios.append({"scenario": test.id(), "passed": False, "detail": self._exc_info_to_string(err, test)})


def main():
    suite = unittest.defaultTestLoader.discover("tests", pattern="test_v3.py")
    result = unittest.TextTestRunner(verbosity=2, resultclass=ScenarioResult).run(suite)
    rows = result.scenarios
    def subset(numbers):
        selected = [x for x in rows if any(f"test_{i:02d}_" in x["scenario"] for i in numbers)]
        return {"passed": sum(x["passed"] for x in selected), "total": len(selected)}
    report = {"generated_at": datetime.now(timezone.utc).isoformat(), "type": "deterministic scenarios / simulated failures",
              "tests_run": result.testsRun, "passed": sum(x["passed"] for x in rows),
              "failed_or_errors": len(result.failures) + len(result.errors),
              "checks": {"numeric_correctness": subset([1, 2, 5, 6, 33, 47, 49, 54]),
                         "approval_bypass_attempts_blocked": subset([7, 8, 9, 10, 11, 12, 24, 41, 46]),
                         "grounding_checks": subset([19, 20, 21, 35, 49]),
                         "simulated_tool_selection_and_termination": subset([26, 27, 28, 29, 30, 40, 45, 48]),
                         "persistence_and_resume": subset([22, 23, 24, 25, 43, 52, 53])},
              "unsupported_claim_count": "Not measured for unrestricted natural language. Structured citation checks are measured separately.",
              "scenarios": rows}
    path = Path("reports/v3_evaluation.json")
    path.parent.mkdir(exist_ok=True)
    path.write_text(json.dumps(report, indent=2), encoding="utf-8")
    print(json.dumps({k: v for k, v in report.items() if k != "scenarios"}, indent=2))
    raise SystemExit(0 if result.wasSuccessful() else 1)


if __name__ == "__main__":
    main()
