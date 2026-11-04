from __future__ import annotations

from pathlib import Path

import pytest

from ai_test_designer.loader import load_gate_config, load_requirements
from ai_test_designer.models import RequirementSet, TestCase, TestStep, TestSuite

ROOT = Path(__file__).resolve().parents[1]


@pytest.fixture
def root() -> Path:
    return ROOT


@pytest.fixture
def reqs() -> RequirementSet:
    return load_requirements(ROOT / "requirements" / "saucedemo.yaml")


@pytest.fixture
def config() -> dict:
    return load_gate_config(ROOT / "config" / "quality_gates.yaml")


def make_case(
    case_id: str,
    req_ids: list[str],
    type_: str = "positive",
    title: str | None = None,
    steps: list[tuple[str, str]] | None = None,
) -> TestCase:
    return TestCase(
        id=case_id,
        title=title or f"Distinct check number {case_id} for {' '.join(req_ids)}",
        requirement_ids=req_ids,
        type=type_,
        priority="high",
        preconditions=[],
        steps=[TestStep(action=a, expected=e) for a, e in (steps or [(f"do {case_id}", f"see {case_id}")])],
    )


@pytest.fixture
def good_suite(reqs: RequirementSet) -> TestSuite:
    """One positive test per requirement, plus a negative test per high-priority one."""
    cases = []
    for req in reqs.requirements:
        cases.append(
            make_case(
                f"TC-{len(cases) + 1:03d}", [req.id], "positive",
                title=req.title,
                steps=[(req.description, "The described outcome happens")],
            )
        )
        if req.priority.value == "high":
            cases.append(
                make_case(
                    f"TC-{len(cases) + 1:03d}", [req.id], "negative",
                    title=f"{req.id} negative check",
                    steps=[(f"Enter data that breaks: {req.title}", "An error is shown")],
                )
            )
    return TestSuite(application=reqs.application, test_cases=cases)
