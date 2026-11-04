"""Export a test suite for people (Excel) and for Jira Xray (CSV import)."""

from __future__ import annotations

import csv
from pathlib import Path

from openpyxl import Workbook
from openpyxl.styles import Alignment, Font, PatternFill

from .models import TestSuite

EXCEL_HEADERS = [
    "Test ID", "Title", "Requirements", "Type", "Priority",
    "Preconditions", "Step", "Action", "Expected Result",
]
EXCEL_WIDTHS = [10, 40, 28, 11, 10, 34, 6, 50, 50]

# One row per step. Test-level fields are filled on the first row of each
# test; the following rows with the same TCID add steps. Column names are
# mapped to Xray fields in Xray's Test Case Importer.
XRAY_HEADERS = [
    "TCID", "Summary", "Priority", "Labels", "Test Category",
    "Requirements", "Precondition", "Action", "Data", "Expected Result",
]

_PRIORITY = {"high": "High", "medium": "Medium", "low": "Low"}


def _path(path: str | Path) -> Path:
    out = Path(path)
    out.parent.mkdir(parents=True, exist_ok=True)
    return out


def to_excel(suite: TestSuite, path: str | Path) -> Path:
    wb = Workbook()
    ws = wb.active
    ws.title = "Test cases"
    ws.append(EXCEL_HEADERS)
    for cell in ws[1]:
        cell.font = Font(bold=True, color="FFFFFF")
        cell.fill = PatternFill("solid", fgColor="1F3864")
        cell.alignment = Alignment(vertical="center", wrap_text=True)

    band = PatternFill("solid", fgColor="EEF2F9")
    for index, tc in enumerate(suite.test_cases):
        for number, step in enumerate(tc.steps, start=1):
            first = number == 1
            ws.append([
                tc.id if first else "",
                tc.title if first else "",
                ", ".join(tc.requirement_ids) if first else "",
                tc.type.value if first else "",
                tc.priority.value if first else "",
                "\n".join(tc.preconditions) if first else "",
                number,
                step.action,
                step.expected,
            ])
            row = ws.max_row
            for cell in ws[row]:
                cell.alignment = Alignment(vertical="top", wrap_text=True)
                if index % 2:
                    cell.fill = band
            if first:
                ws.cell(row=row, column=1).font = Font(bold=True)

    for column, width in enumerate(EXCEL_WIDTHS, start=1):
        ws.column_dimensions[ws.cell(row=1, column=column).column_letter].width = width
    ws.freeze_panes = "A2"
    ws.auto_filter.ref = ws.dimensions

    out = _path(path)
    wb.save(out)
    return out


def to_xray_csv(suite: TestSuite, path: str | Path) -> Path:
    out = _path(path)
    with out.open("w", newline="", encoding="utf-8") as handle:
        writer = csv.writer(handle)
        writer.writerow(XRAY_HEADERS)
        for tc in suite.test_cases:
            for number, step in enumerate(tc.steps, start=1):
                first = number == 1
                writer.writerow([
                    tc.id,
                    tc.title if first else "",
                    _PRIORITY[tc.priority.value] if first else "",
                    "ai-generated" if first else "",
                    tc.type.value if first else "",
                    " ".join(tc.requirement_ids) if first else "",
                    "; ".join(tc.preconditions) if first else "",
                    step.action,
                    "",
                    step.expected,
                ])
    return out
