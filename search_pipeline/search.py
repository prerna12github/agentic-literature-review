"""
Step 1a: Search Agent
----------------------
Takes a research question / topic and searches Semantic Scholar
(a free, no-API-key-required academic search engine) for relevant papers.

Returns a clean list of paper dicts with: title, abstract, year, authors,
url, and open-access PDF link (if available).
"""

import requests
import time
import os

SEMANTIC_SCHOLAR_API = "https://api.semanticscholar.org/graph/v1/paper/search"

# Fields we want back from the API for each paper
FIELDS = "title,abstract,year,authors,url,openAccessPdf,citationCount"

# Optional: if you set an S2_API_KEY environment variable, requests get a much
# higher rate limit (Semantic Scholar's free API key is instant to get at
# https://www.semanticscholar.org/product/api#api-key — no cost, just an email form).
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

    # Semantic Scholar's unauthenticated tier is shared across everyone hitting it
    # globally, so 429 (rate limited) happens often and a single short wait is
    # rarely enough. We retry with "exponential backoff" — each wait is longer
    # than the last (5s, 10s, 20s, 40s...) since the limit usually clears within
    # a minute or so.
    max_retries = 5
    wait_seconds = 5
    headers = {"x-api-key": API_KEY} if API_KEY else {}

    for attempt in range(max_retries):
        response = requests.get(SEMANTIC_SCHOLAR_API, params=params, headers=headers, timeout=15)

        if response.status_code != 429:
            break  # success, or a different error we'll raise below

        print(f"Rate limited (attempt {attempt + 1}/{max_retries}), "
              f"waiting {wait_seconds}s...")
        time.sleep(wait_seconds)
        wait_seconds *= 2  # double the wait each time

    response.raise_for_status()
    data = response.json()

    papers = []
    for item in data.get("data", []):
        if min_year and item.get("year") and item["year"] < min_year:
            continue

        papers.append({
            "title": item.get("title"),
            "abstract": item.get("abstract"),
            "year": item.get("year"),
            "authors": [a.get("name") for a in item.get("authors", [])],
            "url": item.get("url"),
            "open_access_pdf": (item.get("openAccessPdf") or {}).get("url"),
            "citation_count": item.get("citationCount", 0),
        })

    return papers


if __name__ == "__main__":
    # quick manual test
    results = search_papers("retrieval augmented generation hallucination", limit=5)
    for i, p in enumerate(results, 1):
        print(f"\n[{i}] {p['title']} ({p['year']})")
        print(f"    Citations: {p['citation_count']}")
        print(f"    PDF available: {'Yes' if p['open_access_pdf'] else 'No'}")