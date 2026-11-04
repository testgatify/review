"""Command-line interface.

    python -m ai_test_designer generate --requirements requirements/saucedemo.yaml --out output/suite.json
    python -m ai_test_designer evaluate --requirements requirements/saucedemo.yaml --suite output/suite.json
    python -m ai_test_designer run      --requirements requirements/saucedemo.yaml

`evaluate` and `run` exit with code 1 when the verdict is FAIL, so they can
gate a CI pipeline.
"""

from __future__ import annotations

import argparse
import sys
from pathlib import Path

import anthropic

from .generator import DEFAULT_EFFORT, DEFAULT_MODEL, GenerationError, generate_test_suite
from .loader import load_gate_config, load_requirements, load_suite, save_suite
from .models import RequirementSet, TestSuite
from .quality_gates import FAIL, evaluate
from .report import render_markdown

DEFAULT_CONFIG = "config/quality_gates.yaml"


def _generate(args: argparse.Namespace, reqs: RequirementSet) -> TestSuite:
    print(f"Generating test cases for {len(reqs.requirements)} requirements with {args.model}...")
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


def _evaluate(args: argparse.Namespace, reqs: RequirementSet, suite: TestSuite) -> int:
    report = evaluate(reqs, suite, load_gate_config(args.config))
    report_path = Path(args.report)
    report_path.parent.mkdir(parents=True, exist_ok=True)
    report_path.write_text(render_markdown(report, reqs, suite), encoding="utf-8")

    for r in report.results:
        status = "pass" if r.passed else ("FAIL" if r.blocking else "warn")
        print(f"  [{status:>4}] {r.name}: {r.value:.0%}")
    print(f"Verdict: {report.verdict}  (report: {report_path})")
    return 1 if report.verdict == FAIL else 0


def main(argv: list[str] | None = None) -> int:
    parser = argparse.ArgumentParser(
        prog="ai_test_designer",
        description="Generate test cases with Claude and check them with quality gates.",
    )
    sub = parser.add_subparsers(dest="command", required=True)

    def add_common(p: argparse.ArgumentParser) -> None:
        p.add_argument("--requirements", required=True, help="Requirements YAML file")

    def add_generate_opts(p: argparse.ArgumentParser) -> None:
        p.add_argument("--out", default="output/suite.json", help="Where to save the suite")
        p.add_argument("--model", default=DEFAULT_MODEL)
        p.add_argument("--effort", default=DEFAULT_EFFORT, choices=["low", "medium", "high", "xhigh", "max"])

    def add_evaluate_opts(p: argparse.ArgumentParser) -> None:
        p.add_argument("--config", default=DEFAULT_CONFIG, help="Quality gate config YAML")
        p.add_argument("--report", default="output/report.md", help="Where to write the Markdown report")

    gen = sub.add_parser("generate", help="Generate a test suite with Claude")
    add_common(gen)
    add_generate_opts(gen)

    ev = sub.add_parser("evaluate", help="Run quality gates on an existing suite")
    add_common(ev)
    ev.add_argument("--suite", required=True, help="Test suite JSON file")
    add_evaluate_opts(ev)

    run = sub.add_parser("run", help="Generate, then evaluate")
    add_common(run)
    add_generate_opts(run)
    add_evaluate_opts(run)

    args = parser.parse_args(argv)
    reqs = load_requirements(args.requirements)

    if args.command == "generate":
        _generate(args, reqs)
        return 0
    if args.command == "evaluate":
        return _evaluate(args, reqs, load_suite(args.suite))
    return _evaluate(args, reqs, _generate(args, reqs))
