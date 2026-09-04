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

SEMANTIC_SCHOLAR_API = "https://api.semanticscholar.org/graph/v1/paper/search"

# Fields we want back from the API for each paper
FIELDS = "title,abstract,year,authors,url,openAccessPdf,citationCount"


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

    # Semantic Scholar's free, no-login tier shares its rate limit across
    # everyone using it worldwide, so 429 ("too many requests") happens often.
    # We retry with "exponential backoff" — each wait is longer than the last
    # (8s, 16s, 32s, 64s, 128s) since the shared limit usually clears within
    # a couple of minutes.
    max_retries = 5
    wait_seconds = 8

    for attempt in range(max_retries):
        response = requests.get(SEMANTIC_SCHOLAR_API, params=params, timeout=15)

        if response.status_code != 429:
            break  # success, or a different error we'll raise below

        print(f"Rate limited (attempt {attempt + 1}/{max_retries}), "
              f"waiting {wait_seconds}s before retrying...")
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