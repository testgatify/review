from __future__ import annotations

import pytest

from testgatify_review.loader import load_suite
from testgatify_review.review_checks import ACCEPT, MAJOR_REWORK, MINOR_REWORK, review

from .conftest import make_case


def result(report, name):
    return next(r for r in report.results if r.name == name)


def test_good_suite_is_accepted(reqs, good_suite, config):
    report = review(reqs, good_suite, config)
    assert report.verdict == ACCEPT
    assert all(r.passed for r in report.results)


def test_uncovered_requirement_needs_major_rework(reqs, good_suite, config):
    good_suite.test_cases = [tc for tc in good_suite.test_cases if "REQ-NAV-01" not in tc.requirement_ids]
    report = review(reqs, good_suite, config)
    coverage = result(report, "requirement_coverage")
    assert not coverage.passed
    assert coverage.findings == ["REQ-NAV-01 has no test case"]
    assert report.verdict == MAJOR_REWORK


def test_unknown_requirement_reference_is_reported(reqs, good_suite, config):
    good_suite.test_cases.append(make_case("TC-900", ["REQ-LOGIN-01", "REQ-GHOST-01"]))
    trace = result(review(reqs, good_suite, config), "traceability")
    assert not trace.passed
    assert trace.findings == ["TC-900 references unknown requirement(s): REQ-GHOST-01"]


def test_high_priority_requirement_without_negative_test(reqs, good_suite, config):
    good_suite.test_cases = [
        tc
        for tc in good_suite.test_cases
        if not ("REQ-CHK-03" in tc.requirement_ids and tc.type.value == "negative")
    ]
    neg = result(review(reqs, good_suite, config), "high_priority_negative_coverage")
    assert neg.findings == ["REQ-CHK-03 (high priority) has no negative or boundary test"]


def test_missing_expected_result_is_reported(reqs, good_suite, config):
    good_suite.test_cases.append(
        make_case("TC-901", ["REQ-INV-01"], steps=[("Open the page", "Page opens"), ("Click sort", "  ")])
    )
    steps = result(review(reqs, good_suite, config), "step_completeness")
    assert steps.findings == ["TC-901 step 2 has no expected result"]


def test_near_duplicates_need_only_minor_rework(reqs, good_suite, config):
    same_steps = [("Enter standard_user / secret_sauce and click Login", "Products page is shown")]
    good_suite.test_cases += [
        make_case("TC-950", ["REQ-LOGIN-01"], title="Valid login", steps=same_steps),
        make_case("TC-951", ["REQ-LOGIN-01"], title="Valid login ", steps=same_steps),
    ]
    report = review(reqs, good_suite, config)
    dup = result(report, "duplicate_rate")
    assert not dup.passed and dup.severity == "minor"
    assert "TC-950 and TC-951" in dup.findings[0]
    assert report.verdict == MINOR_REWORK


def test_check_needs_exactly_one_threshold(reqs, good_suite, config):
    config["checks"]["traceability"] = {"min": 1.0, "max": 1.0}
    with pytest.raises(ValueError, match="exactly one"):
        review(reqs, good_suite, config)


def test_unknown_check_name_is_rejected(reqs, good_suite, config):
    config["checks"]["made_up_metric"] = {"min": 1.0}
    with pytest.raises(ValueError, match="Unknown review check"):
        review(reqs, good_suite, config)


def test_invalid_severity_is_rejected(reqs, good_suite, config):
    config["checks"]["traceability"]["severity"] = "blocker"
    with pytest.raises(ValueError, match="severity"):
        review(reqs, good_suite, config)


def test_seeded_example_catches_every_planted_defect(root, reqs, config):
    suite = load_suite(root / "examples" / "seeded_suite_with_defects.json")
    report = review(reqs, suite, config)
    assert report.verdict == MAJOR_REWORK
    assert "REQ-NAV-01 has no test case" in result(report, "requirement_coverage").findings
    assert "TC-016 references unknown requirement(s): REQ-CART-99" in result(report, "traceability").findings
    assert any("TC-001 and TC-002" in f for f in result(report, "duplicate_rate").findings)
