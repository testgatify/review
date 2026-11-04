"""Render a review report as Markdown."""

from __future__ import annotations

from .models import RequirementSet, TestSuite
from .review_checks import ACCEPT, MAJOR, MAJOR_REWORK, MINOR_REWORK, CheckResult, ReviewReport

VERDICT_LABEL = {
    ACCEPT: "✅ ACCEPT",
    MINOR_REWORK: "🛠️ MINOR REWORK",
    MAJOR_REWORK: "⛔ MAJOR REWORK",
}

VERDICT_MEANING = {
    ACCEPT: "The test cases can be used as they are.",
    MINOR_REWORK: "The test cases can be used after the minor findings below are addressed.",
    MAJOR_REWORK: "Do not use these test cases yet: fix the major findings below and review again.",
}


def _result(result: CheckResult) -> str:
    if result.passed:
        return "✅ ok"
    return "⛔ major finding" if result.severity == MAJOR else "🛠️ minor finding"


def _threshold(result: CheckResult) -> str:
    sign = "≥" if result.direction == "min" else "≤"
    return f"{sign} {result.threshold:.0%}"


def render_markdown(report: ReviewReport, reqs: RequirementSet, suite: TestSuite) -> str:
    lines = [
        f"# Test Design Review: {report.application}",
        "",
        f"**Verdict: {VERDICT_LABEL[report.verdict]}**: {VERDICT_MEANING[report.verdict]}",
        "",
        f"{report.total_test_cases} test cases for {report.total_requirements} requirements. "
        "This is a static review of the test design; no tests were executed against the application.",
        "",
        "## Review checks",
        "",
        "| Check | Value | Threshold | Severity | Result |",
        "|---|---|---|---|---|",
    ]
    for r in report.results:
        lines.append(
            f"| {r.description} | {r.value:.0%} | {_threshold(r)} | {r.severity} | {_result(r)} |"
        )

    findings = [(r, f) for r in report.results for f in r.findings]
    lines += ["", "## Findings", ""]
    if findings:
        lines += [f"- **{r.severity}** ({r.name}): {f}" for r, f in findings]
    else:
        lines.append("No findings.")

    lines += [
        "",
        "## Traceability matrix",
        "",
        "| Requirement | Priority | Test cases |",
        "|---|---|---|",
    ]
    for req in reqs.requirements:
        linked = [tc.id for tc in suite.test_cases if req.id in tc.requirement_ids]
        lines.append(
            f"| {req.id}: {req.title} | {req.priority.value} | "
            f"{', '.join(linked) if linked else '**none**'} |"
        )

    lines += [
        "",
        "## Test cases",
        "",
        "| ID | Title | Requirements | Type | Priority | Steps |",
        "|---|---|---|---|---|---|",
    ]
    for tc in suite.test_cases:
        lines.append(
            f"| {tc.id} | {tc.title} | {', '.join(tc.requirement_ids)} | "
            f"{tc.type.value} | {tc.priority.value} | {len(tc.steps)} |"
        )
    return "\n".join(lines) + "\n"
