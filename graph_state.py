from typing import TypedDict


class LitReviewState(TypedDict, total=False):
   
    query: str

    # --- Step 1: Search Agent output ---
    papers: list[dict]          

    # --- Step 2: Filter Agent output ---
    relevance_scored: bool        
    approved_papers: list[dict]   

    # Human checkpoint payload (what interrupt() returns)
    human_decision: dict         

    # --- Step 3: Reader Agent output ---
    claims_extracted: bool

    # --- Step 4: Contradiction Agent output ---
    comparisons: list[dict]      

    # --- Step 5: Writer Agent output ---
    final_answer: str
    report_path: str