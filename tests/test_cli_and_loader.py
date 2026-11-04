from __future__ import annotations

import pytest

from ai_test_designer.cli import main
from ai_test_designer.models import RequirementSet


def test_evaluate_exits_1_on_fail_and_writes_report(root, tmp_path):
    report = tmp_path / "report.md"
    code = main(
        [
            "evaluate",
            "--requirements", str(root / "requirements" / "saucedemo.yaml"),
            "--suite", str(root / "examples" / "seeded_suite_with_defects.json"),
            "--config", str(root / "config" / "quality_gates.yaml"),
            "--report", str(report),
        ]
    )
    assert code == 1
    text = report.read_text(encoding="utf-8")
    assert "Verdict: ❌ FAIL" in text
    assert "| REQ-NAV-01: Logout and protected pages | medium | **none** |" in text


def test_duplicate_requirement_ids_are_rejected():
    req = {"id": "REQ-1", "title": "t", "description": "d", "priority": "high"}
    with pytest.raises(ValueError, match="Duplicate requirement id"):
        RequirementSet.model_validate({"application": "x", "requirements": [req, req]})
