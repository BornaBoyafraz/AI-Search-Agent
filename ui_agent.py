from __future__ import annotations

from agent.engine import SearchEngine
from agent.models import SearchSettings

from models import AgentResponse, ResultItem


DEFAULT_SETTINGS = SearchSettings(max_results=10, safe_search=True, provider="auto")



def run_agent_response(query: str) -> AgentResponse:
    """Return a structured response for the desktop UI without writing files."""
    normalized_query = query.strip()
    if not normalized_query:
        raise ValueError("Please enter a query before sending.")

    engine = SearchEngine(cache_dir=None)
    response = engine.run(normalized_query, settings=DEFAULT_SETTINGS)

    if response.error and not response.results:
        raise RuntimeError(
            "I couldn't find enough accessible sources right now. "
            "Please try a broader query or retry in a moment."
        )

    # Show a result list when multiple search results are available.
    if len(response.results) > 1:
        items = [
            ResultItem(
                title=(item.title or "Untitled result").strip(),
                url=item.url,
                snippet=(item.snippet or "No snippet available.").strip(),
            )
            for item in response.results[:8]
            if item.url
        ]
        if items:
            return AgentResponse(results=items)

    answer = (response.summary or "").strip()
    if not answer and response.results:
        first = response.results[0]
        answer = (first.snippet or first.title or "No answer was generated.").strip()

    if not answer:
        answer = "No answer was generated. Please try another query."

    return AgentResponse(answer=answer)



def run_agent(query: str) -> str:
    """Returns the final answer text for the UI."""
    response = run_agent_response(query)
    if response.answer:
        return response.answer

    lines = []
    for index, item in enumerate(response.results, start=1):
        lines.append(f"{index}. {item.title}\n{item.snippet}\n{item.url}")
    return "\n\n".join(lines)
