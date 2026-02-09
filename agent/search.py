# Environment variables for API keys, typing helpers, and URL parsing.
import os
from typing import List, Dict
from urllib.parse import parse_qs, unquote, urlparse

# HTTP client and search/HTML parsing helpers.
import requests
from duckduckgo_search import DDGS
from bs4 import BeautifulSoup

# URL normalization and domain scoring utilities.
from .utils import canonicalize_url, domain_from_url, score_domain


def _collect_results(query: str, max_results: int, backend: str) -> List[Dict[str, str]]:
    # Primary DDG search via the duckduckgo_search library.
    results: List[Dict[str, str]] = []
    seen = set()

    with DDGS() as ddgs:
        for r in ddgs.text(query, max_results=max_results, backend=backend):
            # Normalize and validate URLs before storing.
            url = r.get("href") or r.get("url") or ""
            if not url.startswith("http"):
                continue
            url = canonicalize_url(url)
            if url in seen:
                continue
            seen.add(url)
            # Capture metadata needed for summarization and ranking.
            title = r.get("title") or ""
            snippet = r.get("body") or ""
            domain = domain_from_url(url)
            results.append(
                {
                    "url": url,
                    "title": title,
                    "snippet": snippet,
                    "domain": domain,
                    "score": score_domain(domain),
                }
            )

    return results


def _decode_ddg_url(raw_url: str) -> str:
    # Decode DDG redirect links to the final destination URL.
    if not raw_url:
        return ""
    if raw_url.startswith("/l/") or "duckduckgo.com/l/" in raw_url:
        parsed = urlparse(raw_url)
        params = parse_qs(parsed.query)
        uddg = params.get("uddg", [""])[0]
        if uddg:
            return unquote(uddg)
    return raw_url


def _ddg_html_search(query: str, max_results: int = 10) -> List[Dict[str, str]]:
    # Fallback search by scraping DDG HTML endpoints.
    results: List[Dict[str, str]] = []
    seen = set()
    headers = {
        "User-Agent": (
            "Mozilla/5.0 (Macintosh; Intel Mac OS X 10_15_7) "
            "AppleWebKit/537.36 (KHTML, like Gecko) "
            "Chrome/120.0.0.0 Safari/537.36"
        ),
        "Accept-Language": "en-US,en;q=0.9",
    }
    endpoints = [
        ("https://duckduckgo.com/html/", "post"),
        ("https://html.duckduckgo.com/html/", "post"),
        ("https://duckduckgo.com/html/", "get"),
    ]

    for url, method in endpoints:
        try:
            # Try multiple endpoints and methods to maximize reliability.
            if method == "post":
                resp = requests.post(url, data={"q": query}, headers=headers, timeout=15)
            else:
                resp = requests.get(url, params={"q": query}, headers=headers, timeout=15)
            resp.raise_for_status()
            # Parse the HTML search results and extract links.
            soup = BeautifulSoup(resp.text, "lxml")
            for a in soup.select("a.result__a"):
                href = a.get("href") or ""
                title = a.get_text(strip=True) or ""
                href = _decode_ddg_url(href)
                if not href.startswith("http"):
                    continue
                href = canonicalize_url(href)
                if href in seen:
                    continue
                seen.add(href)
                domain = domain_from_url(href)
                snippet = ""
                results.append(
                    {
                        "url": href,
                        "title": title,
                        "snippet": snippet,
                        "domain": domain,
                        "score": score_domain(domain),
                    }
                )
                if len(results) >= max_results:
                    return results
            if results:
                return results
        except Exception:
            # Move to the next endpoint if this one fails.
            continue
    return results


def _ddg_lite_search(query: str, max_results: int = 10) -> List[Dict[str, str]]:
    # Additional fallback using the DDG lite UI.
    results: List[Dict[str, str]] = []
    seen = set()
    headers = {
        "User-Agent": (
            "Mozilla/5.0 (Macintosh; Intel Mac OS X 10_15_7) "
            "AppleWebKit/537.36 (KHTML, like Gecko) "
            "Chrome/120.0.0.0 Safari/537.36"
        ),
        "Accept-Language": "en-US,en;q=0.9",
    }
    try:
        # Request the lite interface and parse its links.
        resp = requests.get(
            "https://duckduckgo.com/lite/",
            params={"q": query},
            headers=headers,
            timeout=15,
        )
        resp.raise_for_status()
        soup = BeautifulSoup(resp.text, "lxml")
        for a in soup.select("a.result-link"):
            href = a.get("href") or ""
            title = a.get_text(strip=True) or ""
            href = _decode_ddg_url(href)
            if not href.startswith("http"):
                continue
            href = canonicalize_url(href)
            if href in seen:
                continue
            seen.add(href)
            domain = domain_from_url(href)
            results.append(
                {
                    "url": href,
                    "title": title,
                    "snippet": "",
                    "domain": domain,
                    "score": score_domain(domain),
                }
            )
            if len(results) >= max_results:
                break
    except Exception:
        return results
    return results


def _wiki_search(query: str, max_results: int = 10) -> List[Dict[str, str]]:
    # Wikipedia API fallback for broad topics.
    results: List[Dict[str, str]] = []
    seen = set()
    params = {
        "action": "query",
        "list": "search",
        "srsearch": query,
        "srlimit": max_results,
        "format": "json",
    }
    try:
        # Use the MediaWiki search API.
        resp = requests.get(
            "https://en.wikipedia.org/w/api.php", params=params, timeout=10
        )
        resp.raise_for_status()
        data = resp.json()
    except Exception:
        return results

    for item in data.get("query", {}).get("search", []):
        # Convert titles into canonical article URLs.
        title = item.get("title") or ""
        if not title:
            continue
        url = f"https://en.wikipedia.org/wiki/{title.replace(' ', '_')}"
        url = canonicalize_url(url)
        if url in seen:
            continue
        seen.add(url)
        domain = domain_from_url(url)
        snippet = item.get("snippet") or ""
        results.append(
            {
                "url": url,
                "title": title,
                "snippet": snippet,
                "domain": domain,
                "score": score_domain(domain),
            }
        )
    return results


def _google_cse_search(query: str, max_results: int = 10) -> List[Dict[str, str]]:
    # Optional Google Custom Search fallback (requires env vars).
    api_key = os.getenv("GOOGLE_CSE_API_KEY") or os.getenv("GOOGLE_API_KEY")
    cse_id = os.getenv("GOOGLE_CSE_ID")
    if not api_key or not cse_id:
        return []

    results: List[Dict[str, str]] = []
    seen = set()
    start = 1
    while len(results) < max_results:
        # Google CSE uses a start index for pagination.
        params = {
            "key": api_key,
            "cx": cse_id,
            "q": query,
            "start": start,
        }
        try:
            # Call the CSE API and parse JSON results.
            resp = requests.get(
                "https://www.googleapis.com/customsearch/v1",
                params=params,
                timeout=15,
            )
            resp.raise_for_status()
            data = resp.json()
        except Exception:
            break

        items = data.get("items", [])
        if not items:
            break
        for item in items:
            # Extract URL metadata and score by domain.
            url = item.get("link") or ""
            if not url.startswith("http"):
                continue
            url = canonicalize_url(url)
            if url in seen:
                continue
            seen.add(url)
            title = item.get("title") or ""
            snippet = item.get("snippet") or ""
            domain = domain_from_url(url)
            results.append(
                {
                    "url": url,
                    "title": title,
                    "snippet": snippet,
                    "domain": domain,
                    "score": score_domain(domain),
                }
            )
            if len(results) >= max_results:
                break
        start += len(items)
        # Google CSE only supports a limited pagination window.
        if start > 91:
            break
    return results


def search_web(query: str, max_results: int = 15) -> List[Dict[str, str]]:
    # Try multiple backends in order of reliability.
    backends = ["api", "html", "lite"]
    last_error: Exception | None = None
    results: List[Dict[str, str]] = []

    for backend in backends:
        try:
            # Use the duckduckgo_search library first.
            results = _collect_results(query, max_results, backend)
            if results:
                break
        except Exception as e:
            last_error = e

    # If the primary backends fail, try Google CSE if configured.
    if not results:
        results = _google_cse_search(query, max_results=max_results)

    # Fall back to HTML scraping of DuckDuckGo.
    if not results:
        results = _ddg_html_search(query, max_results=max_results)

    # If HTML scraping fails, try the lite endpoint.
    if not results:
        results = _ddg_lite_search(query, max_results=max_results)

    # Final fallback: Wikipedia search.
    if not results:
        wiki_results = _wiki_search(query, max_results=max_results)
        if wiki_results:
            results = wiki_results
        elif last_error:
            print(f"Search failed: {last_error}")

    # Rank results by domain reputation score.
    results.sort(key=lambda x: x["score"], reverse=True)
    return results
