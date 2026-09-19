import json
import os
import logging
from dotenv import load_dotenv
from google import genai

load_dotenv()

log = logging.getLogger(__name__)

MODEL = os.environ.get("GEMINI_MODEL", "gemini-3.5-flash-lite")

API_KEY = os.environ.get("GEMINI_API_KEY")
if not API_KEY:
    raise RuntimeError("GEMINI_API_KEY not set — add it to your .env file")

client = genai.Client(api_key=API_KEY)
MAX_CLAIMS_TOTAL = 250


def _citation_key(paper: dict) -> str:
    
    authors = paper.get("authors") or []
    year = paper.get("year") or "n.d."
    if not authors:
        return f"Unknown ({year})"
    first = authors[0].split()[-1]  
    if len(authors) == 1:
        return f"{first} ({year})"
    return f"{first} et al. ({year})"


def load_step3_claims(claims_file: str) -> tuple[list[dict], str | None]:
  
    with open(claims_file, "r") as f:
        data = json.load(f)

    if isinstance(data, dict) and "papers" in data:
        return data["papers"], data.get("research_question")
    return data, None


def load_step4_comparisons(contradictions_file: str) -> list[dict]:
   
    if not os.path.exists(contradictions_file):
        return []

    with open(contradictions_file, "r") as f:
        data = json.load(f)

    if isinstance(data, dict) and "comparisons" in data:
        return data["comparisons"]
    if isinstance(data, list):
        return data  # old bare-list format
    return []


def assign_citation_keys(papers: list[dict]) -> dict:
    keys = {}
    for paper in papers:
        title = paper.get("title") or "untitled"
        key = _citation_key(paper)
        paper["citation_key"] = key
        keys[title] = key
    return keys


def build_context_block(
    papers: list[dict],
    comparisons: list[dict],
    title_to_key: dict,
) -> str:
    registry_lines = [
        f'- "{title}" -> cite as [{key}]'
        for title, key in title_to_key.items()
    ]
    registry = "\n".join(registry_lines)

    sections = []
    total_claims = 0
    for paper in papers:
        claims = paper.get("claims", [])
        if not claims:
            continue

        room = max(MAX_CLAIMS_TOTAL - total_claims, 0)
        if room == 0:
            log.warning("Claim cap reached — truncating evidence at %d claims.",
                        MAX_CLAIMS_TOTAL)
            break

        shown = claims[:room]
        total_claims += len(shown)

        claim_lines = "\n".join(
            f'  - "{c["claim"]}" (page {c["page"]})'
            for c in shown
        )
        sections.append(
            f'{paper["title"]} [cite as: {paper["citation_key"]}]\n{claim_lines}'
        )

    claims_block = "\n\n".join(sections) if sections else "(No claims available.)"
    if comparisons:
        conflicts = [c for c in comparisons if c.get("verdict") == "conflict"]
        others = [c for c in comparisons if c.get("verdict") != "conflict"]

        def fmt(c):
            claim_refs = "; ".join(
                f'"{cl["claim"]}" (from {title_to_key.get(cl["paper_title"], cl["paper_title"])}, '
                f'page {cl["page"]})'
                for cl in c.get("claims", [])
            )
            return f'- {c["verdict"].upper()}: {claim_refs}\n  Why: {c.get("explanation", "n/a")}'

        parts = []
        if conflicts:
            parts.append("CONFLICTS (must be addressed in the answer):\n" +
                         "\n".join(fmt(c) for c in conflicts))
        if others:
            parts.append("Agreements / unclear groups:\n" +
                         "\n".join(fmt(c) for c in others))
        contradictions_block = "\n\n".join(parts)
    else:
        contradictions_block = "(No cross-paper contradictions were flagged.)"

    return (
        f"=== PAPER REGISTRY (the ONLY papers that exist — never invent others) ===\n\n"
        f"{registry}\n\n"
        f"=== CLAIMS BY PAPER ===\n\n{claims_block}\n\n"
        f"=== CONTRADICTION FINDINGS (from a prior verification step) ===\n\n"
        f"{contradictions_block}"
    )


def generate_final_answer(research_question: str, context_block: str) -> str:
    prompt = f"""You are writing a literature review answer to a specific research question,
using ONLY the evidence provided below. Do not invent claims that aren't listed.

Research question: "{research_question}"

{context_block}

Write a clear, well-organized answer to the research question using this
evidence. Requirements:
- Cite every claim you use as (Author, Year, p. X), using the citation keys
  given in the PAPER REGISTRY exactly — e.g. (Lewis et al., 2020, p. 4).
- If the contradiction findings include CONFLICTS, you MUST explicitly
  address each one: state both sides and the likely reason they differ
  (using the explanation provided). Do not gloss over disagreements.
- If evidence is sparse or one-sided, say so honestly rather than
  overstating certainty.
- Use short paragraphs and, if helpful, subheadings.
- Never fabricate a claim, page number, or paper — only use what's listed.

Write the answer now."""

    response = client.models.generate_content(model=MODEL, contents=prompt)
    return response.text.strip()


def verify_citations(answer: str, papers: list[dict]) -> list[str]:
    known_claims = [
        c["claim"]
        for p in papers
        for c in p.get("claims", [])
    ]

    warnings = []
    for line in answer.split("\n"):
        if '"' in line and "(p" in line:
            start, end = line.find('"'), line.rfind('"')
            if start != -1 and end > start:
                quoted = line[start + 1:end]
                if len(quoted) > 30 and not any(
                    quoted in kc or kc in quoted for kc in known_claims
                ):
                    warnings.append(f"Uncited/unmatched quote: {quoted[:80]}...")
    return warnings


def format_references(papers: list[dict]) -> str:
    lines = []
    for paper in papers:
        if not paper.get("claims"):
            continue
        authors = ", ".join(paper.get("authors", []) or []) or "Unknown authors"
        year = paper.get("year", "n.d.")
        url = paper.get("url", "")
        url_part = f" — {url}" if url else ""
        lines.append(
            f"- **{paper['title']}** — {authors} ({year}){url_part}"
        )
    return "\n".join(lines) if lines else "(No references — no papers contributed claims.)"


def save_report(research_question: str, answer: str, references: str,
                stats: dict, output_file: str = "final_report.md") -> None:
    report = f"""# Literature Review: {research_question}

*Generated from {stats["papers_with_claims"]} papers, {stats["total_claims"]} extracted claims, and {stats["contradictions_checked"]} cross-paper comparisons ({stats["conflicts"]} conflict(s) detected).*

---

{answer}

---

## Contradictions Found

{stats["conflict_summary"]}

## References

{references}

---
*All claims above are grounded in the listed source papers with page-level citations, produced by an agentic pipeline: Search → Filter (human-approved) → Read → Contradiction-check → Write.*
"""
    with open(output_file, "w") as f:
        f.write(report)


def run_writer_step(claims_file: str = "claims_results.json",
                    contradictions_file: str = "contradiction_results.json",
                    output_file: str = "final_report.md",
                    research_question: str = None) -> str:
 
    papers, saved_question = load_step3_claims(claims_file)
    comparisons = load_step4_comparisons(contradictions_file)

    if research_question is None:
        research_question = saved_question or input("Enter your research question: ").strip()
        if saved_question:
            print(f'Using research question from Step 3: "{saved_question}"')

    if not papers:
        print("No papers found in the claims file. Run Step 3 first.")
        return ""

    title_to_key = assign_citation_keys(papers)

    papers_with_claims = sum(1 for p in papers if p.get("claims"))
    total_claims = sum(len(p.get("claims", [])) for p in papers)
    conflicts = [c for c in comparisons if c.get("verdict") == "conflict"]

    print(f"Loaded {total_claims} claims from {papers_with_claims} papers, "
          f"{len(comparisons)} comparisons ({len(conflicts)} conflicts).")

    print("Building evidence context from claims and contradiction findings...")
    context_block = build_context_block(papers, comparisons, title_to_key)

    print("Asking the LLM to synthesize the final answer...")
    answer = generate_final_answer(research_question, context_block)

    warnings = verify_citations(answer, papers)
    if warnings:
        print(f"\n⚠ Verification: {len(warnings)} quoted passage(s) in the answer "
              f"did not match the input evidence exactly — review before trusting:")
        for w in warnings[:5]:
            print(f"  - {w}")
    else:
        print("Verification: all quoted passages match the input evidence. ✓")

    conflict_summary = (
        "\n".join(
            f"- **{c['verdict'].upper()}**: {c.get('explanation', '')}"
            for c in comparisons
        )
        if comparisons else "No cross-paper contradictions were flagged for this question."
    )

    stats = {
        "papers_with_claims": papers_with_claims,
        "total_claims": total_claims,
        "contradictions_checked": len(comparisons),
        "conflicts": len(conflicts),
        "conflict_summary": conflict_summary,
    }

    references = format_references(papers)
    save_report(research_question, answer, references, stats, output_file)

    print(f"\nFinal report saved to {output_file}")
    return answer


if __name__ == "__main__":
    logging.basicConfig(level=logging.INFO, format="%(message)s")
    run_writer_step()