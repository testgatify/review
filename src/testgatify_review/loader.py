"""Read requirements, review settings and test suites from disk."""

from __future__ import annotations

from pathlib import Path
from typing import Any

import yaml

from .models import RequirementSet, TestSuite


def load_requirements(path: str | Path) -> RequirementSet:
    data = yaml.safe_load(Path(path).read_text(encoding="utf-8"))
    return RequirementSet.model_validate(data)


def load_review_config(path: str | Path) -> dict[str, Any]:
    return yaml.safe_load(Path(path).read_text(encoding="utf-8"))


def load_suite(path: str | Path) -> TestSuite:
    return TestSuite.model_validate_json(Path(path).read_text(encoding="utf-8"))


def save_suite(suite: TestSuite, path: str | Path) -> None:
    out = Path(path)
    out.parent.mkdir(parents=True, exist_ok=True)
    out.write_text(suite.model_dump_json(indent=2), encoding="utf-8")
