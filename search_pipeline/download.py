"""
download.py — Download open-access PDFs for papers found by search.py.

Fixes/improvements in this version:
- Fallback chain: Semantic Scholar -> Unpaywall -> arXiv
- download_until_target(): keeps downloading until the target count
  is reached, instead of giving one shot to every paper
- Papers without any PDF are KEPT as abstract-only (not dropped),
  so the Filter Agent still has them
- Idempotent: skips files already on disk
- Collision-safe filenames (paper ID prefix) — no silent overwrites
- Politeness delay between downloads
- Relaxed %PDF check (some PDFs have junk bytes before the header)
"""

import os
import re
import time
import hashlib
import logging

import requests

log = logging.getLogger(__name__)

# Unpaywall is free but requires an identifying email (abuse tracking).
# Put a real address in your .env file.
from dotenv import load_dotenv   

load_dotenv()    

UNPAYWALL_EMAIL = os.environ.get("UNPAYWALL_EMAIL", "your_email@example.com")

POLITENESS_DELAY_SECONDS = 0.5


def _safe_filename(paper: dict) -> str:
    """
    Build a collision-safe filename from the paper's title.
    FIXED: a short ID prefix guarantees uniqueness even when two
    titles truncate to the same string.
    """
    title = paper.get("title") or "untitled"
    name = re.sub(r"[^a-zA-Z0-9]+", "_", title.strip())[:60].strip("_")

    # Prefer the real S2 paper ID; fall back to a title hash
    pid = paper.get("paper_id") or hashlib.md5(title.encode()).hexdigest()[:8]
    short_pid = (pid or "no-id")[:12]

    return f"{short_pid}_{name}.pdf"


def _unpaywall_pdf_url(doi: str) -> str | None:
    """
    Ask Unpaywall for an open-access copy (finds OA versions that
    Semantic Scholar misses). Free API, just needs an email.
    """
    if not doi:
        return None
    try:
        r = requests.get(
            f"https://api.unpaywall.org/v2/{doi}",
            params={"email": UNPAYWALL_EMAIL},
            timeout=15,
        )
        if r.status_code != 200:
            return None
        return (r.json().get("best_oa_location") or {}).get("url_for_pdf")
    except requests.RequestException:
        return None


def _arxiv_pdf_url(arxiv_id: str | None) -> str | None:
    """arXiv PDFs live at a predictable URL — no API call needed."""
    return f"https://arxiv.org/pdf/{arxiv_id}" if arxiv_id else None


def resolve_pdf_url(paper: dict) -> str | None:
    """
    Try every known open-access source, in order of reliability:
      1. Semantic Scholar's openAccessPdf link
      2. Unpaywall (via DOI)
      3. arXiv (via arXiv ID)
    Sets paper['pdf_source'] to record which one worked.
    """
    candidates = [
        ("semantic_scholar", paper.get("open_access_pdf")),
        ("unpaywall", _unpaywall_pdf_url(paper.get("doi"))),
        ("arxiv", _arxiv_pdf_url(paper.get("arxiv_id"))),
    ]

    for source, url in candidates:
        if url:
            paper["pdf_source"] = source
            return url

    paper["pdf_source"] = None
    return None


def download_pdf(paper: dict, pdf_url: str | None, save_dir: str = "papers") -> str | None:
    """
    Download one PDF from the given URL.

    Returns:
        Local file path if successful, otherwise None.
    """
    if not pdf_url:
        return None

    os.makedirs(save_dir, exist_ok=True)

    filepath = os.path.join(save_dir, _safe_filename(paper))

    # NEW: idempotent — don't re-download what we already have.
    # Makes repeated pipeline runs fast and rate-limit friendly.
    if os.path.exists(filepath) and os.path.getsize(filepath) > 0:
        log.info("  Already have: %s (skipping download)", filepath)
        return filepath

    headers = {
        "User-Agent": (
            "Mozilla/5.0 (X11; Linux x86_64) "
            "AppleWebKit/537.36 "
            "(KHTML, like Gecko) "
            "Chrome/131.0 Safari/537.36"
        ),
        "Accept": "application/pdf,*/*",
    }

    try:
        log.info("  Trying %s ...", pdf_url)

        response = requests.get(
            pdf_url,
            headers=headers,
            timeout=30,
            allow_redirects=True,
        )

        if response.status_code == 403:
            log.info("  Failed: 403 Forbidden (server blocked the request).")
            return None

        if response.status_code == 404:
            log.info("  Failed: 404 Not Found (PDF URL may be outdated).")
            return None

        response.raise_for_status()

        # RELAXED: some PDFs ship with junk bytes before the "%PDF"
        # header, so scan the first 1KB instead of only byte 0.
        if b"%PDF" not in response.content[:1024]:
            content_type = response.headers.get("Content-Type", "")
            log.info(
                "  Failed: URL did not return a PDF (Content-Type: %s)",
                content_type,
            )
            return None

        with open(filepath, "wb") as f:
            f.write(response.content)

        log.info("  Saved: %s", filepath)
        return filepath

    except requests.Timeout:
        log.info("  Failed: request timed out.")
        return None

    except requests.RequestException as e:
        log.info("  Failed: %s", e)
        return None


def download_until_target(
    papers: list[dict],
    target: int = 10,
    save_dir: str = "papers",
) -> list[dict]:
    """
    NEW core function: download PDFs in order until `target` successes
    or the candidate list runs out.

    Behavior:
      - Once the target is hit, remaining papers are marked
        'not_attempted' (spare candidates — never downloaded).
      - Papers where every source fails are KEPT with status
        'abstract_only' — the Filter Agent can still rank them,
        and the Reader Agent will simply skip them later.
    """
    os.makedirs(save_dir, exist_ok=True)
    successes = 0

    for paper in papers:
        if successes >= target:
            paper["pdf_status"] = "not_attempted"
            continue

        log.info("\nDownloading: %s", paper.get("title"))

        pdf_url = resolve_pdf_url(paper)
        path = download_pdf(paper, pdf_url=pdf_url, save_dir=save_dir)

        if path:
            paper["local_pdf_path"] = path
            paper["pdf_status"] = "downloaded"
            successes += 1
            log.info("  -> OK (%d/%d so far)", successes, target)
        else:
            paper["local_pdf_path"] = None
            paper["pdf_status"] = "abstract_only"
            log.info("  -> FAILED (kept as abstract-only)")

        # NEW: politeness delay between requests to different servers
        time.sleep(POLITENESS_DELAY_SECONDS)

    return papers


# Kept for backward compatibility with extract.py's __main__ test block
def download_all(
    papers: list[dict],
    save_dir: str = "papers",
) -> list[dict]:
    """Old behavior: attempt every paper, no target. Prefer download_until_target."""
    for paper in papers:
        log.info("\nDownloading: %s", paper.get("title"))
        pdf_url = resolve_pdf_url(paper)
        path = download_pdf(paper, pdf_url=pdf_url, save_dir=save_dir)

        if path:
            paper["local_pdf_path"] = path
            paper["pdf_status"] = "downloaded"
        else:
            paper["local_pdf_path"] = None
            paper["pdf_status"] = "abstract_only"

        time.sleep(POLITENESS_DELAY_SECONDS)

    return papers


if __name__ == "__main__":
    logging.basicConfig(level=logging.INFO, format="%(message)s")

    from search import search_papers

    results = search_papers(
        "retrieval augmented generation hallucination",
        limit=10,
    )
    download_until_target(results, target=5)