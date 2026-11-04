"""Static review of an AI-written test suite.

Nothing is executed against the application: the checks look at the test
design itself (coverage, traceability, negative tests, completeness,
duplicates), the way a test manager reviews test cases before they are used.

Verdicts follow the outcome of a review meeting:
  ACCEPT        every check is within its threshold
  MINOR_REWORK  only minor checks failed
  MAJOR_REWORK  at least one major check failed
"""

from __future__ import annotations

from dataclasses import dataclass, field
from difflib import SequenceMatcher
from itertools import combinations
from typing import Any, Callable

from .models import Priority, RequirementSet, TestCase, TestSuite, TestType

ACCEPT = "ACCEPT"
MINOR_REWORK = "MINOR_REWORK"
MAJOR_REWORK = "MAJOR_REWORK"

MAJOR = "major"
MINOR = "minor"


@dataclass
class CheckResult:
    name: str
    description: str
    value: float
    threshold: float
    direction: str  # "min" (value must be >= threshold) or "max" (value must be <= threshold)
    severity: str  # "major" or "minor"
    findings: list[str] = field(default_factory=list)

    @property
    def passed(self) -> bool:
        if self.direction == "min":
            return self.value >= self.threshold
        return self.value <= self.threshold


@dataclass
class ReviewReport:
    application: str
    total_requirements: int
    total_test_cases: int
    results: list[CheckResult]

    @property
    def verdict(self) -> str:
        failed = [r for r in self.results if not r.passed]
        if any(r.severity == MAJOR for r in failed):
            return MAJOR_REWORK
        if failed:
            return MINOR_REWORK
        return ACCEPT


def _ratio(part: int, whole: int) -> float:
    # An empty population cannot violate a rule, so it scores 1.0.
    return part / whole if whole else 1.0


def requirement_coverage(reqs: RequirementSet, suite: TestSuite) -> tuple[float, list[str]]:
    covered = {rid for tc in suite.test_cases for rid in tc.requirement_ids}
    missing = [r.id for r in reqs.requirements if r.id not in covered]
    findings = [f"{rid} has no test case" for rid in missing]
    return _ratio(len(reqs.requirements) - len(missing), len(reqs.requirements)), findings


def traceability(reqs: RequirementSet, suite: TestSuite) -> tuple[float, list[str]]:
    valid_ids = reqs.ids
    findings = []
    for tc in suite.test_cases:
        unknown = [rid for rid in tc.requirement_ids if rid not in valid_ids]
        if not tc.requirement_ids:
            findings.append(f"{tc.id} is not linked to any requirement")
        elif unknown:
            findings.append(f"{tc.id} references unknown requirement(s): {', '.join(unknown)}")
    return _ratio(len(suite.test_cases) - len(findings), len(suite.test_cases)), findings


def high_priority_negative_coverage(
    reqs: RequirementSet, suite: TestSuite
) -> tuple[float, list[str]]:
    high = [r.id for r in reqs.requirements if r.priority == Priority.HIGH]
    with_negative = {
        rid
        for tc in suite.test_cases
        if tc.type in (TestType.NEGATIVE, TestType.BOUNDARY)
        for rid in tc.requirement_ids
    }
    missing = [rid for rid in high if rid not in with_negative]
    findings = [f"{rid} (high priority) has no negative or boundary test" for rid in missing]
    return _ratio(len(high) - len(missing), len(high)), findings


def step_completeness(reqs: RequirementSet, suite: TestSuite) -> tuple[float, list[str]]:
    findings = []
    incomplete: set[str] = set()
    for tc in suite.test_cases:
        if not tc.steps:
            findings.append(f"{tc.id} has no steps")
            incomplete.add(tc.id)
            continue
        for number, step in enumerate(tc.steps, start=1):
            if not step.action.strip():
                findings.append(f"{tc.id} step {number} has no action")
                incomplete.add(tc.id)
            if not step.expected.strip():
                findings.append(f"{tc.id} step {number} has no expected result")
                incomplete.add(tc.id)
    return _ratio(len(suite.test_cases) - len(incomplete), len(suite.test_cases)), findings


def negative_test_ratio(reqs: RequirementSet, suite: TestSuite) -> tuple[float, list[str]]:
    negatives = sum(
        1 for tc in suite.test_cases if tc.type in (TestType.NEGATIVE, TestType.BOUNDARY)
    )
    return _ratio(negatives, len(suite.test_cases)), []


def _fingerprint(tc: TestCase) -> str:
    text = tc.title + " " + " ".join(step.action for step in tc.steps)
    return " ".join(text.lower().split())


def make_duplicate_rate(similarity_threshold: float) -> Callable[..., tuple[float, list[str]]]:
    def duplicate_rate(reqs: RequirementSet, suite: TestSuite) -> tuple[float, list[str]]:
        findings = []
        duplicated: set[str] = set()
        for a, b in combinations(suite.test_cases, 2):
            similarity = SequenceMatcher(None, _fingerprint(a), _fingerprint(b)).ratio()
            if similarity >= similarity_threshold:
                findings.append(f"{a.id} and {b.id} are {similarity:.0%} similar")
                duplicated.update((a.id, b.id))
        if not suite.test_cases:
            return 0.0, findings
        return len(duplicated) / len(suite.test_cases), findings

    return duplicate_rate


DESCRIPTIONS = {
    "requirement_coverage": "Requirements covered by at least one test",
    "traceability": "Tests that reference only existing requirements",
    "high_priority_negative_coverage": "High-priority requirements with a negative/boundary test",
    "step_completeness": "Tests whose steps all have an action and an expected result",
    "negative_test_ratio": "Share of negative and boundary tests",
    "duplicate_rate": "Share of tests that are near-duplicates",
}


def review(reqs: RequirementSet, suite: TestSuite, config: dict[str, Any]) -> ReviewReport:
    metrics: dict[str, Callable[..., tuple[float, list[str]]]] = {
        "requirement_coverage": requirement_coverage,
        "traceability": traceability,
        "high_priority_negative_coverage": high_priority_negative_coverage,
        "step_completeness": step_completeness,
        "negative_test_ratio": negative_test_ratio,
        "duplicate_rate": make_duplicate_rate(config.get("duplicate_similarity_threshold", 0.9)),
    }

    results = []
    for name, check in config["checks"].items():
        if name not in metrics:
            raise ValueError(f"Unknown review check in config: {name}")
        if ("min" in check) == ("max" in check):
            raise ValueError(f"Check {name} must set exactly one of 'min' or 'max'")
        severity = check.get("severity", MINOR)
        if severity not in (MAJOR, MINOR):
            raise ValueError(f"Check {name} has severity {severity!r}; use 'major' or 'minor'")
        direction = "min" if "min" in check else "max"
        value, findings = metrics[name](reqs, suite)
        results.append(
            CheckResult(
                name=name,
                description=DESCRIPTIONS[name],
                value=value,
                threshold=float(check[direction]),
                direction=direction,
                severity=severity,
                findings=findings,
            )
        )

    return ReviewReport(
        application=suite.application,
        total_requirements=len(reqs.requirements),
        total_test_cases=len(suite.test_cases),
        results=results,
    )
