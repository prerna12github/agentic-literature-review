import json
import os
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
        "GEMINI_API_KEY not set — add it to your .env file "
        "(GEMINI_API_KEY=your_key)"
    )

client = genai.Client(api_key=API_KEY)
MAX_PAPERS_TO_SCORE = 40


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


def score_papers_with_llm(
    papers: list[dict],
    research_question: str,
) -> list[dict]:
    paper_summaries = []
    for i, p in enumerate(papers):
        abstract = p.get("abstract") or "(no abstract available)"
        paper_summaries.append(
            f"[{i}] Title: {p['title']}\n"
            f"Year: {p.get('year')}\n"
            f"Abstract: {abstract}"
        )
    papers_text = "\n\n".join(paper_summaries)

    prompt = f"""You are helping a researcher filter papers for a literature review.

Research question: "{research_question}"

Here are the candidate papers:

{papers_text}

For EACH paper (by its [index] number), score how relevant it is to answering
the research question, from 1 (not relevant) to 10 (highly relevant), and give
a one-sentence reason.

Respond with ONLY a JSON array, no other text, no markdown fences, in this
exact format:
[
  {{"index": 0, "relevance_score": 8, "relevance_reason": "Directly proposes a method for X."}},
  {{"index": 1, "relevance_score": 3, "relevance_reason": "Only tangentially related, focuses on Y instead."}}
]"""
    response = client.models.generate_content(
        model=MODEL,
        contents=prompt,
        config=types.GenerateContentConfig(
            response_mime_type="application/json",
        ),
    )

    try:
        scores = json.loads(response.text.strip())
    except json.JSONDecodeError:
        log.warning("JSON mode output was not clean JSON — using fallback parser.")
        scores = _parse_llm_json(response.text)
    if len(scores) != len(papers):
        log.warning(
            "LLM returned %d scores for %d papers; unscored papers get 0.",
            len(scores), len(papers),
        )

    score_by_index = {s["index"]: s for s in scores}
    for i, paper in enumerate(papers):
        match = score_by_index.get(i, {})
        paper["relevance_score"] = match.get("relevance_score", 0)
        paper["relevance_reason"] = match.get(
            "relevance_reason", "No score returned."
        )

    return papers


def show_ranked_list(papers: list[dict]) -> list[dict]:
    ranked = sorted(
        papers,
        key=lambda p: p.get("relevance_score", 0),
        reverse=True,
    )

    status_labels = {
        "downloaded": "PDF available",
        "abstract_only": "no PDF (abstract only)",
        "not_attempted": "spare candidate (PDF not tried)",
    }

    print("\n" + "=" * 70)
    print("RANKED PAPERS (highest relevance first)")
    print("=" * 70)

    for i, p in enumerate(ranked):
        status = status_labels.get(
            p.get("pdf_status", "unknown"),
            p.get("pdf_status", "unknown"),
        )
        print(f"\n[{i}] Score: {p['relevance_score']}/10  ({status})")
        print(f"    {p['title']} ({p.get('year')})")
        print(f"    Reason: {p['relevance_reason']}")

    return ranked


def human_checkpoint(ranked_papers: list[dict]) -> list[dict]:
    print("\n" + "-" * 70)
    print("Approve this list, or remove papers you don't want carried forward.")
    print("  - Press Enter (or type 'y') to approve ALL papers as shown above")
    print("  - Type comma-separated numbers to REMOVE those papers, e.g: 2,5,7")
    print("  - Type 'q' to quit without approving anything")
    print("-" * 70)

    choice = input("Your choice: ").strip().lower()

    if choice == "q":
        print("Quit — no papers approved.")
        return []

    if choice in ("", "y"):
        print(f"Approved all {len(ranked_papers)} papers.")
        return ranked_papers
    try:
        remove_indices = {int(x.strip()) for x in choice.split(",") if x.strip()}
    except ValueError:
        print("Couldn't understand that input — approving all papers by default.")
        return ranked_papers

    approved = [
        p for i, p in enumerate(ranked_papers) if i not in remove_indices
    ]
    print(
        f"Removed {len(remove_indices)} paper(s). "
        f"{len(approved)} papers approved."
    )
    return approved


def load_step1_results(input_file: str) -> tuple[list[dict], str | None]:
    with open(input_file, "r") as f:
        data = json.load(f)

    if isinstance(data, dict) and "papers" in data:
        return data["papers"], data.get("query")
    return data, None  # old bare-list format


def run_filter_step(
    input_file: str = "results.json",
    output_file: str = "filtered_results.json",
    research_question: str = None,
) -> list[dict]:
    papers, saved_query = load_step1_results(input_file)

    if research_question is None:
        if saved_query:
            research_question = saved_query
            print(f'\nUsing research question from Step 1: "{saved_query}"')
            override = input("Press Enter to keep it, or type a new question: ").strip()
            if override:
                research_question = override
        else:
            research_question = input("Enter your research question: ").strip()

    if len(papers) > MAX_PAPERS_TO_SCORE:
        print(
            f"Note: {len(papers)} candidates found — scoring the top "
            f"{MAX_PAPERS_TO_SCORE} in this batch."
        )
        papers = papers[:MAX_PAPERS_TO_SCORE]

    print(
        f'\nScoring {len(papers)} papers against: "{research_question}"...'
    )
    scored_papers = score_papers_with_llm(papers, research_question)

    ranked = show_ranked_list(scored_papers)
    approved = human_checkpoint(ranked)
    output = {
        "research_question": research_question,
        "stats": {
            "scored": len(scored_papers),
            "approved": len(approved),
            "with_pdf": sum(1 for p in approved if p.get("local_pdf_path")),
        },
        "papers": approved,
    }

    with open(output_file, "w") as f:
        json.dump(output, f, ensure_ascii=False, indent=2)

    print(f"\nSaved {len(approved)} approved papers to {output_file}")
    return approved


if __name__ == "__main__":
    logging.basicConfig(level=logging.INFO, format="%(message)s")
    run_filter_step()