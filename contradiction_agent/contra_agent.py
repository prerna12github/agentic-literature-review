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

MODEL = os.environ.get("GEMINI_MODEL", "gemini-2.0-flash-lite")

API_KEY = os.environ.get("GEMINI_API_KEY")
if not API_KEY:
    raise RuntimeError("GEMINI_API_KEY not set — add it to your .env file")

client = genai.Client(api_key=API_KEY)
SIMILARITY_THRESHOLD = 0.55

BATCH_DELAY_SECONDS = 1.0
VERDICT_CACHE_FILE = "verdict_cache.json"

_embedder: SentenceTransformer | None = None


def _get_embedder() -> SentenceTransformer:
    global _embedder
    if _embedder is None:
        print("Loading local embedding model (all-MiniLM-L6-v2)...")
        _embedder = SentenceTransformer("all-MiniLM-L6-v2")
    return _embedder


def get_embeddings(texts: list[str]) -> list[list[float]]:
   
    model = _get_embedder()
    vectors = model.encode(
        texts,
        show_progress_bar=True,
        normalize_embeddings=True,
    )
    return [v.tolist() for v in vectors]


def _parse_llm_object(raw_text: str) -> dict:
    raw_text = raw_text.strip()
    start, end = raw_text.find("{"), raw_text.rfind("}")
    if start == -1 or end == -1 or end < start:
        raise ValueError("LLM response contained no JSON object")
    return json.loads(raw_text[start:end + 1])


def flatten_claims(papers: list[dict]) -> list[dict]:
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
    return len({c["paper_title"] for c in group}) > 1        


def check_group_for_contradiction(group: list[dict]) -> dict:
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

    if verdict.get("verdict") not in ("agree", "conflict", "unclear"):
        verdict["verdict"] = "unclear"

    cache[key] = verdict
    _save_verdict_cache(cache)
    return verdict


def load_step3_results(input_file: str) -> tuple[list[dict], str | None]:
    with open(input_file, "r") as f:
        data = json.load(f)

    if isinstance(data, dict) and "papers" in data:
        return data["papers"], data.get("research_question")
    return data, None


def run_contradiction_step(input_file: str = "claims_results.json",
                           output_file: str = "contradiction_results.json") -> list[dict]:
    
    papers, research_question = load_step3_results(input_file)

    all_claims = flatten_claims(papers)
    if not all_claims:
        print("No claims found in the input file. Run Step 3 first.")
        return []

    n_papers = len({c["paper_title"] for c in all_claims})
    print(f"Loaded {len(all_claims)} claims from {n_papers} papers.\n")

    print("Embedding claims (local sentence-transformer)...")
    embeddings = get_embeddings([c["claim"] for c in all_claims])
    print(f"DIAGNOSTIC: {len(all_claims)} claims, {len(embeddings)} embeddings")
    _diagnose_embeddings(embeddings)

    print("Grouping claims by similarity...")
    groups = group_similar_claims(all_claims, embeddings)
    print(f"Formed {len(groups)} groups.\n")
    results = []
    checked_count = 0

    for group in groups:
        if len(group) < 2 or not _involves_multiple_papers(group):
            continue

        checked_count += 1
        print(f"  Checking group {checked_count}: {len(group)} claims across "
              f"{len({c['paper_title'] for c in group})} papers...")
        verdict = check_group_for_contradiction(group)
        time.sleep(BATCH_DELAY_SECONDS)

        results.append({
            "claims": group,   
            "verdict": verdict["verdict"],
            "explanation": verdict["explanation"],
        })

    n_conflicts = sum(1 for r in results if r["verdict"] == "conflict")
    n_agree = sum(1 for r in results if r["verdict"] == "agree")
    n_unclear = sum(1 for r in results if r["verdict"] == "unclear")
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