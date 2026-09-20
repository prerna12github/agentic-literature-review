"""
pipeline_graph.py — LangGraph wiring for the 5-agent literature review.

Each node is a thin wrapper around the functions you already built:
    search_node        -> question_to_keywords + search + download + extract
    filter_node        -> score_papers_with_llm
    human_checkpoint   -> LangGraph interrupt() (pauses the graph, waits for
                          approval, then resumes — this is the human-in-the-loop)
    reader_node        -> extract_claims_for_paper
    contradiction_node -> get_embeddings + group_similar_claims + verdicts
    writer_node        -> build_context_block + generate_final_answer

Running it:
    graph = build_pipeline_graph(checkpointer)
    result = graph.invoke({"query": "your question"}, config)
    # -> pauses at the checkpoint; resume with Command(resume=decision)
"""

import json
import os
import logging

from dotenv import load_dotenv
from google import genai
from google.genai import types

from langgraph.graph import StateGraph, START, END
from langgraph.types import interrupt, Command

from graph_state import LitReviewState

from search_pipeline.search import search_papers
from search_pipeline.download import download_until_target
from search_pipeline.extract import extract_for_paper
from filter_agent.filter_agent import score_papers_with_llm, show_ranked_list
from reader_agent.reader_agent import extract_claims_for_paper
from contradiction_agent.contra_agent import (
    flatten_claims, get_embeddings, group_similar_claims,
    check_group_for_contradiction, _involves_multiple_papers,
    SIMILARITY_THRESHOLD,
)
from writer_agent.writer_agent import (
    assign_citation_keys, build_context_block, generate_final_answer,
    format_references, verify_citations, save_report,
)

load_dotenv()

log = logging.getLogger(__name__)

OVERSAMPLE_FACTOR = 3
TARGET_PAPERS = 10

# Separate lightweight Gemini client for the keyword-distillation step
_client = genai.Client(api_key=os.environ["GEMINI_API_KEY"])
_KEYWORD_MODEL = os.environ.get("GEMINI_MODEL", "gemini-3.5-flash-lite")


# --------------------------------------------------------------------------
# Helper: long natural-language questions break keyword search engines
# --------------------------------------------------------------------------
def question_to_keywords(question: str) -> str:
    """
    NEW FIX: Search engines like Semantic Scholar match KEYWORDS, not prose.
    A long natural-language research question ("How can XAI techniques
    improve the transparency...?") returns 0 results because no paper
    matches all 20 words.

    So we distill the question into 5-8 keyword phrases first. The FULL
    question is still kept in state — it's used for relevance scoring
    (filter) and synthesis (writer). Only the search uses the distilled
    version.
    """
    if len(question.split()) <= 8:      # already keyword-like — use as-is
        return question

    response = _client.models.generate_content(
        model=_KEYWORD_MODEL,
        contents=f"""Distill this research question into 5-8 short keyword
phrases suitable for an academic paper search engine (like Semantic Scholar).
Return ONLY the keywords separated by commas, nothing else.

Question: "{question}" """.strip(),
    )
    keywords = response.text.strip().replace("\n", " ")
    print(f"  Search keywords: {keywords}")
    return keywords


# --------------------------------------------------------------------------
# Node 1: Search (wraps your entire Step 1 pipeline)
# --------------------------------------------------------------------------
def search_node(state: LitReviewState) -> dict:
    query = state["query"]
    # FIX 1: distill the question into keywords before searching
    search_query = question_to_keywords(query)
    log.info("=== [Search Agent] Searching: %s ===", search_query)

    papers = search_papers(search_query, limit=TARGET_PAPERS * OVERSAMPLE_FACTOR)

    # FIX 3 (part 1): fail loudly here instead of sailing silently
    # into an empty checkpoint downstream
    if not papers:
        raise RuntimeError(
            f"No papers found for the search keywords: '{search_query}'. "
            "Try rephrasing the research question with more specific terms."
        )

    papers = download_until_target(papers, target=TARGET_PAPERS, save_dir="papers")
    for paper in papers:
        extract_for_paper(paper)

    n_downloaded = sum(1 for p in papers if p["pdf_status"] == "downloaded")
    log.info("Search done: %d candidates, %d PDFs downloaded.",
             len(papers), n_downloaded)

    return {"papers": papers}


# --------------------------------------------------------------------------
# Node 2: Filter (LLM scoring — the RANKING, not the approval)
# --------------------------------------------------------------------------
def filter_node(state: LitReviewState) -> dict:
    papers = state["papers"]
    log.info("=== [Filter Agent] Scoring %d papers ===", len(papers))

    # Score against the FULL original question (not the keywords) —
    # relevance is about meaning, and the LLM understands prose
    scored = score_papers_with_llm(papers, state["query"])
    return {"papers": scored, "relevance_scored": True}


# --------------------------------------------------------------------------
# Node 3: Human checkpoint — THE interrupt
# --------------------------------------------------------------------------
def human_checkpoint_node(state: LitReviewState) -> dict:
    """
    LangGraph interrupt(): the graph STOPS here and returns control to the
    caller. The caller decides (CLI, web UI, API) and resumes the graph
    with Command(resume=decision). This is your human-in-the-loop.
    """
    papers = state["papers"]

    # FIX 3 (part 2): never present an empty ranked list — if we got here
    # with no papers, something upstream failed. Fail loudly.
    if not papers:
        raise RuntimeError(
            "No papers reached the approval checkpoint. "
            "This means search or filtering failed — check the logs above."
        )

    ranked = sorted(papers, key=lambda p: p.get("relevance_score", 0), reverse=True)

    # Show the ranked list (same display as your CLI version)
    show_ranked_list(ranked)

    # Pause here. Whatever the caller passes to Command(resume=...)
    # becomes the return value of interrupt().
    decision = interrupt({
        "prompt": "Approve papers for full reading? Reply with "
                  "{'action': 'approve_all'} or {'remove': [indices]}.",
        "ranked_papers": [
            {"index": i, "title": p["title"], "score": p.get("relevance_score", 0)}
            for i, p in enumerate(ranked)
        ],
    })

    # Apply the human's decision
    action = decision.get("action")
    if action == "approve_all":
        approved = ranked
    elif action == "remove":
        remove = set(decision.get("remove", []))
        approved = [p for i, p in enumerate(ranked) if i not in remove]
    else:
        log.warning("Unknown decision %r — approving all.", action)
        approved = ranked

    if not approved:
        raise RuntimeError(
            "Human removed all papers — nothing left to read. "
            "Rerun with a broader question or approve at least one paper."
        )

    log.info("Human approved %d papers.", len(approved))
    return {"approved_papers": approved}


# --------------------------------------------------------------------------
# Node 4: Reader (claim extraction, only for APPROVED papers)
# --------------------------------------------------------------------------
def reader_node(state: LitReviewState) -> dict:
    approved = state["approved_papers"]
    log.info("=== [Reader Agent] Reading %d papers ===", len(approved))

    for paper in approved:
        extract_claims_for_paper(paper)
        log.info("  '%s': %d claims", paper["title"], len(paper["claims"]))

    return {"approved_papers": approved, "claims_extracted": True}


# --------------------------------------------------------------------------
# Node 5: Contradiction (local embeddings + LLM verdicts)
# --------------------------------------------------------------------------
def contradiction_node(state: LitReviewState) -> dict:
    approved = state["approved_papers"]
    log.info("=== [Contradiction Agent] Checking %d papers ===", len(approved))

    all_claims = flatten_claims(approved)
    if len(all_claims) < 2:
        log.info("Fewer than 2 claims total — skipping contradiction check.")
        return {"comparisons": []}

    embeddings = get_embeddings([c["claim"] for c in all_claims])
    groups = group_similar_claims(all_claims, embeddings, SIMILARITY_THRESHOLD)

    comparisons = []
    for group in groups:
        if len(group) < 2 or not _involves_multiple_papers(group):
            continue
        verdict = check_group_for_contradiction(group)
        comparisons.append({
            "claims": group,
            "verdict": verdict["verdict"],
            "explanation": verdict["explanation"],
        })

    conflicts = sum(1 for c in comparisons if c["verdict"] == "conflict")
    log.info("Contradiction done: %d groups checked, %d conflict(s).",
             len(comparisons), conflicts)
    return {"comparisons": comparisons}


# --------------------------------------------------------------------------
# Node 6: Writer (final synthesis)
# --------------------------------------------------------------------------
def writer_node(state: LitReviewState) -> dict:
    approved = state["approved_papers"]
    comparisons = state.get("comparisons", [])
    log.info("=== [Writer Agent] Synthesizing final answer ===")

    title_to_key = assign_citation_keys(approved)
    context_block = build_context_block(approved, comparisons, title_to_key)
    answer = generate_final_answer(state["query"], context_block)

    warnings = verify_citations(answer, approved)
    if warnings:
        log.warning("%d quote(s) could not be matched to the evidence — review.",
                    len(warnings))

    conflicts = [c for c in comparisons if c.get("verdict") == "conflict"]
    conflict_summary = "\n".join(
        f"- **{c['verdict'].upper()}**: {c.get('explanation', '')}"
        for c in comparisons
    ) if comparisons else "No cross-paper contradictions were flagged."

    stats = {
        "papers_with_claims": sum(1 for p in approved if p.get("claims")),
        "total_claims": sum(len(p.get("claims", [])) for p in approved),
        "contradictions_checked": len(comparisons),
        "conflicts": len(conflicts),
        "conflict_summary": conflict_summary,
    }

    report_path = "final_report.md"
    save_report(state["query"], answer, format_references(approved),
                stats, report_path)

    log.info("Report saved to %s", report_path)
    return {"final_answer": answer, "report_path": report_path}


# --------------------------------------------------------------------------
# Build the graph
# --------------------------------------------------------------------------
def build_pipeline_graph(checkpointer=None):
    """
    Build and compile the pipeline graph.

    Args:
        checkpointer: optional LangGraph checkpointer (e.g. MemorySaver()).
                      REQUIRED for interrupt()/resume to work across
                      invocations — pass one when you actually run it.
    """
    graph = StateGraph(LitReviewState)

    graph.add_node("search", search_node)
    graph.add_node("filter", filter_node)
    graph.add_node("human_checkpoint", human_checkpoint_node)
    graph.add_node("reader", reader_node)
    graph.add_node("contradiction", contradiction_node)
    graph.add_node("writer", writer_node)

    graph.add_edge(START, "search")
    graph.add_edge("search", "filter")
    graph.add_edge("filter", "human_checkpoint")   # the gate
    graph.add_edge("human_checkpoint", "reader")
    graph.add_edge("reader", "contradiction")
    graph.add_edge("contradiction", "writer")
    graph.add_edge("writer", END)

    # checkpointer makes interrupt() + resume actually persist the
    # paused state. Without one, resume may fail depending on version.
    return graph.compile(checkpointer=checkpointer)