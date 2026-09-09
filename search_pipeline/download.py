import requests
import os
import re


def _safe_filename(title: str) -> str:
    """Turn a paper title into a safe filename."""
    name = re.sub(r"[^a-zA-Z0-9]+", "_", title.strip())
    return name[:80].strip("_") + ".pdf"


def download_pdf(paper: dict, save_dir: str = "papers") -> str | None:
    """
    Download a paper's open-access PDF.

    Returns:
        Local file path if successful, otherwise None.
    """

    pdf_url = paper.get("open_access_pdf")

    # No PDF URL available
    if not pdf_url:
        print("  No open-access PDF URL available.")
        return None

    os.makedirs(save_dir, exist_ok=True)

    filename = _safe_filename(paper.get("title") or "untitled")
    filepath = os.path.join(save_dir, filename)

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
        print(f"  URL: {pdf_url}")

        response = requests.get(
            pdf_url,
            headers=headers,
            timeout=30,
            allow_redirects=True,
        )

        # Handle common HTTP errors separately
        if response.status_code == 403:
            print("  Failed: 403 Forbidden (server blocked the request).")
            return None

        if response.status_code == 404:
            print("  Failed: 404 Not Found (PDF URL may be outdated).")
            return None

        response.raise_for_status()

        # Make sure the response is actually a PDF
        if not response.content.startswith(b"%PDF"):
            content_type = response.headers.get("Content-Type", "")

            print(
                f"  Failed: URL did not return a PDF "
                f"(Content-Type: {content_type})"
            )
            return None

        # Save PDF
        with open(filepath, "wb") as f:
            f.write(response.content)

        print(f"  Saved: {filepath}")

        return filepath

    except requests.Timeout:
        print("  Failed: request timed out.")
        return None

    except requests.RequestException as e:
        print(f"  Failed: {e}")
        return None


def download_all(
    papers: list[dict],
    save_dir: str = "papers"
) -> list[dict]:
    """
    Download PDFs for all papers.

    Adds:
        local_pdf_path

    to each paper dictionary.
    """

    for paper in papers:

        print(f"\nDownloading: {paper['title']}")

        paper["local_pdf_path"] = download_pdf(
            paper,
            save_dir
        )

        if paper["local_pdf_path"]:
            print("  -> OK")
        else:
            print("  -> FAILED")

    return papers


if __name__ == "__main__":

    from search import search_papers

    results = search_papers(
        "retrieval augmented generation hallucination",
        limit=5
    )

    download_all(results)