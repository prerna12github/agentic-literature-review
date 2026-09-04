"""
Step 1a: Search Agent
----------------------
Takes a research question / topic and searches Semantic Scholar
(a free, no-API-key-required academic search engine) for relevant papers.

Returns a clean list of paper dicts with: title, abstract, year, authors,
url, and open-access PDF link (if available).
"""

import os
import time

import requests
from dotenv import load_dotenv

load_dotenv()  # reads a .env file in the project folder (if present) into os.environ

SEMANTIC_SCHOLAR_API = "https://api.semanticscholar.org/graph/v1/paper/search"

# Fields we want back from the API for each paper
FIELDS = "title,abstract,year,authors,url,openAccessPdf,citationCount"

# If you have a Semantic Scholar API key, put it in a .env file in the project
# root as: S2_API_KEY=your-key-here
# (or export it in your shell — either way works, load_dotenv() above handles the .env case)
API_KEY = os.environ.get("S2_API_KEY")


def search_papers(query: str, limit: int = 10, min_year: int = None) -> list[dict]:
    """
    Search Semantic Scholar for papers matching `query`.

    Args:
        query: research question or topic, e.g. "transformer long context handling"
        limit: max number of papers to return
        min_year: optional, only return papers published in/after this year

    Returns:
        List of dicts, one per paper.
    """
    params = {
        "query": query,
        "limit": limit,
        "fields": FIELDS,
    }

    # With an API key, rate limits are per-key instead of shared globally, so
    # 429s should be rare — but we keep the backoff retry as a safety net.
    max_retries = 5
    wait_seconds = 8
    headers = {"x-api-key": API_KEY} if API_KEY else {}

    for attempt in range(max_retries):
        response = requests.get(
            SEMANTIC_SCHOLAR_API, params=params, headers=headers, timeout=15
        )

        if response.status_code != 429:
            break  # success, or a different error we'll raise below

        print(
            f"Rate limited (attempt {attempt + 1}/{max_retries}), "
            f"waiting {wait_seconds}s before retrying..."
        )
        time.sleep(wait_seconds)
        wait_seconds *= 2  # double the wait each time

    response.raise_for_status()
    data = response.json()

    papers = []
    for item in data.get("data", []):
        if min_year and item.get("year") and item["year"] < min_year:
            continue

        papers.append(
            {
                "title": item.get("title"),
                "abstract": item.get("abstract"),
                "year": item.get("year"),
                "authors": [a.get("name") for a in item.get("authors", [])],
                "url": item.get("url"),
                "open_access_pdf": (item.get("openAccessPdf") or {}).get("url"),
                "citation_count": item.get("citationCount", 0),
            }
        )

    return papers


if __name__ == "__main__":
    # quick manual test
    results = search_papers("quantum computing", limit=5)
    for i, p in enumerate(results, 1):
        print(f"\n[{i}] {p['title']} ({p['year']})")
        print(f"    Citations: {p['citation_count']}")
        print(f"    PDF available: {'Yes' if p['open_access_pdf'] else 'No'}")
