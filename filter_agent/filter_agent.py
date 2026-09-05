"""
Step 2: Filter Agent
----------------------
Takes the papers found by Step 1 (search/download/extract) and a research
question, then:

  1. Asks an LLM (Google Gemini) to score each paper's relevance to the
     question and give a one-line reason for the score.
  2. Shows you the ranked list.
  3. PAUSES and waits for you to approve, remove specific papers, or approve
     all — before anything expensive (like full-text reading in Step 3)
     happens.

This is the "human-in-the-loop checkpoint" mentioned in the project docs:
a bad automatic decision here would silently corrupt everything downstream,
so a person reviews it first.
"""

import json
import os
from dotenv import load_dotenv
from google import genai

load_dotenv()

# Which Gemini model to use. Gemini 2.5 Flash has a generous free tier
# (no credit card needed) — good fit for this kind of triage/scoring task.
MODEL = os.environ.get("GEMINI_MODEL", "gemini-2.5-flash")

client = genai.Client(api_key=os.environ.get("GEMINI_API_KEY"))


def score_papers_with_llm(papers: list[dict], research_question: str) -> list[dict]:
    """
    Sends all paper titles/abstracts to the LLM in one call, and asks it to
    score each one's relevance to the research question.

    Args:
        papers: list of paper dicts (from Step 1's results.json)
        research_question: the user's actual research question

    Returns:
        The same list of papers, each with two new keys added:
        'relevance_score' (1-10) and 'relevance_reason' (short explanation).
    """
    # Build a compact numbered list of papers for the prompt — we only send
    # title + abstract, not full text, since this step is just triage.
    paper_summaries = []
    for i, p in enumerate(papers):
        abstract = p.get("abstract") or "(no abstract available)"
        paper_summaries.append(
            f"[{i}] Title: {p['title']}\nYear: {p.get('year')}\nAbstract: {abstract}"
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
    )

    raw_text = response.text.strip()

    # Defensive cleanup: sometimes models wrap JSON in ```json fences even when
    # told not to — strip those off if present, so json.loads doesn't choke.
    if raw_text.startswith("```"):
        raw_text = raw_text.strip("`")
        raw_text = raw_text.replace("json\n", "", 1).replace("json", "", 1)

    scores = json.loads(raw_text)

    # Merge scores back onto the original paper dicts, matched by index
    score_by_index = {s["index"]: s for s in scores}
    for i, paper in enumerate(papers):
        match = score_by_index.get(i, {})
        paper["relevance_score"] = match.get("relevance_score", 0)
        paper["relevance_reason"] = match.get("relevance_reason", "No score returned.")

    return papers


def show_ranked_list(papers: list[dict]) -> None:
    """Print papers sorted by relevance score, highest first."""
    ranked = sorted(papers, key=lambda p: p["relevance_score"], reverse=True)

    print("\n" + "=" * 70)
    print("RANKED PAPERS (highest relevance first)")
    print("=" * 70)
    for i, p in enumerate(ranked):
        pdf_status = "PDF available" if p.get("local_pdf_path") else "no PDF"
        print(f"\n[{i}] Score: {p['relevance_score']}/10  ({pdf_status})")
        print(f"    {p['title']} ({p.get('year')})")
        print(f"    Reason: {p['relevance_reason']}")

    return ranked


def human_checkpoint(ranked_papers: list[dict]) -> list[dict]:
    """
    THE HUMAN-IN-THE-LOOP STEP.

    Shows the ranked list (already printed by show_ranked_list) and asks the
    user what to do next:
      - press Enter / type 'y'  -> approve all papers as-is
      - type comma-separated numbers (e.g. "2,5,7") -> REMOVE those papers
      - type 'q' -> quit without approving anything

    Returns the final approved list of papers.
    """
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

    # Parse comma-separated indices to remove
    try:
        remove_indices = {int(x.strip()) for x in choice.split(",") if x.strip()}
    except ValueError:
        print("Couldn't understand that input — approving all papers by default.")
        return ranked_papers

    approved = [p for i, p in enumerate(ranked_papers) if i not in remove_indices]
    print(f"Removed {len(remove_indices)} paper(s). {len(approved)} papers approved.")
    return approved


def run_filter_step(input_file: str = "results.json",
                     output_file: str = "filtered_results.json",
                     research_question: str = None) -> list[dict]:
    """
    Full Step 2 pipeline: load Step 1's output, score with LLM, show ranked
    list, pause for human approval, save the approved subset.
    """
    with open(input_file, "r") as f:
        papers = json.load(f)

    if research_question is None:
        research_question = input("Enter your research question: ").strip()

    print(f"\nScoring {len(papers)} papers against: \"{research_question}\"...")
    scored_papers = score_papers_with_llm(papers, research_question)

    ranked = show_ranked_list(scored_papers)
    approved = human_checkpoint(ranked)

    with open(output_file, "w") as f:
        json.dump(approved, f, indent=2)

    print(f"\nSaved {len(approved)} approved papers to {output_file}")
    return approved


if __name__ == "__main__":
    run_filter_step()