from __future__ import annotations

import logging
from pathlib import Path

from .extract import cached_extract
from .fetch import allowed_by_robots, fetch_url
from .models import SearchResponse, SearchResult, SearchSettings
from .search import search_web
from .summarize import source_bullets, synthesize_from_search_results, synthesize_paragraph


class SearchEngine:
    def __init__(self, cache_dir: Path | str | None = None) -> None:
        self.cache_dir = Path(cache_dir) if cache_dir is not None else None
        self.logger = logging.getLogger(__name__)

    def run(self, query: str, settings: SearchSettings | None = None) -> SearchResponse:
        normalized_query = query.strip()
        if not normalized_query:
            return SearchResponse(
                query="",
                error="Query cannot be empty.",
                summary="Please provide a search topic.",
            )

        settings = settings or SearchSettings()
        self.logger.info(
            "Running search: query='%s', max_results=%s, provider=%s, safe_search=%s",
            normalized_query,
            settings.max_results,
            settings.provider,
            settings.safe_search,
        )

        try:
            raw_results = search_web(
                normalized_query,
                max_results=settings.max_results,
                provider=settings.provider,
                safe_search=settings.safe_search,
            )
        except Exception:
            self.logger.exception("Search provider raised an exception for query='%s'", normalized_query)
            return SearchResponse(
                query=normalized_query,
                error="Search providers failed. Try a different query or provider.",
                summary=(
                    "The search request failed before results were returned. "
                    "Try another query and retry."
                ),
            )

        results = [SearchResult.from_mapping(result) for result in raw_results]

        if not results:
            paragraph = (
                "Not enough high-quality sources were accessible to produce a reliable summary. "
                "No search results were returned or accessible; this can happen due to network "
                "restrictions or a very narrow query."
            )
            return SearchResponse(
                query=normalized_query,
                results=[],
                summary=paragraph,
                sources=[],
                error="No results were returned.",
            )

        source_summaries = []
        extraction_limit = min(len(results), max(1, min(settings.max_results, 10)))

        for result in results[:extraction_limit]:
            if not result.url:
                continue

            if not allowed_by_robots(result.url):
                self.logger.info("Skipped by robots.txt: %s", result.url)
                continue

            html, status = fetch_url(result.url, self.cache_dir)
            if not html:
                self.logger.info("Fetch failed for %s (%s)", result.url, status)
                continue

            text = cached_extract(result.url, html, self.cache_dir)
            if not text or len(text) < 200:
                continue

            bullets = source_bullets(text)
            if not bullets:
                continue

            source_summaries.append({"url": result.url, "bullets": bullets})

        if not source_summaries:
            paragraph, sources = synthesize_from_search_results(raw_results, normalized_query)
        else:
            paragraph, sources = synthesize_paragraph(
                source_summaries,
                min_sources=1,
                query=normalized_query,
                max_sentences=10,
            )

        return SearchResponse(
            query=normalized_query,
            results=results,
            summary=paragraph,
            sources=sources,
        )
