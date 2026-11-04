"""Command-line interface for TestGatify Review.

    testgatify-review generate --requirements requirements/saucedemo.yaml
    testgatify-review review   --requirements requirements/saucedemo.yaml --suite output/suite.json
    testgatify-review export   --suite output/suite.json
    testgatify-review run      --requirements requirements/saucedemo.yaml

(`python -m testgatify_review ...` works too.)

`review` and `run` exit with code 1 when the verdict is MAJOR_REWORK, so they
can stop a CI pipeline.
"""

from __future__ import annotations

import argparse
import sys
from pathlib import Path

import anthropic

from .export import to_excel, to_xray_csv
from .generator import DEFAULT_EFFORT, DEFAULT_MODEL, GenerationError, generate_test_suite
from .loader import load_requirements, load_review_config, load_suite, save_suite
from .models import RequirementSet, TestSuite
from .report import render_markdown
from .review_checks import MAJOR_REWORK, review

DEFAULT_CONFIG = "config/review_checks.yaml"


def _generate(args: argparse.Namespace, reqs: RequirementSet) -> TestSuite:
    print(f"Gatifying... Claude is writing test scenarios for {len(reqs.requirements)} requirements ({args.model}).")
    try:
        suite = generate_test_suite(reqs, model=args.model, effort=args.effort)
    except anthropic.AuthenticationError:
        sys.exit("Authentication failed. Set the ANTHROPIC_API_KEY environment variable.")
    except anthropic.APIConnectionError:
        sys.exit("Could not reach the Claude API. Check your internet connection.")
    except anthropic.APIStatusError as exc:
        sys.exit(f"Claude API error {exc.status_code}: {exc.message}")
    except GenerationError as exc:
        sys.exit(f"Generation failed: {exc}")
    save_suite(suite, args.out)
    print(f"Saved {len(suite.test_cases)} test cases to {args.out}")
    return suite


def _review(args: argparse.Namespace, reqs: RequirementSet, suite: TestSuite) -> int:
    report = review(reqs, suite, load_review_config(args.config))
    report_path = Path(args.report)
    report_path.parent.mkdir(parents=True, exist_ok=True)
    report_path.write_text(render_markdown(report, reqs, suite), encoding="utf-8")

    print("At the gate: static review of the test design (nothing is executed).")
    for r in report.results:
        status = "  ok " if r.passed else r.severity.upper()
        print(f"  [{status:>5}] {r.name}: {r.value:.0%}")
    print(f"Verdict: {report.verdict.replace('_', ' ')}  (report: {report_path})")
    return 1 if report.verdict == MAJOR_REWORK else 0


def _export(args: argparse.Namespace, suite: TestSuite) -> None:
    print(f"Excel:    {to_excel(suite, args.xlsx)}")
    print(f"Xray CSV: {to_xray_csv(suite, args.csv)}")


def main(argv: list[str] | None = None) -> int:
    parser = argparse.ArgumentParser(
        prog="testgatify-review",
        description="TestGatify Review: AI writes your test scenarios. The gate decides if they're ready.",
    )
    sub = parser.add_subparsers(dest="command", required=True)

    def add_requirements(p: argparse.ArgumentParser) -> None:
        p.add_argument("--requirements", required=True, help="Requirements YAML file")

    def add_generate_opts(p: argparse.ArgumentParser) -> None:
        p.add_argument("--out", default="output/suite.json", help="Where to save the suite (JSON)")
        p.add_argument("--model", default=DEFAULT_MODEL)
        p.add_argument("--effort", default=DEFAULT_EFFORT, choices=["low", "medium", "high", "xhigh", "max"])

    def add_review_opts(p: argparse.ArgumentParser) -> None:
        p.add_argument("--config", default=DEFAULT_CONFIG, help="Review checks YAML")
        p.add_argument("--report", default="output/review.md", help="Where to write the review report")

    def add_export_opts(p: argparse.ArgumentParser) -> None:
        p.add_argument("--xlsx", default="output/test_cases.xlsx", help="Excel output")
        p.add_argument("--csv", default="output/xray_import.csv", help="Xray CSV output")

    gen = sub.add_parser("generate", help="Claude writes a test suite from the requirements")
    add_requirements(gen)
    add_generate_opts(gen)

    rev = sub.add_parser("review", help="Statically review an existing test suite")
    add_requirements(rev)
    rev.add_argument("--suite", required=True, help="Test suite JSON file")
    add_review_opts(rev)

    exp = sub.add_parser("export", help="Export a test suite to Excel and Xray CSV")
    exp.add_argument("--suite", required=True, help="Test suite JSON file")
    add_export_opts(exp)

    run = sub.add_parser("run", help="Generate, review and export in one go")
    add_requirements(run)
    add_generate_opts(run)
    add_review_opts(run)
    add_export_opts(run)

    args = parser.parse_args(argv)

    if args.command == "export":
        _export(args, load_suite(args.suite))
        return 0

    reqs = load_requirements(args.requirements)
    if args.command == "generate":
        _generate(args, reqs)
        return 0
    if args.command == "review":
        return _review(args, reqs, load_suite(args.suite))

    suite = _generate(args, reqs)
    code = _review(args, reqs, suite)
    _export(args, suite)
    return code
