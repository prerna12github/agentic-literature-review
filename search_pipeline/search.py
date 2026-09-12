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
  
    params = {
        "query": query,
        "limit": limit,
        "fields": FIELDS,
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
            log.warning(
                "Network error (attempt %d/%d): %s",
                attempt, MAX_RETRIES, e,
            )
            response = None

        if response is not None and response.status_code != 429:
            break  

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

        if min_year and (year is None or year < min_year):
            continue

        ext_ids = item.get("externalIds") or {}

        papers.append({
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
            "local_pdf_path": None,
            "pdf_status": "not_attempted",
            "pdf_source": None,
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