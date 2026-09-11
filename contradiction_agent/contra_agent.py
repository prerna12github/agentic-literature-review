
import json
import os
import math
from dotenv import load_dotenv
from google import genai

load_dotenv()

MODEL = os.environ.get("GEMINI_MODEL", "gemini-3.5-flash-lite")
EMBED_MODEL = os.environ.get("GEMINI_EMBED_MODEL", "gemini-embedding-2")
client = genai.Client(api_key=os.environ.get("GEMINI_API_KEY"))

# Claims whose embeddings are at least this similar get grouped together.
# 1.0 = identical meaning, 0.0 = unrelated. 0.80 is a reasonably tight bar —
# raise it if unrelated claims are getting grouped, lower it if genuinely
# related claims are being split apart.
SIMILARITY_THRESHOLD = 0.80


def flatten_claims(papers: list[dict]) -> list[dict]:
    """
    Step 3's output is organized by paper (each paper has a list of claims).
    For grouping across papers, it's easier to work with one flat list of
    claims, each remembering which paper and page it came from.
    """
    flat = []
    for paper in papers:
        for claim in paper.get("claims", []):
            flat.append({
                "paper_title": paper["title"],
                "claim": claim["claim"],
                "page": claim["page"],
            })
    return flat


def get_embedding(text: str) -> list[float]:
    """Turn a piece of text into an embedding (list of numbers) using Gemini."""
    response = client.models.embed_content(model=EMBED_MODEL, contents=text)
    return response.embeddings[0].values


def cosine_similarity(vec_a: list[float], vec_b: list[float]) -> float:
    """
    Measures how similar two embedding vectors are, from -1 (opposite) to
    1 (identical direction/meaning). This is the standard way to compare
    embeddings.
    """
    dot_product = sum(a * b for a, b in zip(vec_a, vec_b))
    magnitude_a = math.sqrt(sum(a * a for a in vec_a))
    magnitude_b = math.sqrt(sum(b * b for b in vec_b))

    if magnitude_a == 0 or magnitude_b == 0:
        return 0.0

    return dot_product / (magnitude_a * magnitude_b)


def group_similar_claims(claims: list[dict], threshold: float = SIMILARITY_THRESHOLD) -> list[list[dict]]:
    """
    Groups claims by meaning similarity using a simple greedy approach:
    for each claim, compare it to the FIRST claim already in each existing
    group. If similar enough, join that group. Otherwise, start a new group.

    This is simpler than proper clustering algorithms (like k-means), but
    works well for this use case and is easy to understand and debug.
    """
    groups: list[list[dict]] = []
    group_embeddings: list[list[float]] = []  # one representative embedding per group

    for claim in claims:
        embedding = get_embedding(claim["claim"])
        claim["_embedding"] = embedding  # stash temporarily for reuse below

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

    # clean up the temporary embedding field before returning
    for group in groups:
        for claim in group:
            claim.pop("_embedding", None)

    return groups


def _involves_multiple_papers(group: list[dict]) -> bool:
    """Only worth an LLM contradiction-check if claims come from different papers."""
    return len({c["paper_title"] for c in group}) > 1


def check_group_for_contradiction(group: list[dict]) -> dict:
    """
    Sends one group of related claims (from different papers) to the LLM
    and asks whether they agree or conflict.

    Returns a dict: {"verdict": "agree"|"conflict"|"unclear", "explanation": "..."}
    """
    claims_text = "\n".join(
        f'- "{c["claim"]}" (from {c["paper_title"]}, page {c["page"]})' for c in group
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

    response = client.models.generate_content(model=MODEL, contents=prompt)
    raw_text = response.text.strip()

    if raw_text.startswith("```"):
        raw_text = raw_text.strip("`")
        raw_text = raw_text.replace("json\n", "", 1).replace("json", "", 1)

    try:
        return json.loads(raw_text)
    except json.JSONDecodeError:
        return {"verdict": "unclear", "explanation": "Could not parse LLM response."}


def run_contradiction_step(input_file: str = "claims_results.json",
                            output_file: str = "contradiction_results.json") -> list[dict]:
    """
    Full Step 4 pipeline: load Step 3's claims, group similar ones, check
    cross-paper groups for agreement/conflict, save the result.
    """
    with open(input_file, "r") as f:
        papers = json.load(f)

    all_claims = flatten_claims(papers)
    print(f"Loaded {len(all_claims)} claims from {len(papers)} papers.\n")

    print("Grouping claims by similarity (this calls the embedding model once per claim)...")
    groups = group_similar_claims(all_claims)
    print(f"Formed {len(groups)} groups.\n")

    results = []
    checked_count = 0

    for group in groups:
        if len(group) < 2 or not _involves_multiple_papers(group):
            # Nothing to compare — either a lone claim, or all claims came
            # from the same paper (agreeing with itself isn't interesting)
            continue

        checked_count += 1
        print(f"  Checking group {checked_count}: {len(group)} claims across "
              f"{len({c['paper_title'] for c in group})} papers...")
        verdict = check_group_for_contradiction(group)

        results.append({
            "claims": group,
            "verdict": verdict["verdict"],
            "explanation": verdict["explanation"],
        })

    with open(output_file, "w") as f:
        json.dump(results, f, indent=2)

    conflicts = sum(1 for r in results if r["verdict"] == "conflict")
    print(f"\nChecked {checked_count} cross-paper groups. Found {conflicts} conflict(s).")
    print(f"Saved results to {output_file}")
    return results


if __name__ == "__main__":
    run_contradiction_step()