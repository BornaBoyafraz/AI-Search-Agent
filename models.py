from __future__ import annotations

from dataclasses import dataclass, field
from typing import List


@dataclass(slots=True)
class ResultItem:
    title: str
    url: str
    snippet: str = ""


@dataclass(slots=True)
class AgentResponse:
    answer: str = ""
    results: List[ResultItem] = field(default_factory=list)

    @property
    def is_list(self) -> bool:
        return bool(self.results)
