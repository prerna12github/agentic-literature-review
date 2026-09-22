import sys
import json
import os

from search_pipeline.search import search_papers
from search_pipeline.download import download_until_target   # FIXED: correct import
from search_pipeline.extract import extract_for_paper

OUTPUT_FILE = "results.json"


def run_pipeline(query: str, target_papers: int = 10, save_dir: str = "papers") -> list[dict]:
    print(f"\n=== Step 1: Searching for papers on: '{query}' ===")
    papers = search_papers(query, limit=target_papers * 3)

    if not papers:
        print("No papers found for this query. Try rephrasing it.")
        return []

    print(f"Found {len(papers)} candidate papers.\n")

    print(f"=== Step 2: Downloading open-access PDFs (target: {target_papers}) ===")
    papers = download_until_target(papers, target=target_papers, save_dir=save_dir)

    print("\n=== Step 3: Extracting text (with page tracking) ===")
    for paper in papers:
        extract_for_paper(paper)
        print(f"  '{paper['title']}': {len(paper['chunks'])} chunks")

    n_downloaded = sum(1 for p in papers if p["pdf_status"] == "downloaded")
    n_abstract_only = sum(1 for p in papers if p["pdf_status"] == "abstract_only")
    n_spare = sum(1 for p in papers if p["pdf_status"] == "not_attempted")
    total_chunks = sum(len(p["chunks"]) for p in papers)

    output = {
        "query": query,
        "stats": {
            "candidates_found": len(papers),
            "pdfs_downloaded": n_downloaded,
            "abstract_only": n_abstract_only,
            "spare_candidates": n_spare,
            "total_chunks": total_chunks,
        },
        "papers": papers,
    }

    with open(OUTPUT_FILE, "w") as f:
        json.dump(output, f, ensure_ascii=False, indent=2)   

    print(f"\nSaved results to {OUTPUT_FILE}")

    print(
        f"\nSummary: {len(papers)} candidates | {n_downloaded} PDFs downloaded | "
        f"{n_abstract_only} abstract-only | {n_spare} spares | {total_chunks} chunks extracted."
    )

    return papers


if __name__ == "__main__":
    if len(sys.argv) < 2:
        print('Usage: python main.py "your research question"')
        sys.exit(1)

    query = " ".join(sys.argv[1:])
    run_pipeline(query)