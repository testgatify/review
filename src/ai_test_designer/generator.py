"""Ask Claude to design a manual test suite from a requirement set."""

from __future__ import annotations

from typing import Any

import anthropic
import yaml

from .models import RequirementSet, TestSuite

DEFAULT_MODEL = "claude-opus-5-5"
DEFAULT_EFFORT = "high"

# Server-side fallback: if the model declines a request, the API retries it on
# a suitable substitute model inside the same call.
FALLBACK_BETA = "server-side-fallback-2026-07-01"

SYSTEM_PROMPT = """\
You are a senior QA engineer. You design manual test cases from software
requirements so that a tester who has never seen the application can run them.

Rules:
- Cover every requirement with at least one test case.
- For every high-priority requirement, include at least one negative or
  boundary test in addition to the positive one.
- Reference only requirement IDs that appear in the requirement list.
- Every step has a concrete action and an observable, checkable expected
  result. Quote exact UI texts and error messages when the requirement gives them.
- Use only test data that the requirements mention.
- Do not write two test cases that check the same thing.
- Number test cases TC-001, TC-002, and so on.
- Set each test case's priority from the requirement it covers.
"""

_STEP_SCHEMA: dict[str, Any] = {
    "type": "object",
    "properties": {
        "action": {"type": "string"},
        "expected": {"type": "string"},
    },
    "required": ["action", "expected"],
    "additionalProperties": False,
}

_TEST_CASE_SCHEMA: dict[str, Any] = {
    "type": "object",
    "properties": {
        "id": {"type": "string"},
        "title": {"type": "string"},
        "requirement_ids": {"type": "array", "items": {"type": "string"}},
        "type": {"type": "string", "enum": ["positive", "negative", "boundary"]},
        "priority": {"type": "string", "enum": ["high", "medium", "low"]},
        "preconditions": {"type": "array", "items": {"type": "string"}},
        "steps": {"type": "array", "items": _STEP_SCHEMA},
    },
    "required": ["id", "title", "requirement_ids", "type", "priority", "preconditions", "steps"],
    "additionalProperties": False,
}

TEST_SUITE_SCHEMA: dict[str, Any] = {
    "type": "object",
    "properties": {
        "application": {"type": "string"},
        "test_cases": {"type": "array", "items": _TEST_CASE_SCHEMA},
    },
    "required": ["application", "test_cases"],
    "additionalProperties": False,
}


class GenerationError(RuntimeError):
    """Claude did not return a usable test suite."""


def build_user_prompt(requirements: RequirementSet) -> str:
    req_yaml = yaml.safe_dump(
        requirements.model_dump(mode="json"), sort_keys=False, allow_unicode=True
    )
    return (
        f"Design a manual test suite for {requirements.application}.\n\n"
        f"Requirements:\n\n{req_yaml}"
    )


def generate_test_suite(
    requirements: RequirementSet,
    client: anthropic.Anthropic | None = None,
    model: str = DEFAULT_MODEL,
    effort: str = DEFAULT_EFFORT,
) -> TestSuite:
    """Call Claude and return a validated TestSuite."""
    client = client or anthropic.Anthropic()

    # Streaming keeps a long response from hitting HTTP timeouts.
    with client.beta.messages.stream(
        model=model,
        max_tokens=64000,
        betas=[FALLBACK_BETA],
        fallbacks="default",
        output_config={
            "effort": effort,
            "format": {"type": "json_schema", "schema": TEST_SUITE_SCHEMA},
        },
        system=SYSTEM_PROMPT,
        messages=[{"role": "user", "content": build_user_prompt(requirements)}],
    ) as stream:
        message = stream.get_final_message()

    if message.stop_reason == "refusal":
        raise GenerationError("Claude declined the request (stop_reason=refusal).")
    if message.stop_reason == "max_tokens":
        raise GenerationError("The response was cut off at max_tokens; the suite is incomplete.")

    text = next((block.text for block in message.content if block.type == "text"), None)
    if text is None:
        raise GenerationError("The response contained no text block.")

    try:
        return TestSuite.model_validate_json(text)
    except ValueError as exc:
        raise GenerationError(f"The response did not match the test suite schema: {exc}") from exc
