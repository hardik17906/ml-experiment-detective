import argparse
import json

from note_retrieval import (
    PROJECT_DIR,
    load_notes,
)
from v2_retrieval import hybrid_search_notes


def recall_at_k(ranked_ids, relevant_ids, k):
    return len(set(ranked_ids[:k]) & relevant_ids) / len(relevant_ids)


def mrr_at_k(ranked_ids, relevant_ids, k):
    return next(
        (1 / rank for rank, run_id in enumerate(ranked_ids[:k], start=1) if run_id in relevant_ids),
        0.0,
    )


parser = argparse.ArgumentParser(description="Evaluate keyword and semantic note retrieval")
parser.add_argument("--top-k", type=int, default=2)
args = parser.parse_args()
if args.top_k < 1:
    parser.error("--top-k must be at least 1")

cases = json.loads((PROJECT_DIR / "retrieval_eval_cases.json").read_text(encoding="utf-8"))
notes = load_notes()
known_ids = {path.stem for path, _ in notes}
for case in cases:
    if not case["relevant"] or not set(case["relevant"]) <= known_ids:
        parser.error(f"case {case['id']} has no valid relevant note IDs")

totals = {method: [0.0, 0.0] for method in ("keyword", "semantic", "hybrid", "reranked")}

print(f"Cases: {len(cases)} | Notes: {len(notes)} | K: {args.top_k}")
for case in cases:
    relevant = set(case["relevant"])
    result = hybrid_search_notes(case["query"], top_k=len(notes), rerank=True)
    stages = result["stages"]
    if not stages["RERANKED RESULTS"]:
        parser.error(f"reranker unavailable: {result['rerank_status']}")
    rankings = {
        "keyword": [row["run_id"] for row in stages["KEYWORD RESULTS"]],
        "semantic": [row["run_id"] for row in stages["SEMANTIC RESULTS"]],
        "hybrid": [row["run_id"] for row in stages["HYBRID RESULTS"]],
        "reranked": [row["run_id"] for row in stages["RERANKED RESULTS"]],
    }
    print(f"\n{case['id']}: {case['query']}")
    print(f"  relevant: {', '.join(case['relevant'])}")
    print(f"  label reason: {case['reason']}")
    for method, ranked_ids in rankings.items():
        recall = recall_at_k(ranked_ids, relevant, args.top_k)
        mrr = mrr_at_k(ranked_ids, relevant, args.top_k)
        totals[method][0] += recall
        totals[method][1] += mrr
        top_ids = ", ".join(ranked_ids[: args.top_k]) or "none"
        print(f"  {method:<8} top: {top_ids} | Recall@{args.top_k}={recall:.2f} MRR@{args.top_k}={mrr:.2f}")

print("\nMean scores across these cases:")
for method, (recall_total, mrr_total) in totals.items():
    print(
        f"  {method:<8} Recall@{args.top_k}={recall_total / len(cases):.2f} "
        f"MRR@{args.top_k}={mrr_total / len(cases):.2f}"
    )
