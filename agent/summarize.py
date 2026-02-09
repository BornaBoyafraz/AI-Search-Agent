# Regex utilities and typing helpers.
import re
from typing import Dict, List, Tuple


def _split_sentences(text: str) -> List[str]:
    # Normalize whitespace to make sentence splitting more reliable.
    text = re.sub(r"\s+", " ", text).strip()
    if not text:
        return []
    # Split on sentence-ending punctuation followed by whitespace.
    sentences = re.split(r"(?<=[.!?])\s+", text)
    # Filter out very short fragments.
    return [s.strip() for s in sentences if len(s.strip()) > 20]


def _clean_text(text: str) -> str:
    # Remove Wikipedia-style bracketed citations and collapse whitespace.
    text = re.sub(r"\[[^\]]+\]", "", text)
    text = re.sub(r"\s+", " ", text).strip()
    return text


def _score_sentence(sentence: str) -> int:
    # Heuristic scoring: prefer sentences with dates, numbers, and proper nouns.
    score = 0
    if re.search(r"\b\d{4}\b", sentence):
        score += 3
    if re.search(r"\b\d+(?:\.\d+)?%\b", sentence):
        score += 2
    if re.search(r"\b\d+(?:,\d{3})+\b", sentence):
        score += 2
    if re.search(r"\b[A-Z][a-z]+\b", sentence):
        score += 1
    return score


def source_bullets(text: str, max_bullets: int = 8) -> List[str]:
    # Select the best sentences to represent a source.
    sentences = _split_sentences(text)
    scored = sorted(sentences, key=_score_sentence, reverse=True)
    bullets = []
    seen = set()
    for s in scored:
        # Clean and de-duplicate sentences.
        s = _clean_text(s)
        if s in seen:
            continue
        seen.add(s)
        bullets.append(s)
        if len(bullets) >= max_bullets:
            break
    return bullets


def _detect_conflicts(source_summaries: List[Dict[str, object]]) -> List[str]:
    # Very conservative conflict detection based on keyword + number pairs.
    pattern = re.compile(
        r"\\b([A-Za-z][A-Za-z\\-]{3,})[^\\d]{0,10}(\\d{4}|\\d+(?:,\\d{3})+|\\d+%|\\d+\\.\\d+)\\b"
    )
    keyword_to_numbers: Dict[str, set] = {}
    for s in source_summaries:
        bullets = s.get("bullets", [])
        for b in bullets:
            for match in pattern.findall(b):
                keyword = match[0].lower()
                number = match[1]
                keyword_to_numbers.setdefault(keyword, set()).add(number)

    # Flag keywords that appear with multiple different numbers.
    conflicts = [k for k, nums in keyword_to_numbers.items() if len(nums) > 1]
    return conflicts[:2]


def synthesize_paragraph(
    source_summaries: List[Dict[str, object]],
    min_sources: int = 2,
    query: str | None = None,
    max_sentences: int = 8,
) -> Tuple[str, List[str]]:
    # Build a paragraph from bullet summaries and return sources used.
    all_sentences: List[str] = []
    sources_used: List[str] = []

    for s in source_summaries:
        bullets = s.get("bullets", [])
        if not bullets:
            continue
        sources_used.append(s["url"])
        all_sentences.extend(bullets)

    # De-duplicate sentences while preserving order
    seen = set()
    unique_sentences = []
    for s in all_sentences:
        s = _clean_text(s)
        if s in seen:
            continue
        seen.add(s)
        unique_sentences.append(s)

    # If we have too few sources or sentences, return a fallback paragraph.
    if len(sources_used) < min_sources or len(unique_sentences) < 1:
        paragraph = (
            "Not enough high-quality sources were accessible to produce a reliable summary. "
            "This can happen when pages block automated access, restrict content via robots.txt, "
            "or contain too little extractable text."
        )
        return paragraph, sources_used

    # Use more strong sentences to form a longer single paragraph.
    prefix = f"About {query}, " if query else ""
    paragraph = prefix + " ".join(unique_sentences[:max_sentences])
    # Append a brief note if numeric conflicts are detected.
    conflicts = _detect_conflicts(source_summaries)
    if conflicts:
        paragraph += (
            " Sources report differing figures for "
            + ", ".join(conflicts)
            + "."
        )
    return paragraph, sources_used


def synthesize_from_search_results(
    results: List[Dict[str, str]],
    query: str,
    max_items: int = 3,
) -> Tuple[str, List[str]]:
    # Build a summary from search snippets when full text is unavailable.
    snippets: List[str] = []
    sources: List[str] = []
    for r in results:
        url = r.get("url") or ""
        title = r.get("title") or ""
        snippet = r.get("snippet") or ""
        text = snippet.strip() or title.strip()
        text = _clean_text(text)
        if not text or url in sources:
            continue
        snippets.append(text)
        sources.append(url)
        if len(snippets) >= max_items:
            break
    if not snippets:
        paragraph = (
            f"No accessible sources were found for {query}, "
            "and search snippets were unavailable."
        )
        return paragraph, sources
    # Combine snippets into a short paragraph.
    paragraph = f"About {query}, search results indicate: " + " ".join(snippets)
    return paragraph, sources
