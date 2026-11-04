from __future__ import annotations

import pytest

from testgatify_review.cli import main
from testgatify_review.models import RequirementSet


def test_review_exits_1_on_major_rework_and_writes_report(root, tmp_path):
    report = tmp_path / "review.md"
    code = main(
        [
            "review",
            "--requirements", str(root / "requirements" / "saucedemo.yaml"),
            "--suite", str(root / "examples" / "seeded_suite_with_defects.json"),
            "--config", str(root / "config" / "review_checks.yaml"),
            "--report", str(report),
        ]
    )
    assert code == 1
    text = report.read_text(encoding="utf-8")
    assert "Verdict: ⛔ MAJOR REWORK" in text
    assert "no tests were executed" in text
    assert "| REQ-NAV-01: Logout and protected pages | medium | **none** |" in text


def test_export_command_writes_both_files(root, tmp_path):
    xlsx, csv_file = tmp_path / "cases.xlsx", tmp_path / "xray.csv"
    code = main(
        [
            "export",
            "--suite", str(root / "examples" / "seeded_suite_with_defects.json"),
            "--xlsx", str(xlsx),
            "--csv", str(csv_file),
        ]
    )
    assert code == 0
    assert xlsx.exists() and csv_file.exists()


def test_duplicate_requirement_ids_are_rejected():
    req = {"id": "REQ-1", "title": "t", "description": "d", "priority": "high"}
    with pytest.raises(ValueError, match="Duplicate requirement id"):
        RequirementSet.model_validate({"application": "x", "requirements": [req, req]})
