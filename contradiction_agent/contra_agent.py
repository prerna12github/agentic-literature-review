import json
import os
import math
import time
import hashlib
import logging
from dotenv import load_dotenv
from google import genai
from google.genai import types
from sentence_transformers import SentenceTransformer

load_dotenv()

log = logging.getLogger(__name__)

# FIXED: real model name (gemini-3.5-flash-lite does not exist).
# Check .env too — a stale GEMINI_MODEL there overrides this default.
MODEL = os.environ.get("GEMINI_MODEL", "gemini-3.5-flash-lite")

API_KEY = os.environ.get("GEMINI_API_KEY")
if not API_KEY:
    raise RuntimeError("GEMINI_API_KEY not set — add it to your .env file")

client = genai.Client(api_key=API_KEY)

# Calibrated for all-MiniLM-L6-v2 (NOT the old Gemini scale — see docstring).
# Raise it if unrelated claims get grouped; lower it if related claims
# get split apart. Use the diagnostic printout to tune from evidence.
SIMILARITY_THRESHOLD = 0.55

# Politeness delay between LLM verdict calls
BATCH_DELAY_SECONDS = 1.0

# Verdict cache: re-running with a tweaked threshold shouldn't re-spend
# LLM quota on groups whose claim sets haven't changed.
VERDICT_CACHE_FILE = "verdict_cache.json"

# Local embedding model (lazy-loaded so import stays fast)
_embedder: SentenceTransformer | None = None


def _get_embedder() -> SentenceTransformer:
    """Load the local embedding model once, on first use."""
    global _embedder
    if _embedder is None:
        print("Loading local embedding model (all-MiniLM-L6-v2)...")
        _embedder = SentenceTransformer("all-MiniLM-L6-v2")
    return _embedder


def get_embeddings(texts: list[str]) -> list[list[float]]:
    """
    LOCAL embeddings via sentence-transformers — no API, no quota, no
    rate limits. Returns embeddings in input order, unit-normalized
    (so cosine similarity is a plain dot product under the hood).
    """
    model = _get_embedder()
    vectors = model.encode(
        texts,
        show_progress_bar=True,
        normalize_embeddings=True,
    )
    return [v.tolist() for v in vectors]


def _parse_llm_object(raw_text: str) -> dict:
    """
    Extract a JSON OBJECT (not array) from an LLM response, tolerating
    fences/prose — slices between the first '{' and last '}'.
    """
    raw_text = raw_text.strip()
    start, end = raw_text.find("{"), raw_text.rfind("}")
    if start == -1 or end == -1 or end < start:
        raise ValueError("LLM response contained no JSON object")
    return json.loads(raw_text[start:end + 1])


def flatten_claims(papers: list[dict]) -> list[dict]:
    """
    Step 3's output is organized by paper. For grouping across papers we
    flatten into one list — carrying FULL provenance (paper_id, chunk_id,
    paper_title, page) so the Writer Agent can still cite each claim
    exactly after all the reshuffling in this step.
    """
    flat = []
    for paper in papers:
        for claim in paper.get("claims", []):
            flat.append({
                "paper_id": claim.get("paper_id") or paper.get("paper_id"),
                "paper_title": claim.get("paper_title") or paper.get("title"),
                "chunk_id": claim.get("chunk_id"),
                "page": claim.get("page"),
                "claim": claim["claim"],
            })
    return flat


def cosine_similarity(vec_a: list[float], vec_b: list[float]) -> float:
    """
    How similar two embedding vectors are: -1 (opposite) to 1 (identical
    direction/meaning). The standard way to compare embeddings.
    """
    dot_product = sum(a * b for a, b in zip(vec_a, vec_b))
    magnitude_a = math.sqrt(sum(a * a for a in vec_a))
    magnitude_b = math.sqrt(sum(b * b for b in vec_b))

    if magnitude_a == 0 or magnitude_b == 0:
        return 0.0

    return dot_product / (magnitude_a * magnitude_b)


def group_similar_claims(
    claims: list[dict],
    embeddings: list[list[float]],
    threshold: float = SIMILARITY_THRESHOLD,
) -> list[list[dict]]:
    """
    Groups claims by meaning similarity (greedy leader approach):
    each claim joins the group whose FIRST claim it's most similar to,
    or starts a new group if none pass the threshold.

    Pure local math — zero API calls.
    """
    assert len(claims) == len(embeddings), (
        f"claims/embeddings mismatch: {len(claims)} vs {len(embeddings)}"
    )

    groups: list[list[dict]] = []
    group_embeddings: list[list[float]] = []

    for claim, embedding in zip(claims, embeddings):
        best_group_index = None
        best_similarity = 0.0

        for i, rep_embedding in enumerate(group_embeddings):
            similarity = cosine_similarity(embedding, rep_embedding)
            if similarity > best_similarity:
                best_similarity = similarity
                best_group_index = i

        if best_group_index is not None and best_similarity >= threshold:
            groups[best_group_index].append(claim)
        else:
            groups.append([claim])
            group_embeddings.append(embedding)

    return groups


def _diagnose_embeddings(embeddings: list[list[float]]) -> None:
    """
    Prints the sample pairwise-similarity spread so the threshold can be
    tuned from evidence. Healthy MiniLM output: unrelated pairs land
    ~0.1-0.4; if nearly all pairs exceed the threshold, embeddings are
    degenerate; if the spread is sane but grouping fails, the threshold
    is simply too high/low.
    """
    n = min(len(embeddings), 8)
    if n < 2:
        return
    sims = []
    for i in range(n):
        for j in range(i + 1, n):
            sims.append(cosine_similarity(embeddings[i], embeddings[j]))
    sims.sort()
    print(f"  Sample pairwise similarities (first {n} claims): "
          f"min={sims[0]:.3f}  median={sims[len(sims)//2]:.3f}  "
          f"max={sims[-1]:.3f}")
    print(f"  (Unrelated pairs should be well BELOW the threshold "
          f"{SIMILARITY_THRESHOLD})")


def _group_cache_key(group: list[dict]) -> str:
    """Stable hash of a group's claims, for the verdict cache."""
    canonical = json.dumps(
        sorted(c["claim"] for c in group),
        ensure_ascii=False,
    )
    return hashlib.sha256(canonical.encode()).hexdigest()


def _load_verdict_cache() -> dict:
    if os.path.exists(VERDICT_CACHE_FILE):
        with open(VERDICT_CACHE_FILE) as f:
            return json.load(f)
    return {}


def _save_verdict_cache(cache: dict) -> None:
    with open(VERDICT_CACHE_FILE, "w") as f:
        json.dump(cache, f)

def _involves_multiple_papers(group: list[dict]) -> bool:
    """Only worth an LLM contradiction-check if claims come from different papers."""
    return len({c["paper_title"] for c in group}) > 1        


def check_group_for_contradiction(group: list[dict]) -> dict:
    """
    Sends one group of related claims (from different papers) to the LLM
    and asks whether they agree or conflict. Cached on disk so threshold
    re-tuning doesn't re-spend quota on unchanged groups.

    Returns: {"verdict": "agree"|"conflict"|"unclear", "explanation": "..."}
    """
    cache = _load_verdict_cache()
    key = _group_cache_key(group)
    if key in cache:
        return cache[key]

    claims_text = "\n".join(
        f'- "{c["claim"]}" (from {c["paper_title"]}, page {c["page"]})'
        for c in group
    )

    prompt = f"""Here are claims from different papers that appear to be about the same topic:

{claims_text}

Do these claims agree with each other, or do they conflict? If they conflict,
briefly explain WHY they might differ (e.g. different datasets, different
methods, different assumptions, different time periods).

Respond with ONLY a JSON object, no other text, no markdown fences, in this
exact format:
{{"verdict": "agree", "explanation": "Both papers report similar findings using comparable methods."}}

("verdict" must be exactly one of: "agree", "conflict", "unclear")"""

    response = client.models.generate_content(
        model=MODEL,
        contents=prompt,
        config=types.GenerateContentConfig(
            response_mime_type="application/json",
        ),
    )

    try:
        verdict = json.loads(response.text.strip())
    except json.JSONDecodeError:
        try:
            verdict = _parse_llm_object(response.text)
        except (ValueError, json.JSONDecodeError):
            log.warning("Could not parse verdict response; marking group unclear.")
            verdict = {"verdict": "unclear",
                       "explanation": "Could not parse LLM response."}

    # Validate the verdict value — an unexpected string from the LLM
    # shouldn't poison the downstream stats/output
    if verdict.get("verdict") not in ("agree", "conflict", "unclear"):
        verdict["verdict"] = "unclear"

    cache[key] = verdict
    _save_verdict_cache(cache)
    return verdict


def load_step3_results(input_file: str) -> tuple[list[dict], str | None]:
    """
    Unwrap Step 3's wrapped output
        {"research_question": ..., "stats": ..., "papers": [...]}
    Bare-list format supported for backward compatibility.
    """
    with open(input_file, "r") as f:
        data = json.load(f)

    if isinstance(data, dict) and "papers" in data:
        return data["papers"], data.get("research_question")
    return data, None


def run_contradiction_step(input_file: str = "claims_results.json",
                           output_file: str = "contradiction_results.json") -> list[dict]:
    """
    Full Step 4 pipeline: load Step 3's claims, group similar ones, check
    cross-paper groups for agreement/conflict, save the result.
    """
    papers, research_question = load_step3_results(input_file)

    all_claims = flatten_claims(papers)
    if not all_claims:
        print("No claims found in the input file. Run Step 3 first.")
        return []

    n_papers = len({c["paper_title"] for c in all_claims})
    print(f"Loaded {len(all_claims)} claims from {n_papers} papers.\n")

    # --- Step A: embed ALL claims locally (free, no quota) ---
    print("Embedding claims (local sentence-transformer)...")
    embeddings = get_embeddings([c["claim"] for c in all_claims])
    print(f"DIAGNOSTIC: {len(all_claims)} claims, {len(embeddings)} embeddings")
    _diagnose_embeddings(embeddings)

    # --- Step B: group by similarity (pure local math) ---
    print("Grouping claims by similarity...")
    groups = group_similar_claims(all_claims, embeddings)
    print(f"Formed {len(groups)} groups.\n")

    # --- Step C: LLM check on cross-paper groups ---
    results = []
    checked_count = 0

    for group in groups:
        if len(group) < 2 or not _involves_multiple_papers(group):
            # Nothing to compare — a lone claim, or all claims came from
            # the same paper (a paper agreeing with itself isn't interesting)
            continue

        checked_count += 1
        print(f"  Checking group {checked_count}: {len(group)} claims across "
              f"{len({c['paper_title'] for c in group})} papers...")
        verdict = check_group_for_contradiction(group)
        time.sleep(BATCH_DELAY_SECONDS)

        results.append({
            "claims": group,   # full provenance preserved for the Writer
            "verdict": verdict["verdict"],
            "explanation": verdict["explanation"],
        })

    n_conflicts = sum(1 for r in results if r["verdict"] == "conflict")
    n_agree = sum(1 for r in results if r["verdict"] == "agree")
    n_unclear = sum(1 for r in results if r["verdict"] == "unclear")

    # Consistent wrapped output schema for Step 5 (Writer Agent)
    output = {
        "research_question": research_question,
        "stats": {
            "total_claims": len(all_claims),
            "groups_formed": len(groups),
            "cross_paper_groups_checked": checked_count,
            "conflicts": n_conflicts,
            "agreements": n_agree,
            "unclear": n_unclear,
        },
        "comparisons": results,
    }

    with open(output_file, "w") as f:
        json.dump(output, f, ensure_ascii=False, indent=2)

    print(f"\nChecked {checked_count} cross-paper groups: "
          f"{n_conflicts} conflict(s), {n_agree} agreement(s), {n_unclear} unclear.")
    print(f"Saved results to {output_file}")
    return results


if __name__ == "__main__":
    logging.basicConfig(level=logging.INFO, format="%(message)s")
    run_contradiction_step()