from __future__ import annotations

from dataclasses import dataclass, field
from typing import Any, Dict, List, Literal, cast

ProviderName = Literal["auto", "duckduckgo", "google_cse", "wikipedia"]
PROVIDER_CHOICES: tuple[ProviderName, ...] = (
    "auto",
    "duckduckgo",
    "google_cse",
    "wikipedia",
)

def _coerce_bool(value: Any, default: bool = True) -> bool:
    if isinstance(value, bool):
        return value
    if isinstance(value, (int, float)):
        return bool(value)
    if isinstance(value, str):
        return value.strip().lower() in {"1", "true", "yes", "on"}
    return default


@dataclass(slots=True)
class SearchSettings:
    max_results: int = 10
    safe_search: bool = True
    provider: ProviderName = "auto"

    @classmethod
    def from_mapping(cls, payload: Dict[str, Any] | None) -> "SearchSettings":
        payload = payload or {}

        raw_max_results = payload.get("max_results", cls.max_results)
        try:
            max_results = int(raw_max_results)
        except (TypeError, ValueError):
            max_results = cls.max_results
        max_results = max(1, min(30, max_results))

        provider_raw = str(payload.get("provider", cls.provider)).strip().lower()
        provider: ProviderName
        if provider_raw in PROVIDER_CHOICES:
            provider = cast(ProviderName, provider_raw)
        else:
            provider = "auto"

        safe_search = _coerce_bool(payload.get("safe_search", cls.safe_search), default=True)

        return cls(max_results=max_results, safe_search=safe_search, provider=provider)

    def to_dict(self) -> Dict[str, Any]:
        return {
            "max_results": self.max_results,
            "safe_search": self.safe_search,
            "provider": self.provider,
        }


@dataclass(slots=True)
class SearchResult:
    title: str
    snippet: str
    url: str
    domain: str = ""
    score: int = 0

    @classmethod
    def from_mapping(cls, payload: Dict[str, Any]) -> "SearchResult":
        return cls(
            title=str(payload.get("title", "") or ""),
            snippet=str(payload.get("snippet", "") or ""),
            url=str(payload.get("url", "") or ""),
            domain=str(payload.get("domain", "") or ""),
            score=int(payload.get("score", 0) or 0),
        )

    def to_dict(self) -> Dict[str, Any]:
        return {
            "title": self.title,
            "snippet": self.snippet,
            "url": self.url,
            "domain": self.domain,
            "score": self.score,
        }


@dataclass(slots=True)
class SearchResponse:
    query: str
    results: List[SearchResult] = field(default_factory=list)
    summary: str = ""
    sources: List[str] = field(default_factory=list)
    error: str | None = None

    def to_dict(self) -> Dict[str, Any]:
        return {
            "query": self.query,
            "results": [result.to_dict() for result in self.results],
            "summary": self.summary,
            "sources": self.sources,
            "error": self.error,
        }


@dataclass(slots=True)
class UserPreferences:
    settings: SearchSettings = field(default_factory=SearchSettings)
    recent_queries: List[str] = field(default_factory=list)

    def to_dict(self) -> Dict[str, Any]:
        return {
            **self.settings.to_dict(),
            "recent_queries": self.recent_queries,
        }
