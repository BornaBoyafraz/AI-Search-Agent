# Research Agent (Free, Legal, Source-Based)

A minimal Python research agent that searches the web with DuckDuckGo, respects robots.txt, extracts main text, and synthesizes one factual paragraph with a Sources list.

## Features
- Free search via `duckduckgo_search`
- Respects `robots.txt` (skips disallowed pages)
- Requests + BeautifulSoup + readability-lxml for extraction
- Caching for raw HTML and extracted text
- One-paragraph summary + Sources list

## Setup (macOS)
1. `python3 -m venv .venv`
2. `source .venv/bin/activate`
3. `pip install -r requirements.txt`
4. `python main.py "your topic"` (if `python` is not found, use `python3`)
5. If you run `python main.py` without arguments, it will prompt you for a topic.

## Setup (Windows PowerShell)
1. `py -3.11 -m venv .venv`
2. `.venv\Scripts\Activate.ps1`
3. `pip install -r requirements.txt`
4. `python main.py "your topic"` (if `python` is not found, use `python3`)
5. If you run `python main.py` without arguments, it will prompt you for a topic.

## Usage
- `python main.py "your topic"`
- Output saved to `output/<sanitized_topic>_<YYYY-MM-DD>.txt`

## Project Structure
- `main.py` entry point
- `agent/search.py` search and ranking
- `agent/fetch.py` robots.txt and fetching
- `agent/extract.py` main-text extraction
- `agent/summarize.py` bullet summaries + one paragraph synthesis
- `agent/writeout.py` output file writing
- `agent/utils.py` helpers

## Notes & Troubleshooting
- If you get empty outputs, many pages may block automated access or be disallowed by robots.txt.
- Try broadening the query or using more general terms.
- The agent does not bypass paywalls, logins, or restricted content.
- If you see DNS or connectivity errors, ensure your environment has outbound internet access.
