import json
import os
from dotenv import load_dotenv
from google import genai

load_dotenv()

MODEL = os.environ.get("GEMINI_MODEL", "gemini-3.5-flash-lite")
client = genai.Client(api_key=os.environ.get("GEMINI_API_KEY"))


def load_data(claims_file: str, contradictions_file: str) -> tuple[list[dict], list[dict]]:
    """Load Step 3's claims and Step 4's contradiction findings."""
    with open(claims_file, "r") as f:
        papers = json.load(f)

    # Contradiction results are optional — Step 4 might not have found any
    # cross-paper groups worth checking, or the file might not exist yet.
    if os.path.exists(contradictions_file):
        with open(contradictions_file, "r") as f:
            contradictions = json.load(f)
    else:
        contradictions = []

    return papers, contradictions


def build_context_block(papers: list[dict], contradictions: list[dict]) -> str:
    """
    Builds the big text block that gets fed to the LLM: every paper's claims
    (with page citations), followed by a clearly separated section listing
    any contradictions Step 4 found.
    """
    sections = []

    # Part 1: claims, organized by paper
    for paper in papers:
        claims = paper.get("claims", [])
        if not claims:
            continue

        claim_lines = "\n".join(
            f'  - "{c["claim"]}" (p. {c["page"]})' for c in claims
        )
        sections.append(f'Paper: "{paper["title"]}" ({paper.get("year", "n.d.")})\n{claim_lines}')

    claims_block = "\n\n".join(sections)

    # Part 2: contradictions, if any were found
    if contradictions:
        contradiction_lines = []
        for c in contradictions:
            claim_refs = "; ".join(
                f'"{cl["claim"]}" ({cl["paper_title"]}, p. {cl["page"]})' for cl in c["claims"]
            )
            contradiction_lines.append(
                f'- Verdict: {c["verdict"].upper()} — {claim_refs}\n  Reason: {c["explanation"]}'
            )
        contradictions_block = "\n".join(contradiction_lines)
    else:
        contradictions_block = "(No cross-paper contradictions were flagged.)"

    return (
        f"=== CLAIMS BY PAPER ===\n\n{claims_block}\n\n"
        f"=== CONTRADICTION FINDINGS (from an earlier verification step) ===\n\n{contradictions_block}"
    )


def generate_final_answer(research_question: str, context_block: str) -> str:
    """
    Sends the research question plus all gathered evidence to the LLM, and
    asks it to write a synthesized, cited answer.
    """
    prompt = f"""You are writing a literature review answer to a specific research question,
using ONLY the evidence provided below. Do not invent claims that aren't listed.

Research question: "{research_question}"

{context_block}

Write a clear, well-organized answer to the research question using this
evidence. Requirements:
- Cite every claim you use as (Paper Title, p. X), matching exactly what's given above.
- If the contradiction findings above show a CONFLICT, explicitly mention the
  disagreement in your answer and explain why the papers might differ (using
  the reason already given).
- If evidence is sparse or one-sided, say so honestly rather than overstating certainty.
- Organize the answer with short paragraphs or subheadings if it helps readability.
- Do not fabricate any claim, page number, or paper title beyond what was given.

Write the answer now."""

    response = client.models.generate_content(model=MODEL, contents=prompt)
    return response.text.strip()


def format_references(papers: list[dict]) -> str:
    """Builds a simple reference list from the papers that actually contributed claims."""
    lines = []
    for paper in papers:
        if not paper.get("claims"):
            continue  # don't list papers that contributed nothing to the answer

        authors = ", ".join(paper.get("authors", []) or []) or "Unknown authors"
        year = paper.get("year", "n.d.")
        lines.append(f"- {paper['title']} — {authors} ({year})")

    return "\n".join(lines) if lines else "(No references — no papers contributed claims.)"


def save_report(research_question: str, answer: str, references: str,
                 output_file: str = "final_report.md") -> None:
    """Writes the final answer + references as a readable Markdown report."""
    report = f"""# Literature Review: {research_question}

{answer}

## References

{references}
"""
    with open(output_file, "w") as f:
        f.write(report)


def run_writer_step(claims_file: str = "claims_results.json",
                     contradictions_file: str = "contradiction_results.json",
                     output_file: str = "final_report.md",
                     research_question: str = None) -> str:
    """
    Full Step 5 pipeline: load Steps 3 & 4's outputs, build the evidence
    context, ask the LLM to synthesize an answer, and save a final report.
    """
    papers, contradictions = load_data(claims_file, contradictions_file)

    if research_question is None:
        research_question = input("Enter your research question: ").strip()

    print("Building evidence context from claims and contradiction findings...")
    context_block = build_context_block(papers, contradictions)

    print("Asking the LLM to synthesize the final answer...")
    answer = generate_final_answer(research_question, context_block)

    references = format_references(papers)
    save_report(research_question, answer, references, output_file)

    print(f"\nFinal report saved to {output_file}")
    return answer


if __name__ == "__main__":
    run_writer_step()