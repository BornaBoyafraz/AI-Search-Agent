# Time for polite delays, Path for cache paths, and typing helpers.
import time
from pathlib import Path
from typing import Optional, Tuple
from urllib.parse import urljoin, urlparse
from urllib.robotparser import RobotFileParser

# HTTP client.
import requests

# Shared constants and cache helpers.
from .utils import USER_AGENT, ensure_dir, url_to_cache_key


def _robots_url(url: str) -> str:
    # Build the robots.txt URL for a given page URL.
    parsed = urlparse(url)
    return urljoin(f"{parsed.scheme}://{parsed.netloc}", "/robots.txt")


def allowed_by_robots(url: str, user_agent: str = USER_AGENT, timeout: int = 10) -> bool:
    # Check robots.txt to respect site crawling rules.
    robots_url = _robots_url(url)
    rp = RobotFileParser()
    rp.set_url(robots_url)
    try:
        rp.read()
    except Exception:
        # If robots.txt can't be fetched, default to allow.
        # This avoids dropping all sources when robots is unreachable.
        return True
    # Ask the parser whether the user agent is allowed to fetch this URL.
    return rp.can_fetch(user_agent, url)


def fetch_url(url: str, cache_dir: Path | None = None) -> Tuple[Optional[str], Optional[str]]:
    html_path: Path | None = None
    if cache_dir is not None:
        # Ensure the cache directory exists for raw HTML.
        ensure_dir(cache_dir / "html")
        cache_key = url_to_cache_key(url)
        html_path = cache_dir / "html" / f"{cache_key}.html"

        # Serve cached HTML if available.
        if html_path.exists():
            return html_path.read_text(encoding="utf-8", errors="ignore"), "cached"

    # Use a realistic user agent to reduce blocks.
    headers = {"User-Agent": USER_AGENT}
    try:
        # Fetch the page with a timeout to avoid hanging.
        resp = requests.get(url, headers=headers, timeout=15)
    except requests.RequestException as e:
        return None, f"request_error: {e}"

    # Treat common block status codes as failures.
    if resp.status_code in (403, 429):
        return None, f"blocked_status: {resp.status_code}"
    if resp.status_code >= 400:
        return None, f"http_error: {resp.status_code}"

    # Cache the fetched HTML for reuse.
    text = resp.text
    if html_path is not None:
        html_path.write_text(text, encoding="utf-8", errors="ignore")
    # Small delay to be polite to servers.
    time.sleep(0.5)
    return text, "fetched"
