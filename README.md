# AI Test Designer

**Generate manual test cases from requirements with Claude, then check them with quality gates before anyone trusts them.**

LLMs can draft a test suite in seconds, but the output can't be accepted blindly. It may skip a requirement, cite one that doesn't exist, repeat itself, or write steps nobody can verify. This tool treats AI-generated tests like a release candidate: it **measures** them, applies **quality gates**, and returns a **verdict**.

```
requirements.yaml ──► Claude (structured JSON output) ──► suite.json ──► quality gates ──► report.md + exit code
```

## Quality gates

Each gate has a threshold. A failing **blocking** gate fails the whole suite, even when every other metric looks good, the same way one blocker defect stops a release.

| Gate | Default threshold | Blocking | What it catches |
|---|---|---|---|
| Requirement coverage | ≥ 100% | yes | Requirements with no test case |
| Traceability | ≥ 100% | yes | Tests that cite requirement IDs that don't exist (hallucinated links) |
| High-priority negative coverage | ≥ 100% | yes | High-priority requirements tested only on the happy path |
| Step completeness | ≥ 95% | yes | Steps with no action or no expected result |
| Negative test ratio | ≥ 25% | no | Suites that are mostly happy-path tests |
| Duplicate rate | ≤ 5% | no | Near-duplicate tests (title + steps similarity) |

Thresholds live in [`config/quality_gates.yaml`](config/quality_gates.yaml).

Verdicts: **PASS**, **PASS_WITH_WARNINGS** (only non-blocking gates failed) or **FAIL**. `evaluate` and `run` exit with code `1` on FAIL, so the tool can gate a CI pipeline.

## Example

[`examples/seeded_suite_with_defects.json`](examples/seeded_suite_with_defects.json) is a **hand-written** suite for [SauceDemo](https://www.saucedemo.com), a public practice shop. It is not model output: it is seeded with three known defects to show what the gates catch. A missing requirement, a link to a non-existent requirement, and a duplicated test:

```
$ python -m ai_test_designer evaluate --requirements requirements/saucedemo.yaml \
      --suite examples/seeded_suite_with_defects.json --report examples/seeded_suite_report.md
  [FAIL] requirement_coverage: 92%
  [FAIL] traceability: 94%
  [FAIL] high_priority_negative_coverage: 62%
  [pass] step_completeness: 100%
  [pass] negative_test_ratio: 39%
  [warn] duplicate_rate: 11%
Verdict: FAIL  (report: examples/seeded_suite_report.md)
```

All three planted defects were caught, plus three high-priority requirements that only had happy-path tests. Full report: [`examples/seeded_suite_report.md`](examples/seeded_suite_report.md), including a requirement-to-test traceability matrix.

## Quick start

Requires Python 3.10+ and an [Anthropic API key](https://console.anthropic.com/) for generation (evaluation works offline).

```bash
python -m venv .venv
source .venv/bin/activate          # Windows: .venv\Scripts\activate
pip install -e ".[dev]"

export ANTHROPIC_API_KEY=...       # Windows PowerShell: $env:ANTHROPIC_API_KEY="..."

# Generate a suite with Claude, then run the quality gates on it
python -m ai_test_designer run --requirements requirements/saucedemo.yaml

# Or run the steps separately
python -m ai_test_designer generate --requirements requirements/saucedemo.yaml --out output/suite.json
python -m ai_test_designer evaluate --requirements requirements/saucedemo.yaml --suite output/suite.json
```

Run the tool's own tests (no API key needed):

```bash
pytest
```

## Design decisions

- **Structured output, not free text.** Claude answers against a strict JSON schema, so every test case has the same fields and can be checked by code.
- **Deterministic gates.** The checks are plain code, not another LLM call: they are cheap, reproducible and safe to run in CI. The model never grades its own work.
- **Blocking vs. non-blocking gates.** The same trade-off a test manager makes at a go/no-go meeting: some problems stop the release, others are noted.
- **The prompt and the gates mirror each other.** Every rule in the generation prompt ("cover every requirement", "only cite existing IDs") has a gate that verifies the model actually followed it.
- **Testable without the API.** The generator is tested with a fake client, so the test suite runs offline and in CI.
- **Graceful failure.** Refusals, truncated responses and schema mismatches raise clear errors instead of producing a partial suite. Server-side model fallback is enabled for declined requests.

## Project structure

```
requirements/saucedemo.yaml       Input: requirements for the demo app
config/quality_gates.yaml         Gate thresholds
src/ai_test_designer/
  generator.py                    Claude call with a JSON schema
  quality_gates.py                Metrics and verdict
  report.py                       Markdown report
  cli.py                          generate / evaluate / run
examples/                         Seeded suite and its report
tests/                            pytest suite (runs offline)
```

## Roadmap

- LLM-as-judge for qualities code can't measure (clarity, realism of test data), reported next to the deterministic gates
- Export test cases to Playwright skeletons and run them against SauceDemo
- Compare prompts and models on the same requirements (an eval loop for test generation)

## About

Built by **Tülay Güçlü**, a QA lead with 14+ years in defence, public-sector and telecom projects, now focused on AI-augmented testing.
[LinkedIn](https://www.linkedin.com/in/tulayguclu/)
