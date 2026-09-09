"""
Step 3: Reader Agent
----------------------
Takes the papers approved in Step 2 (filtered_results.json) — each one
already carrying page-tagged text chunks from Step 1 — and asks the LLM to
pull out the key claims from each paper.

The critical design point: every claim we extract must keep its page-number
link. We never just ask "summarize this paper" — we ask "which page does
each claim come from", so later steps (Contradiction Agent, Writer Agent)
can always trace a claim back to its exact source.

A paper can have a LOT of chunks (some papers = 100+ paragraphs), so we
batch chunks into smaller groups per LLM call instead of sending an entire
paper's text in one shot — keeps prompts manageable and avoids truncation.
"""

import json
import os
from dotenv import load_dotenv
from google import genai

load_dotenv()

MODEL = os.environ.get("GEMINI_MODEL", "gemini-3.5-flash-lite")
client = genai.Client(api_key=os.environ.get("GEMINI_API_KEY"))

# How many chunks to send to the LLM in a single call. Smaller batches are
# cheaper and safer against truncation; larger batches mean fewer API calls.
CHUNKS_PER_BATCH = 15

# Skip papers with no extracted chunks at all (e.g. PDF wasn't available)
def _has_chunks(paper: dict) -> bool:
    return bool(paper.get("chunks"))


def _batch_chunks(chunks: list[dict], batch_size: int) -> list[list[dict]]:
    """Split a paper's chunk list into smaller batches for separate LLM calls."""
    return [chunks[i:i + batch_size] for i in range(0, len(chunks), batch_size)]


def _extract_claims_from_batch(paper_title: str, chunk_batch: list[dict]) -> list[dict]:
    """
    Sends ONE batch of page-tagged chunks to the LLM and asks it to extract
    factual claims, each tied to the exact page it came from.

    Returns a list of dicts: [{"claim": "...", "page": 4}, ...]
    """
    # Build the text block, clearly labeling each chunk with its page number
    # so the model can reference it accurately.
    labeled_chunks = "\n\n".join(
        f"(Page {c['page']}) {c['text']}" for c in chunk_batch
    )

    prompt = f"""You are extracting factual claims from a section of the research paper "{paper_title}".

Text (each piece is labeled with the page it came from):

{labeled_chunks}

Extract the key factual claims made in this text — things like reported
results, proposed methods, findings, or conclusions. Skip filler text
(references, acknowledgments, boilerplate).

For each claim, note the exact page number it came from (use the page label
shown above). If no real claims are present in this text, return an empty
array.

Respond with ONLY a JSON array, no other text, no markdown fences, in this
exact format:
[
  {{"claim": "The proposed method reduces error rate by 12% over baseline.", "page": 4}},
  {{"claim": "Prior work assumed a fixed retrieval window, which limits recall.", "page": 5}}
]"""

    response = client.models.generate_content(model=MODEL, contents=prompt)
    raw_text = response.text.strip()

    if raw_text.startswith("```"):
        raw_text = raw_text.strip("`")
        raw_text = raw_text.replace("json\n", "", 1).replace("json", "", 1)

    try:
        return json.loads(raw_text)
    except json.JSONDecodeError:
        print(f"  Warning: couldn't parse LLM response for a batch of '{paper_title}', skipping it.")
        return []


def extract_claims_for_paper(paper: dict) -> dict:
    """
    Runs claim extraction across ALL of a paper's chunk batches, and attaches
    the combined list of claims to the paper dict as paper['claims'].
    """
    if not _has_chunks(paper):
        paper["claims"] = []
        return paper

    all_claims = []
    batches = _batch_chunks(paper["chunks"], CHUNKS_PER_BATCH)

    for i, batch in enumerate(batches):
        print(f"    Reading batch {i + 1}/{len(batches)}...")
        claims = _extract_claims_from_batch(paper["title"], batch)
        all_claims.extend(claims)

    paper["claims"] = all_claims
    return paper


def run_reader_step(input_file: str = "filtered_results.json",
                     output_file: str = "claims_results.json") -> list[dict]:
    """
    Full Step 3 pipeline: load Step 2's approved papers, extract claims (with
    page citations) from each one, save the result.
    """
    with open(input_file, "r") as f:
        papers = json.load(f)

    print(f"Reading {len(papers)} approved papers...\n")

    for paper in papers:
        print(f"  {paper['title']}")
        paper = extract_claims_for_paper(paper)
        print(f"    -> {len(paper['claims'])} claims extracted\n")

    with open(output_file, "w") as f:
        json.dump(papers, f, indent=2)

    total_claims = sum(len(p["claims"]) for p in papers)
    print(f"Saved {total_claims} total claims across {len(papers)} papers to {output_file}")
    return papers


if __name__ == "__main__":
    run_reader_step()
