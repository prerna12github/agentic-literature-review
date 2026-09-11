"""
Step 1: Full pipeline runner
------------------------------
Search -> Download -> Extract (with page-tracked chunks)

This is NOT the agent yet (no LLM calls, no reasoning). It's the
"plumbing" layer that later agent steps (Filter, Reader, Contradiction,
Writer) will build on top of.

Usage:
    python main.py "your research question here"
"""

import sys
import json
import os

from search_pipeline.search import search_papers
from search_pipeline.download import download_until_target   # FIXED: correct import
from search_pipeline.extract import extract_for_paper

OUTPUT_FILE = "results.json"


def run_pipeline(query: str, target_papers: int = 10, save_dir: str = "papers") -> list[dict]:
    # --- Step 1: search (oversample 3x to survive download losses) ---
    print(f"\n=== Step 1: Searching for papers on: '{query}' ===")
    papers = search_papers(query, limit=target_papers * 3)

    if not papers:
        print("No papers found for this query. Try rephrasing it.")
        return []

    print(f"Found {len(papers)} candidate papers.\n")

    # --- Step 2: download until target count ---
    print(f"=== Step 2: Downloading open-access PDFs (target: {target_papers}) ===")
    papers = download_until_target(papers, target=target_papers, save_dir=save_dir)

    # --- Step 3: extract page-tagged chunks ---
    print("\n=== Step 3: Extracting text (with page tracking) ===")
    for paper in papers:
        extract_for_paper(paper)
        print(f"  '{paper['title']}': {len(paper['chunks'])} chunks")

    # --- Build a self-describing stats block for Step 2 (Filter Agent) ---
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

    # --- Save everything so later steps can just load this file ---
    with open(OUTPUT_FILE, "w") as f:
        json.dump(output, f, ensure_ascii=False, indent=2)   # FIXED: dump `output`

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