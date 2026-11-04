"""Render a quality-gate report as Markdown."""

from __future__ import annotations

from .models import RequirementSet, TestSuite
from .quality_gates import FAIL, PASS, GateReport, MetricResult

VERDICT_LABEL = {
    PASS: "✅ PASS",
    "PASS_WITH_WARNINGS": "⚠️ PASS WITH WARNINGS",
    FAIL: "❌ FAIL",
}


def _status(result: MetricResult) -> str:
    if result.passed:
        return "✅ pass"
    return "❌ fail" if result.blocking else "⚠️ warning"


def _threshold(result: MetricResult) -> str:
    sign = "≥" if result.direction == "min" else "≤"
    return f"{sign} {result.threshold:.0%}"


def render_markdown(report: GateReport, reqs: RequirementSet, suite: TestSuite) -> str:
    lines = [
        f"# Quality Gate Report: {report.application}",
        "",
        f"**Verdict: {VERDICT_LABEL[report.verdict]}**",
        "",
        f"{report.total_test_cases} test cases for {report.total_requirements} requirements.",
        "",
        "## Gates",
        "",
        "| Gate | Value | Threshold | Blocking | Status |",
        "|---|---|---|---|---|",
    ]
    for r in report.results:
        lines.append(
            f"| {r.description} | {r.value:.0%} | {_threshold(r)} | "
            f"{'yes' if r.blocking else 'no'} | {_status(r)} |"
        )

    findings = [(r, f) for r in report.results for f in r.findings]
    lines += ["", "## Findings", ""]
    if findings:
        lines += [f"- **{r.name}**: {f}" for r, f in findings]
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
