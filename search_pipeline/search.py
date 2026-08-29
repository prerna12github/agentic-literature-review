import requests
import time

SEMANTIC_SCHOLAR_API = "https://api.semanticscholar.org/graph/v1/paper/search"

# Fields we want back from the API for each paper
FIELDS = "title,abstract,year,authors,url,openAccessPdf,citationCount"


def search_papers(query: str, limit: int = 10, min_year: int = None) -> list[dict]:
  
    params = {
        "query": query,
        "limit": limit,
        "fields": FIELDS,
    }

    response = requests.get(SEMANTIC_SCHOLAR_API, params=params, timeout=15)

    if response.status_code == 429:
        # Semantic Scholar free tier rate-limits aggressively — back off and retry once
        print("Rate limited, waiting 5s and retrying...")
        time.sleep(5)
        response = requests.get(SEMANTIC_SCHOLAR_API, params=params, timeout=15)

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