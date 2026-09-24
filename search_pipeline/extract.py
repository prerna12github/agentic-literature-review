import os
import logging

import pymupdf

log = logging.getLogger(__name__)


def extract_chunks(pdf_path: str, min_chunk_length: int = 40) -> list[dict]:

    if not os.path.exists(pdf_path):
        raise FileNotFoundError(pdf_path)

    chunks = []

    with pymupdf.open(pdf_path) as doc:
        for page_number, page in enumerate(doc, start=1):
            text = page.get_text()

            paragraphs = [p.strip() for p in text.split("\n\n") if p.strip()]

            for para in paragraphs:
                clean_para = " ".join(para.split())

                if len(clean_para) >= min_chunk_length:
                    chunks.append({
                        "page": page_number,
                        "text": clean_para,
                    })

    return chunks


def extract_for_paper(paper: dict) -> dict:

    pdf_path = paper.get("local_pdf_path")

    if not pdf_path:
        paper["chunks"] = []
        return paper

    try:
        raw_chunks = extract_chunks(pdf_path)
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