import json
import os
import time
import logging
from dotenv import load_dotenv
from google import genai
from google.genai import types

load_dotenv()

log = logging.getLogger(__name__)

MODEL = os.environ.get("GEMINI_MODEL", "gemini-3.5-flash-lite")
API_KEY = os.environ.get("GEMINI_API_KEY")
if not API_KEY:
    raise RuntimeError(
        "GEMINI_API_KEY not set — add it to your .env file"
    )

client = genai.Client(api_key=API_KEY)

CHUNKS_PER_BATCH = 15
BATCH_DELAY_SECONDS = 1.0


def _has_chunks(paper: dict) -> bool:
    return bool(paper.get("chunks"))


def _batch_chunks(chunks: list[dict], batch_size: int) -> list[list[dict]]:
    """Split a paper's chunk list into smaller batches for separate LLM calls."""
    return [chunks[i:i + batch_size] for i in range(0, len(chunks), batch_size)]


def _parse_llm_json(raw_text: str) -> list:

    raw_text = raw_text.strip()

    if raw_text.startswith("```"):
        parts = raw_text.split("```")
        raw_text = parts[1] if len(parts) > 1 else raw_text
        if raw_text.lower().lstrip().startswith("json"):
            raw_text = raw_text.lstrip()[4:]

    start, end = raw_text.find("["), raw_text.rfind("]")
    if start == -1 or end == -1 or end < start:
        raise ValueError("LLM response contained no JSON array")

    return json.loads(raw_text[start:end + 1])


def _extract_claims_from_batch(paper_title: str, chunk_batch: list[dict]) -> list[dict]:

    labeled_chunks = "\n\n".join(
        f"(chunk {c['chunk_id']}, page {c['page']}) {c['text']}"
        for c in chunk_batch
    )

    prompt = f"""You are extracting factual claims from a section of the research paper "{paper_title}".

Text (each piece is labeled with its chunk ID and the page it came from):

{labeled_chunks}

Extract the key factual claims made in this text — things like reported
results, proposed methods, findings, or conclusions. Skip filler text
(references, acknowledgments, boilerplate).

For each claim, copy the exact chunk_id and page number of the chunk it
came from. If no real claims are present in this text, return an empty
array.

Respond with ONLY a JSON array, no other text, no markdown fences, in this
exact format:
[
  {{"claim": "The proposed method reduces error rate by 12% over baseline.", "page": 4, "chunk_id": "abc123:p4:2"}},
  {{"claim": "Prior work assumed a fixed retrieval window, which limits recall.", "page": 5, "chunk_id": "abc123:p5:0"}}
]"""

    response = client.models.generate_content(
        model=MODEL,
        contents=prompt,
        config=types.GenerateContentConfig(
            response_mime_type="application/json",
        ),
    )

    try:
        claims = json.loads(response.text.strip())
    except json.JSONDecodeError:
        log.warning("JSON mode output was not clean — using fallback parser.")
        try:
            claims = _parse_llm_json(response.text)
        except (ValueError, json.JSONDecodeError):
            log.warning(
                "Couldn't parse LLM response for a batch of '%s', skipping it.",
                paper_title,
            )
            return []

    return [
        c for c in claims
        if isinstance(c, dict) and c.get("claim")
    ]


def extract_claims_for_paper(paper: dict) -> dict:
   
    if not _has_chunks(paper):
        paper["claims"] = []
        return paper

    paper_id = paper.get("paper_id") or "unknown-id"
    paper_title = paper.get("title") or "untitled"

    all_claims = []
    batches = _batch_chunks(paper["chunks"], CHUNKS_PER_BATCH)

    for i, batch in enumerate(batches):
        print(f"    Reading batch {i + 1}/{len(batches)}...")
        claims = _extract_claims_from_batch(paper_title, batch)

        for c in claims:
            all_claims.append({
                "claim": c["claim"],
                "page": c.get("page"),
                "chunk_id": c.get("chunk_id"),
                "paper_id": paper_id,
                "paper_title": paper_title,
            })

        if i < len(batches) - 1:
            time.sleep(BATCH_DELAY_SECONDS)

    paper["claims"] = all_claims
    return paper


def load_step2_results(input_file: str) -> tuple[list[dict], str | None]:
   
    with open(input_file, "r") as f:
        data = json.load(f)

    if isinstance(data, dict) and "papers" in data:
        return data["papers"], data.get("research_question")
    return data, None


def run_reader_step(input_file: str = "filtered_results.json",
                    output_file: str = "claims_results.json") -> list[dict]:
   
    papers, research_question = load_step2_results(input_file)

    if not papers:
        print("No approved papers found in the input file. Nothing to read.")
        return []

    print(f"Reading {len(papers)} approved papers...\n")

    papers_with_claims = 0
    for paper in papers:
        print(f"  {paper['title']}")
        extract_claims_for_paper(paper)
        n = len(paper["claims"])
        if n > 0:
            papers_with_claims += 1
        print(f"    -> {n} claims extracted\n")

    total_claims = sum(len(p["claims"]) for p in papers)

    output = {
        "research_question": research_question,
        "stats": {
            "papers_read": len(papers),
            "papers_with_claims": papers_with_claims,
            "total_claims": total_claims,
        },
        "papers": papers,
    }

    with open(output_file, "w") as f:
        json.dump(output, f, ensure_ascii=False, indent=2)

    print(
        f"Saved {total_claims} total claims across {papers_with_claims} "
        f"papers (of {len(papers)} read) to {output_file}"
    )
    return papers


if __name__ == "__main__":
    logging.basicConfig(level=logging.INFO, format="%(message)s")
    run_reader_step()