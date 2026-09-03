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
from search_pipeline.download import download_all
from search_pipeline.extract import extract_for_paper


def run_pipeline(query: str, limit: int = 5, save_dir: str = "papers", output_file: str = "results.json"):
    print(f"\n=== Step 1: Searching for papers on: '{query}' ===")
    papers = search_papers(query, limit=limit)
    print(f"Found {len(papers)} papers.\n")

    print("=== Step 2: Downloading open-access PDFs ===")
    papers = download_all(papers, save_dir=save_dir)

    print("\n=== Step 3: Extracting text (with page tracking) ===")
    for paper in papers:
        paper = extract_for_paper(paper)
        print(f"  '{paper['title']}': {len(paper['chunks'])} chunks")

    # Save everything to a JSON file so later steps (Reader Agent, etc.)
    # can just load this instead of re-searching/downloading.
    with open(output_file, "w") as f:
        json.dump(papers, f, indent=2)

    print(f"\nSaved results to {output_file}")

    # quick summary
    with_pdf = sum(1 for p in papers if p["local_pdf_path"])
    total_chunks = sum(len(p["chunks"]) for p in papers)
    print(f"\nSummary: {len(papers)} papers found, {with_pdf} PDFs downloaded, {total_chunks} text chunks extracted.")

    return papers


if __name__ == "__main__":
    if len(sys.argv) < 2:
        print('Usage: python main.py "your research question"')
        sys.exit(1)

    query = " ".join(sys.argv[1:])
    run_pipeline(query)