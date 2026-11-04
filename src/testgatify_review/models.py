"""Data models for requirements and generated test suites."""

from __future__ import annotations

from enum import Enum
from typing import ClassVar

from pydantic import BaseModel, model_validator


class Priority(str, Enum):
    HIGH = "high"
    MEDIUM = "medium"
    LOW = "low"


class TestType(str, Enum):
    __test__: ClassVar[bool] = False  # tell pytest this is not a test class

    POSITIVE = "positive"
    NEGATIVE = "negative"
    BOUNDARY = "boundary"


class Requirement(BaseModel):
    id: str
    title: str
    description: str
    priority: Priority


class RequirementSet(BaseModel):
    application: str
    url: str | None = None
    description: str = ""
    requirements: list[Requirement]

    @model_validator(mode="after")
    def _ids_are_unique(self) -> "RequirementSet":
        seen: set[str] = set()
        for req in self.requirements:
            if req.id in seen:
                raise ValueError(f"Duplicate requirement id: {req.id}")
            seen.add(req.id)
        return self

    @property
    def ids(self) -> set[str]:
        return {req.id for req in self.requirements}


class TestStep(BaseModel):
    __test__: ClassVar[bool] = False

    action: str
    expected: str


class TestCase(BaseModel):
    __test__: ClassVar[bool] = False

    id: str
    title: str
    requirement_ids: list[str]
    type: TestType
    priority: Priority
    preconditions: list[str]
    steps: list[TestStep]


class TestSuite(BaseModel):
    __test__: ClassVar[bool] = False

    application: str
    test_cases: list[TestCase]
