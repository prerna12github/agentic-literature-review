import os
import re
import time
import hashlib
import logging

import requests

log = logging.getLogger(__name__)

from dotenv import load_dotenv   

load_dotenv()    

UNPAYWALL_EMAIL = os.environ.get("UNPAYWALL_EMAIL", "your_email@example.com")

POLITENESS_DELAY_SECONDS = 0.5


def _safe_filename(paper: dict) -> str:
    title = paper.get("title") or "untitled"
    name = re.sub(r"[^a-zA-Z0-9]+", "_", title.strip())[:60].strip("_")
    pid = paper.get("paper_id") or hashlib.md5(title.encode()).hexdigest()[:8]
    short_pid = (pid or "no-id")[:12]

    return f"{short_pid}_{name}.pdf"


def _unpaywall_pdf_url(doi: str) -> str | None:
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
    if not pdf_url:
        return None

    os.makedirs(save_dir, exist_ok=True)

    filepath = os.path.join(save_dir, _safe_filename(paper))
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
        time.sleep(POLITENESS_DELAY_SECONDS)

    return papers


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