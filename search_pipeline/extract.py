"""
extract.py — Extract page-tagged text chunks from downloaded PDFs.

Fixes/improvements in this version:
- Context manager ensures the PDF is closed even if extraction errors
- Each chunk gets a unique chunk_id + the paper's title/ID embedded,
  so chunks stay traceable after LangGraph moves them around (Steps 2-5)
"""

import os
import logging

import pymupdf

log = logging.getLogger(__name__)


def extract_chunks(pdf_path: str, min_chunk_length: int = 40) -> list[dict]:
    """
    Extract text from a PDF, split into paragraph-level chunks,
    each tagged with its page number.

    Args:
        pdf_path: path to a local PDF file
        min_chunk_length: skip tiny fragments (headers, page numbers, etc.)

    Returns:
        List of dicts: [{"page": 1, "text": "...", "chunk_id": "..."}, ...]
    """
    if not os.path.exists(pdf_path):
        raise FileNotFoundError(pdf_path)

    chunks = []

    # FIXED: context manager guarantees doc.close() even on errors
    with pymupdf.open(pdf_path) as doc:
        for page_number, page in enumerate(doc, start=1):
            text = page.get_text()

            # split page text into paragraphs on blank lines
            paragraphs = [p.strip() for p in text.split("\n\n") if p.strip()]

            for para in paragraphs:
                # collapse internal newlines (PDFs break lines mid-sentence)
                clean_para = " ".join(para.split())

                if len(clean_para) >= min_chunk_length:
                    chunks.append({
                        "page": page_number,
                        "text": clean_para,
                    })

    return chunks


def extract_for_paper(paper: dict) -> dict:
    """
    Convenience wrapper: takes a paper dict (with 'local_pdf_path' set by
    download.py) and attaches extracted chunks with full traceability info.
    """
    pdf_path = paper.get("local_pdf_path")

    # Papers kept as 'abstract_only' (no PDF found) — nothing to extract
    if not pdf_path:
        paper["chunks"] = []
        return paper

    try:
        raw_chunks = extract_chunks(pdf_path)

        # NEW: make each chunk self-contained. After Steps 2-5 shuffle
        # data through LangGraph nodes, each chunk must carry its own
        # provenance — this is what makes the Writer Agent's citations
        # traceable to an exact page of an exact paper.
        paper_id = paper.get("paper_id") or "unknown-id"
        short_title = (paper.get("title") or "untitled")[:80]

        paper["chunks"] = [
            {
                "chunk_id": f"{paper_id}:p{c['page']}:{i}",
                "page": c["page"],
                "text": c["text"],
                "paper_id": paper_id,
                "paper_title": short_title,
            }
            for i, c in enumerate(raw_chunks)
        ]

    except Exception as e:
        log.info(
            "  Failed to extract text from '%s': %s",
            paper.get("title"), e,
        )
        paper["chunks"] = []

    return paper


if __name__ == "__main__":
    logging.basicConfig(level=logging.INFO, format="%(message)s")

    from search import search_papers
    from download import download_until_target

    results = search_papers("retrieval augmented generation hallucination", limit=10)
    results = download_until_target(results, target=3)

    for paper in results:
        paper = extract_for_paper(paper)
        print(f"\n{paper['title']}: {len(paper['chunks'])} chunks extracted")
        if paper["chunks"]:
            first = paper["chunks"][0]
            print(f"  Example chunk (page {first['page']}, id {first['chunk_id']}):")
            print(f"  \"{first['text'][:150]}...\"")