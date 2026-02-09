# Standard library imports for CLI args and filesystem paths.
import sys
from pathlib import Path

# Local modules that handle search, fetching, extraction, summarization, and output.
from agent.fetch import allowed_by_robots, fetch_url
from agent.extract import cached_extract
from agent.search import search_web
from agent.summarize import (
    source_bullets,
    synthesize_from_search_results,
    synthesize_paragraph,
)
from agent.utils import output_path
from agent.writeout import write_output


def run(query: str) -> int:
    # Perform a web search for the user query.
    results = search_web(query, max_results=15)
    if not results:
        # Fall back to a clear error paragraph if no sources are reachable.
        paragraph = (
            "Not enough high-quality sources were accessible to produce a reliable summary. "
            "No search results were returned or accessible; this can happen due to network "
            "restrictions or a very narrow query."
        )
        # Persist the failure result so the user still gets an output file.
        out_path = output_path(query)
        write_output(out_path, paragraph, [])
        print(f"Saved to {out_path}")
        return 1

    # Cache directory for fetched HTML and extracted text.
    cache_dir = Path("cache")
    # Accumulate per-source bullet summaries for synthesis.
    source_summaries = []

    for r in results[:10]:
        # Pull the URL from each search result.
        url = r["url"]
        # Respect robots.txt rules before fetching content.
        if not allowed_by_robots(url):
            continue
        # Fetch the page (and cache it) to avoid refetching on reruns.
        html, status = fetch_url(url, cache_dir)
        if not html:
            continue
        # Extract readable text from HTML, using cache to speed repeats.
        text = cached_extract(url, html, cache_dir)
        # Skip thin or empty content that won't summarize well.
        if not text or len(text) < 200:
            continue
        # Convert the source text into bullet points.
        bullets = source_bullets(text)
        if not bullets:
            continue
        # Keep the URL + bullets for final synthesis.
        source_summaries.append({"url": url, "bullets": bullets})

    # If extraction failed for all sources, synthesize from search metadata.
    if not source_summaries:
        paragraph, sources = synthesize_from_search_results(results, query)
    else:
        # Otherwise, synthesize a paragraph from the extracted bullet summaries.
        paragraph, sources = synthesize_paragraph(
            source_summaries, min_sources=1, query=query, max_sentences=10
        )
    # Write the final output and return success.
    out_path = output_path(query)
    write_output(out_path, paragraph, sources)
    print(f"Saved to {out_path}")
    return 0


def main() -> int:
    # Accept a query from CLI args or prompt interactively.
    if len(sys.argv) < 2:
        query = input("Enter a topic to research: ").strip()
        if not query:
            # Provide usage guidance when no query is supplied.
            print('Usage: python main.py "your topic"')
            return 2
    else:
        # Join CLI args into a single query string.
        query = " ".join(sys.argv[1:]).strip()
    if not query:
        # Guard against empty queries.
        print("Empty query.")
        return 2
    # Run the main workflow and return its exit code.
    return run(query)


if __name__ == "__main__":
    # Standard CLI entry point.
    raise SystemExit(main())
