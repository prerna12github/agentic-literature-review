"""
search.py — Search Semantic Scholar for papers matching a research question.

Fixes/improvements in this version:
- Network errors (ConnectionError, Timeout) are retried, not fatal
- Honors Retry-After header on 429, with capped exponential backoff
- Captures paperId, DOI, and arXiv ID (needed for download fallbacks + citations)
- min_year now also excludes papers with unknown year
- Papers without an abstract are kept but tagged (Filter Agent will rank them low)
"""

import os
import time
import logging

import requests
from dotenv import load_dotenv

load_dotenv()

log = logging.getLogger(__name__)

SEMANTIC_SCHOLAR_API = (
    "https://api.semanticscholar.org/graph/v1/paper/search"
)

# paperId + externalIds added: needed for citation traceability
# (Step 5) and for the Unpaywall / arXiv download fallbacks.
FIELDS = (
    "title,abstract,year,authors,url,openAccessPdf,"
    "citationCount,paperId,externalIds"
)

API_KEY = os.environ.get("S2_API_KEY")

MAX_RETRIES = 5
INITIAL_WAIT_SECONDS = 8
MAX_WAIT_SECONDS = 60


def search_papers(
    query: str,
    limit: int = 30,
    min_year: int = None,
) -> list[dict]:
    """
    Search Semantic Scholar and return a clean list of paper dicts.

    Args:
        query: research question / topic
        limit: how many candidate papers to fetch (oversample this:
               expect 30-50% to be lost at the download stage)
        min_year: skip papers published before this year.
                  Papers with an unknown year are also skipped
                  (safer than letting them through unfiltered).
    """

    params = {
        "query": query,
        "limit": limit,
        "fields": FIELDS,
        # Only ask for papers S2 believes have an open-access PDF.
        # The download fallback chain still exists for dead URLs.
        "openAccessPdf": "",
    }

    headers = {"x-api-key": API_KEY} if API_KEY else {}

    response = None
    wait_seconds = INITIAL_WAIT_SECONDS

    for attempt in range(1, MAX_RETRIES + 1):
        try:
            response = requests.get(
                SEMANTIC_SCHOLAR_API,
                params=params,
                headers=headers,
                timeout=15,
            )
        except requests.RequestException as e:
            # NEW: network failures retry too, instead of crashing
            log.warning(
                "Network error (attempt %d/%d): %s",
                attempt, MAX_RETRIES, e,
            )
            response = None

        if response is not None and response.status_code != 429:
            break  # got a real answer (good or bad) — stop retrying

        # NEW: honor the server's Retry-After hint when present
        retry_after = None
        if response is not None:
            retry_after = response.headers.get("Retry-After")

        sleep_for = (
            min(int(retry_after), MAX_WAIT_SECONDS)
            if retry_after and retry_after.isdigit()
            else wait_seconds
        )

        log.info(
            "Rate limited (attempt %d/%d), waiting %ds before retrying...",
            attempt, MAX_RETRIES, sleep_for,
        )
        time.sleep(sleep_for)

        # exponential backoff, capped
        wait_seconds = min(wait_seconds * 2, MAX_WAIT_SECONDS)

    if response is None:
        raise ConnectionError(
            f"Could not reach Semantic Scholar after {MAX_RETRIES} attempts."
        )

    response.raise_for_status()

    data = response.json()
    papers = []

    for item in data.get("data", []):
        year = item.get("year")

        # FIXED: papers with no year are now excluded too when min_year is set
        if min_year and (year is None or year < min_year):
            continue

        ext_ids = item.get("externalIds") or {}

        papers.append({
            # NEW: stable IDs — required for fallback downloads and citations
            "paper_id": item.get("paperId"),
            "doi": ext_ids.get("DOI"),
            "arxiv_id": ext_ids.get("ArXiv"),

            "title": item.get("title"),
            "abstract": item.get("abstract"),
            "year": year,
            "authors": [
                a.get("name") for a in item.get("authors", [])
            ],
            "url": item.get("url"),
            "open_access_pdf": (item.get("openAccessPdf") or {}).get("url"),
            "citation_count": item.get("citationCount", 0),

            # NEW: filled in by download.py later
            "local_pdf_path": None,
            "pdf_status": "not_attempted",
            "pdf_source": None,

            # NEW: tag papers with no abstract — Filter Agent (Step 2)
            # will rank these low since it works from title + abstract
            "no_abstract": item.get("abstract") is None,
        })

    return papers


if __name__ == "__main__":
    logging.basicConfig(level=logging.INFO, format="%(message)s")

    results = search_papers(
        "RAG hallucination mitigation detection",
        limit=10,
    )

    for i, p in enumerate(results, 1):
        print(f"\n[{i}] {p['title']} ({p['year']})")
        print(f"    Citations: {p['citation_count']}")
        print(f"    PDF available: {'Yes' if p['open_access_pdf'] else 'No'}")
        print(f"    PDF URL: {p['open_access_pdf']}")
        print(f"    paperId: {p['paper_id']}")