"""
Step 1c: Extract text from PDFs (with page tracking)
--------------------------------------------------------
This is the piece that makes citation traceability possible later on.

Instead of just dumping "all the text" from a PDF, we break it into
paragraph-sized chunks and remember EXACTLY which page each chunk came
from. Later, when the Reader Agent pulls out a claim, we can say
"this came from page 4" instead of just "this paper said so".
"""

import pymupdf  # this is the new import name for the library formerly called `fitz`
import os


def extract_chunks(pdf_path: str, min_chunk_length: int = 40) -> list[dict]:
    """
    Extract text from a PDF, split into paragraph-level chunks,
    each tagged with its page number.

    Args:
        pdf_path: path to a local PDF file
        min_chunk_length: skip tiny fragments (headers, page numbers, etc.)

    Returns:
        List of dicts: [{"page": 1, "text": "..."}, {"page": 1, "text": "..."}, ...]
    """
    if not os.path.exists(pdf_path):
        raise FileNotFoundError(pdf_path)

    chunks = []
    doc = pymupdf.open(pdf_path)

    for page_number, page in enumerate(doc, start=1):
        text = page.get_text()

        # split page text into paragraphs on blank lines
        paragraphs = [p.strip() for p in text.split("\n\n") if p.strip()]

        for para in paragraphs:
            # collapse internal newlines (PDFs often break lines mid-sentence)
            clean_para = " ".join(para.split())

            if len(clean_para) >= min_chunk_length:
                chunks.append({
                    "page": page_number,
                    "text": clean_para,
                })

    doc.close()
    return chunks


def extract_for_paper(paper: dict) -> dict:
    """
    Convenience wrapper: takes a paper dict (with 'local_pdf_path' set by
    download.py) and attaches its extracted chunks to it.
    """
    pdf_path = paper.get("local_pdf_path")
    if not pdf_path:
        paper["chunks"] = []
        return paper

    try:
        paper["chunks"] = extract_chunks(pdf_path)
    except Exception as e:
        print(f"  Failed to extract text from '{paper['title']}': {e}")
        paper["chunks"] = []

    return paper


if __name__ == "__main__":
    from search import search_papers
    from download import download_all

    results = search_papers("retrieval augmented generation hallucination", limit=3)
    results = download_all(results)

    for paper in results:
        paper = extract_for_paper(paper)
        print(f"\n{paper['title']}: {len(paper['chunks'])} chunks extracted")
        if paper["chunks"]:
            print(f"  Example chunk (page {paper['chunks'][0]['page']}):")
            print(f"  \"{paper['chunks'][0]['text'][:150]}...\"")