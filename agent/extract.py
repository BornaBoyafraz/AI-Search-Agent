# Path for filesystem work and Optional for type hints.
from pathlib import Path
from typing import Optional

# HTML parsing and main-content extraction.
from bs4 import BeautifulSoup
from readability import Document

# Local helpers for caching.
from .utils import ensure_dir, url_to_cache_key


def extract_main_text(html: str) -> str:
    # Return empty string for empty input to avoid parsing errors.
    if not html:
        return ""
    try:
        # Use readability to isolate the main article content.
        doc = Document(html)
        content_html = doc.summary(html_partial=True)
        soup = BeautifulSoup(content_html, "lxml")
    except Exception:
        # Fall back to parsing the full document if readability fails.
        soup = BeautifulSoup(html, "lxml")

    # Remove non-content elements that add noise to summaries.
    for tag in soup(["script", "style", "noscript", "header", "footer", "nav", "aside"]):
        tag.decompose()

    # Extract visible text as a single whitespace-normalized string.
    text = soup.get_text(separator=" ", strip=True)
    return text


def cached_extract(url: str, html: str, cache_dir: Path | None = None) -> Optional[str]:
    text_path: Path | None = None
    if cache_dir is not None:
        # Ensure the cache directory exists for extracted text.
        ensure_dir(cache_dir / "text")
        cache_key = url_to_cache_key(url)
        text_path = cache_dir / "text" / f"{cache_key}.txt"

        # Reuse cached extraction if it already exists.
        if text_path.exists():
            return text_path.read_text(encoding="utf-8", errors="ignore")

    # Extract fresh text and cache it for future runs.
    text = extract_main_text(html)
    if text and text_path is not None:
        text_path.write_text(text, encoding="utf-8", errors="ignore")
    return text
