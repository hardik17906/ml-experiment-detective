"""One deterministic suite for the retained research core and integrated final application."""
from pathlib import Path
import json
import unittest
from evaluate_v3 import ScenarioResult


def main():
    suite=unittest.defaultTestLoader.discover("tests",pattern="test_*.py")
    result=unittest.TextTestRunner(verbosity=2,resultclass=ScenarioResult).run(suite)
    report={"type":"deterministic scenarios and labeled mocks; no live training", "tests_run":result.testsRun,
            "passed":sum(r["passed"] for r in result.scenarios), "failures":len(result.failures)+len(result.errors),
            "scenarios":result.scenarios}
    Path("reports/final").mkdir(parents=True,exist_ok=True)
    Path("reports/final/deterministic.json").write_text(json.dumps(report,indent=2),encoding="utf-8")
    print(f"FINAL: {report['passed']}/{report['tests_run']} passed")
    raise SystemExit(0 if result.wasSuccessful() else 1)


if __name__=="__main__":
    main()
