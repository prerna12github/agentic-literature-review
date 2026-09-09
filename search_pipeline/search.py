import os
import time

import requests
from dotenv import load_dotenv

load_dotenv()

SEMANTIC_SCHOLAR_API = (
    "https://api.semanticscholar.org/graph/v1/paper/search"
)

FIELDS = (
    "title,abstract,year,authors,url,openAccessPdf,citationCount"
)

API_KEY = os.environ.get("S2_API_KEY")


def search_papers(
    query: str,
    limit: int = 10,
    min_year: int = None
) -> list[dict]:

    params = {
        "query": query,
        "limit": limit,
        "fields": FIELDS,

        # Ask Semantic Scholar to return papers
        # that have an open-access PDF.
        "openAccessPdf": "",
    }

    max_retries = 5
    wait_seconds = 8

    headers = {"x-api-key": API_KEY} if API_KEY else {}

    for attempt in range(max_retries):

        response = requests.get(
            SEMANTIC_SCHOLAR_API,
            params=params,
            headers=headers,
            timeout=15
        )

        if response.status_code != 429:
            break

        print(
            f"Rate limited (attempt {attempt + 1}/{max_retries}), "
            f"waiting {wait_seconds}s before retrying..."
        )

        time.sleep(wait_seconds)
        wait_seconds *= 2

    response.raise_for_status()

    data = response.json()

    papers = []

    for item in data.get("data", []):

        # Optional year filtering
        if (
            min_year
            and item.get("year")
            and item["year"] < min_year
        ):
            continue

        open_access_pdf = item.get("openAccessPdf") or {}

        papers.append(
            {
                "title": item.get("title"),
                "abstract": item.get("abstract"),
                "year": item.get("year"),

                "authors": [
                    a.get("name")
                    for a in item.get("authors", [])
                ],

                "url": item.get("url"),

                "open_access_pdf": open_access_pdf.get("url"),

                "citation_count": item.get(
                    "citationCount", 0
                ),
            }
        )

    return papers


if __name__ == "__main__":

    results = search_papers(
        "RAG hallucination mitigation detection",
        limit=5
    )

    for i, p in enumerate(results, 1):

        print(f"\n[{i}] {p['title']} ({p['year']})")

        print(
            f"    Citations: "
            f"{p['citation_count']}"
        )

        print(
            f"    PDF available: "
            f"{'Yes' if p['open_access_pdf'] else 'No'}"
        )

        print(
            f"    PDF URL: "
            f"{p['open_access_pdf']}"
        )