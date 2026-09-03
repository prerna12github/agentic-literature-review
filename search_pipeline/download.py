"""
Step 1b: Download open-access PDFs
------------------------------------
Given a paper dict from search.py (with an `open_access_pdf` url),
downloads the PDF to a local folder so it can be read/extracted later.

Papers with no open-access PDF are skipped (can't legally download those
without institutional access, so we just note them as "unavailable").
"""

import requests
import os
import re


def _safe_filename(title: str) -> str:
    """Turn a paper title into a safe filename."""
    name = re.sub(r"[^a-zA-Z0-9]+", "_", title.strip())
    return name[:80].strip("_") + ".pdf"


def download_pdf(paper: dict, save_dir: str = "papers") -> str | None:
    """
    Download a single paper's PDF if an open-access link exists.

    Args:
        paper: a paper dict from search.search_papers()
        save_dir: folder to save PDFs into

    Returns:
        Local file path if downloaded successfully, else None.
    """
    pdf_url = paper.get("open_access_pdf")
    if not pdf_url:
        return None

    os.makedirs(save_dir, exist_ok=True)
    filename = _safe_filename(paper["title"] or "untitled")
    filepath = os.path.join(save_dir, filename)

    try:
        response = requests.get(pdf_url, timeout=20, headers={"User-Agent": "Mozilla/5.0"})
        response.raise_for_status()

        # basic sanity check: make sure we actually got a PDF, not an HTML error page
        if not response.content.startswith(b"%PDF"):
            print(f"  Skipped (not a real PDF): {paper['title']}")
            return None

        with open(filepath, "wb") as f:
            f.write(response.content)

        return filepath

    except requests.RequestException as e:
        print(f"  Failed to download '{paper['title']}': {e}")
        return None


def download_all(papers: list[dict], save_dir: str = "papers") -> list[dict]:
    """
    Download PDFs for a list of papers. Adds a 'local_pdf_path' key to each
    paper dict (None if download failed or wasn't available).
    """
    for paper in papers:
        print(f"Downloading: {paper['title']}")
        paper["local_pdf_path"] = download_pdf(paper, save_dir)
        status = "OK" if paper["local_pdf_path"] else "unavailable/failed"
        print(f"  -> {status}")

    return papers


if __name__ == "__main__":
    from search import search_papers

    results = search_papers("retrieval augmented generation hallucination", limit=5)
    download_all(results)