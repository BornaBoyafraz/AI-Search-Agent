# Hashing for cache keys, regex helpers, date for filenames, path and URL utilities.
import hashlib
import re
from datetime import date
from pathlib import Path
from urllib.parse import urlparse, urlunparse

# Shared browser-like user agent string for HTTP requests.
USER_AGENT = (
    "Mozilla/5.0 (Macintosh; Intel Mac OS X 10_15_7) "
    "AppleWebKit/537.36 (KHTML, like Gecko) "
    "Chrome/120.0.0.0 Safari/537.36"
)

# Domains considered reputable for scoring search results.
REPUTABLE_DOMAINS = {
    "reuters.com",
    "apnews.com",
    "bbc.com",
    "bbc.co.uk",
    "nytimes.com",
    "wsj.com",
    "theguardian.com",
    "npr.org",
    "pbs.org",
    "nature.com",
    "science.org",
    "who.int",
    "cdc.gov",
    "nih.gov",
    "un.org",
    "worldbank.org",
    "oecd.org",
    "europa.eu",
    "wikipedia.org",
    "britannica.com",
}


def today_str() -> str:
    # ISO date string used in output filenames.
    return date.today().isoformat()


def sanitize_filename(text: str) -> str:
    # Normalize topic text into a safe filename.
    text = text.strip().lower()
    text = re.sub(r"[^a-z0-9\-\s_]", "", text)
    text = re.sub(r"[\s_]+", "_", text)
    return text[:80] if text else "topic"


def ensure_dir(path: Path) -> None:
    # Create directories if they don't already exist.
    path.mkdir(parents=True, exist_ok=True)


def canonicalize_url(url: str) -> str:
    # Normalize URLs to reduce duplicate variations.
    parsed = urlparse(url)
    scheme = parsed.scheme or "http"
    netloc = parsed.netloc.lower()
    path = parsed.path or "/"
    return urlunparse((scheme, netloc, path, "", parsed.query, ""))


def url_to_cache_key(url: str) -> str:
    # Stable cache key based on URL content.
    return hashlib.sha256(url.encode("utf-8")).hexdigest()


def domain_from_url(url: str) -> str:
    # Extract a normalized domain from a URL.
    return urlparse(url).netloc.lower()


def is_reputable_domain(domain: str) -> bool:
    # Mark .gov/.edu and known outlets as reputable.
    if domain.endswith(".gov") or domain.endswith(".edu"):
        return True
    for d in REPUTABLE_DOMAINS:
        if domain == d or domain.endswith("." + d):
            return True
    return False


def score_domain(domain: str) -> int:
    # Simple heuristic to rank domains by trustworthiness.
    score = 0
    if domain.endswith(".gov"):
        score += 5
    if domain.endswith(".edu"):
        score += 4
    if is_reputable_domain(domain):
        score += 3
    if any(domain.endswith(tld) for tld in [".org", ".int"]):
        score += 1
    return score


def output_path(topic: str) -> Path:
    # Output files are named by topic and current date.
    name = f"{sanitize_filename(topic)}_{today_str()}.txt"
    return Path("output") / name
