"""Generator tests use a fake client, so they run without an API key or network."""

from __future__ import annotations

import json
from types import SimpleNamespace

import pytest

from testgatify_review.generator import (
    DEFAULT_MODEL,
    TEST_SUITE_SCHEMA,
    GenerationError,
    build_user_prompt,
    generate_test_suite,
)


class FakeStream:
    def __init__(self, message):
        self._message = message

    def __enter__(self):
        return self

    def __exit__(self, *exc):
        return False

    def get_final_message(self):
        return self._message


class FakeClient:
    """Records the request and returns a canned message."""

    def __init__(self, text: str | None, stop_reason: str = "end_turn"):
        content = [SimpleNamespace(type="text", text=text)] if text is not None else []
        self._message = SimpleNamespace(stop_reason=stop_reason, content=content)
        self.request: dict = {}
        self.beta = SimpleNamespace(messages=SimpleNamespace(stream=self._stream))

    def _stream(self, **kwargs):
        self.request = kwargs
        return FakeStream(self._message)


VALID_SUITE = {
    "application": "SauceDemo",
    "test_cases": [
        {
            "id": "TC-001",
            "title": "Valid login",
            "requirement_ids": ["REQ-LOGIN-01"],
            "type": "positive",
            "priority": "high",
            "preconditions": [],
            "steps": [{"action": "Log in as standard_user", "expected": "Products page is shown"}],
        }
    ],
}


def test_returns_validated_suite(reqs):
    client = FakeClient(json.dumps(VALID_SUITE))
    suite = generate_test_suite(reqs, client=client)
    assert suite.test_cases[0].id == "TC-001"


def test_request_uses_schema_fallback_and_model(reqs):
    client = FakeClient(json.dumps(VALID_SUITE))
    generate_test_suite(reqs, client=client)
    req = client.request
    assert req["model"] == DEFAULT_MODEL
    assert req["output_config"]["format"]["schema"] == TEST_SUITE_SCHEMA
    assert req["fallbacks"] == "default"
    assert "REQ-NAV-01" in req["messages"][0]["content"]


def test_prompt_lists_every_requirement(reqs):
    prompt = build_user_prompt(reqs)
    for req in reqs.requirements:
        assert req.id in prompt


@pytest.mark.parametrize(
    ("text", "stop_reason", "message"),
    [
        ("{}", "refusal", "declined"),
        ("{}", "max_tokens", "cut off"),
        (None, "end_turn", "no text block"),
        ('{"application": "x"}', "end_turn", "did not match"),
    ],
)
def test_unusable_responses_raise(reqs, text, stop_reason, message):
    with pytest.raises(GenerationError, match=message):
        generate_test_suite(reqs, client=FakeClient(text, stop_reason))
