from __future__ import annotations

import csv

from openpyxl import load_workbook

from ai_test_dragon.export import EXCEL_HEADERS, XRAY_HEADERS, to_excel, to_xray_csv
from ai_test_dragon.loader import load_suite


def seeded(root):
    return load_suite(root / "examples" / "seeded_suite_with_defects.json")


def test_excel_has_one_row_per_step(root, tmp_path):
    suite = seeded(root)
    ws = load_workbook(to_excel(suite, tmp_path / "cases.xlsx")).active
    rows = list(ws.iter_rows(values_only=True))
    assert list(rows[0]) == EXCEL_HEADERS
    assert len(rows) - 1 == sum(len(tc.steps) for tc in suite.test_cases)


def test_excel_fills_test_fields_on_first_step_only(root, tmp_path):
    suite = seeded(root)
    ws = load_workbook(to_excel(suite, tmp_path / "cases.xlsx")).active
    first, second = ws[2], ws[3]  # TC-001 has two steps
    assert first[0].value == "TC-001" and first[1].value == suite.test_cases[0].title
    assert second[0].value is None and second[6].value == 2
    assert second[8].value == suite.test_cases[0].steps[1].expected


def test_xray_csv_groups_steps_by_tcid(root, tmp_path):
    suite = seeded(root)
    path = to_xray_csv(suite, tmp_path / "xray.csv")
    with path.open(encoding="utf-8", newline="") as handle:
        rows = list(csv.DictReader(handle))
    assert list(rows[0].keys()) == XRAY_HEADERS
    assert len(rows) == sum(len(tc.steps) for tc in suite.test_cases)
    tc015 = [r for r in rows if r["TCID"] == "TC-015"]
    assert len(tc015) == 3
    assert tc015[0]["Summary"] == "Checkout information fields are required"
    assert tc015[0]["Priority"] == "High"
    assert tc015[0]["Labels"] == "ai-generated"
    assert tc015[1]["Summary"] == ""
    assert "Error: Last Name is required" in tc015[1]["Expected Result"]


def test_xray_csv_keeps_turkish_and_quotes(root, tmp_path):
    suite = seeded(root)
    suite.test_cases[0].title = 'Giriş "doğru" bilgilerle'
    path = to_xray_csv(suite, tmp_path / "xray.csv")
    with path.open(encoding="utf-8", newline="") as handle:
        rows = list(csv.DictReader(handle))
    assert rows[0]["Summary"] == 'Giriş "doğru" bilgilerle'
