from __future__ import annotations

from dataclasses import dataclass, field
from typing import Any, Dict, List, Optional

from .diagram_ir import DiagramSpec
from .diagram_parser import build_diagram_spec


@dataclass
class QuestionSpec:
    """One exam question consumed by the M20 renderer."""

    id: str
    text: str
    number: Optional[int] = None
    marks: Optional[float] = None
    options: List[str] = field(default_factory=list)
    diagrams: List[DiagramSpec] = field(default_factory=list)
    section: Optional[str] = None
    metadata: Dict[str, Any] = field(default_factory=dict)

    @classmethod
    def from_dict(cls, data: Dict[str, Any]) -> "QuestionSpec":
        d = dict(data)
        diagrams = []
        for item in d.pop("diagrams", []) or []:
            if isinstance(item, DiagramSpec):
                diagrams.append(item)
            elif isinstance(item, dict):
                diagrams.append(build_diagram_spec(item))
            else:
                raise TypeError("Question diagrams must be DiagramSpec or dictionaries.")
        return cls(diagrams=diagrams, **d)

    def ensure_valid(self) -> "QuestionSpec":
        if not str(self.id).strip():
            raise ValueError("Question ID must not be empty.")
        if not str(self.text).strip():
            raise ValueError(f"Question {self.id} text must not be empty.")
        if self.number is not None and int(self.number) <= 0:
            raise ValueError(f"Question {self.id} number must be positive.")
        if self.marks is not None and float(self.marks) < 0:
            raise ValueError(f"Question {self.id} marks must be non-negative.")
        for diagram in self.diagrams:
            diagram.ensure_valid()
        return self

    def to_dict(self) -> Dict[str, Any]:
        return {
            "id": self.id,
            "text": self.text,
            "number": self.number,
            "marks": self.marks,
            "options": list(self.options),
            "diagrams": [d.to_dict() for d in self.diagrams],
            "section": self.section,
            "metadata": self.metadata,
        }


@dataclass
class PaperSpec:
    """Structured question-paper input for M20.

    M20 is intentionally a composition layer. It consumes normalized question
    text and already-validated DiagramSpec objects; it does not solve questions
    or invent diagram semantics.
    """

    title: str
    questions: List[QuestionSpec] = field(default_factory=list)
    subject: Optional[str] = None
    exam: Optional[str] = None
    duration_minutes: Optional[int] = None
    total_marks: Optional[float] = None
    instructions: List[str] = field(default_factory=list)
    metadata: Dict[str, Any] = field(default_factory=dict)

    @classmethod
    def from_dict(cls, data: Dict[str, Any]) -> "PaperSpec":
        d = dict(data)
        questions = []
        for q in d.pop("questions", []) or []:
            questions.append(q if isinstance(q, QuestionSpec) else QuestionSpec.from_dict(q))
        return cls(questions=questions, **d)

    def ensure_valid(self) -> "PaperSpec":
        if not str(self.title).strip():
            raise ValueError("Paper title must not be empty.")
        if not self.questions:
            raise ValueError("Paper must contain at least one question.")
        ids = [q.id for q in self.questions]
        if len(ids) != len(set(ids)):
            raise ValueError("Question IDs must be unique.")
        for q in self.questions:
            q.ensure_valid()
        if self.duration_minutes is not None and int(self.duration_minutes) <= 0:
            raise ValueError("Duration must be positive.")
        if self.total_marks is not None and float(self.total_marks) < 0:
            raise ValueError("Total marks must be non-negative.")
        return self

    def resolved_total_marks(self) -> float:
        if self.total_marks is not None:
            return float(self.total_marks)
        return sum(float(q.marks or 0) for q in self.questions)

    def to_dict(self) -> Dict[str, Any]:
        return {
            "title": self.title,
            "subject": self.subject,
            "exam": self.exam,
            "duration_minutes": self.duration_minutes,
            "total_marks": self.resolved_total_marks(),
            "instructions": list(self.instructions),
            "questions": [q.to_dict() for q in self.questions],
            "metadata": self.metadata,
        }
