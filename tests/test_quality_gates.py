from __future__ import annotations

import pytest

from ai_test_designer.loader import load_suite
from ai_test_designer.quality_gates import FAIL, PASS, PASS_WITH_WARNINGS, evaluate

from .conftest import make_case


def result(report, name):
    return next(r for r in report.results if r.name == name)


def test_good_suite_passes_every_gate(reqs, good_suite, config):
    report = evaluate(reqs, good_suite, config)
    assert report.verdict == PASS
    assert all(r.passed for r in report.results)


def test_uncovered_requirement_fails_the_suite(reqs, good_suite, config):
    good_suite.test_cases = [tc for tc in good_suite.test_cases if "REQ-NAV-01" not in tc.requirement_ids]
    report = evaluate(reqs, good_suite, config)
    coverage = result(report, "requirement_coverage")
    assert not coverage.passed
    assert coverage.findings == ["REQ-NAV-01 has no test case"]
    assert report.verdict == FAIL


def test_unknown_requirement_reference_is_reported(reqs, good_suite, config):
    good_suite.test_cases.append(make_case("TC-900", ["REQ-LOGIN-01", "REQ-GHOST-01"]))
    trace = result(evaluate(reqs, good_suite, config), "traceability")
    assert not trace.passed
    assert trace.findings == ["TC-900 references unknown requirement(s): REQ-GHOST-01"]


def test_high_priority_requirement_without_negative_test(reqs, good_suite, config):
    good_suite.test_cases = [
        tc
        for tc in good_suite.test_cases
        if not ("REQ-CHK-03" in tc.requirement_ids and tc.type.value == "negative")
    ]
    neg = result(evaluate(reqs, good_suite, config), "high_priority_negative_coverage")
    assert neg.findings == ["REQ-CHK-03 (high priority) has no negative or boundary test"]


def test_missing_expected_result_is_reported(reqs, good_suite, config):
    good_suite.test_cases.append(
        make_case("TC-901", ["REQ-INV-01"], steps=[("Open the page", "Page opens"), ("Click sort", "  ")])
    )
    steps = result(evaluate(reqs, good_suite, config), "step_completeness")
    assert steps.findings == ["TC-901 step 2 has no expected result"]


def test_near_duplicates_only_warn(reqs, good_suite, config):
    same_steps = [("Enter standard_user / secret_sauce and click Login", "Products page is shown")]
    good_suite.test_cases += [
        make_case("TC-950", ["REQ-LOGIN-01"], title="Valid login", steps=same_steps),
        make_case("TC-951", ["REQ-LOGIN-01"], title="Valid login ", steps=same_steps),
    ]
    report = evaluate(reqs, good_suite, config)
    dup = result(report, "duplicate_rate")
    assert not dup.passed and not dup.blocking
    assert "TC-950 and TC-951" in dup.findings[0]
    assert report.verdict == PASS_WITH_WARNINGS


def test_gate_needs_exactly_one_threshold(reqs, good_suite, config):
    config["gates"]["traceability"] = {"min": 1.0, "max": 1.0}
    with pytest.raises(ValueError, match="exactly one"):
        evaluate(reqs, good_suite, config)


def test_unknown_gate_name_is_rejected(reqs, good_suite, config):
    config["gates"]["made_up_metric"] = {"min": 1.0}
    with pytest.raises(ValueError, match="Unknown quality gate"):
        evaluate(reqs, good_suite, config)


def test_seeded_example_catches_every_planted_defect(root, reqs, config):
    suite = load_suite(root / "examples" / "seeded_suite_with_defects.json")
    report = evaluate(reqs, suite, config)
    assert report.verdict == FAIL
    assert "REQ-NAV-01 has no test case" in result(report, "requirement_coverage").findings
    assert "TC-016 references unknown requirement(s): REQ-CART-99" in result(report, "traceability").findings
    assert any("TC-001 and TC-002" in f for f in result(report, "duplicate_rate").findings)
