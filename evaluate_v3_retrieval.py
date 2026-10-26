"""Compare V2 and candidate V3 ranking on identical labels, then measure coverage."""

import json
from statistics import mean

from experiment_data import RUNS_DIR
from note_retrieval import PROJECT_DIR, load_notes
from v2_retrieval import hybrid_search_notes
from v3.retrieval import search_notes


def scores(ids, relevant, k=2):
    return {"recall_at_2": len(set(ids[:k]) & set(relevant)) / len(relevant),
            "mrr_at_2": next((1 / i for i, x in enumerate(ids[:k], 1) if x in relevant), 0)}


def main():
    cases = json.loads((PROJECT_DIR / "retrieval_eval_cases.json").read_text(encoding="utf-8"))
    rows = []
    for c in cases:
        baseline = hybrid_search_notes(c["query"], top_k=5, rerank=True)
        rankings = {f"v2_{key}": [x["run_id"] for x in baseline["stages"][stage]] for key, stage in (
            ("keyword", "KEYWORD RESULTS"), ("semantic", "SEMANTIC RESULTS"),
            ("hybrid", "HYBRID RESULTS"), ("reranked", "RERANKED RESULTS"))}
        for variant, opts in (("v3_normalized_human", {"include_derived": False, "normalized": True}),
                              ("v3_normalized_expanded", {"include_derived": True, "normalized": True, "source_policy": "mixed"}),
                              ("v3_original_keyword_expanded", {"include_derived": True, "normalized": False, "source_policy": "mixed"}),
                              ("v3_human_priority_expanded", {"include_derived": True, "normalized": True})):
            rankings[variant] = [x["run_id"] for x in search_notes(c["query"], top_k=5, **opts)["matches"]]
        rows.append({"id": c["id"], "query": c["query"], "relevant": c["relevant"],
                     "methods": {method: dict(scores(ids, c["relevant"]), top_ids=ids[:2]) for method, ids in rankings.items()}})
        print("DONE", c["id"], flush=True)
    methods = list(rows[0]["methods"])
    means = {method: {metric: round(mean(r["methods"][method][metric] for r in rows), 4)
                       for metric in ("recall_at_2", "mrr_at_2")} for method in methods}
    note_ids = {p.stem for p, _ in load_notes()}
    coverage = []
    for path in sorted(RUNS_DIR.glob("*.json")):
        if path.stem in note_ids:
            continue
        q = f"Show the recorded validation behavior of {path.stem}"
        old = hybrid_search_notes(q, top_k=2)
        new = search_notes(q, top_k=2)
        coverage.append({"query": q, "relevant": path.stem,
                         "v2_found": path.stem in [x["run_id"] for x in old["matches"]],
                         "v3_found": path.stem in [x["run_id"] for x in new["matches"]]})
    report = {"scope": "Five fixed V2 labels; expanded coverage separately tests exact IDs absent from human notes. This is not a broad retrieval benchmark.",
              "means": means, "cases": rows, "unnoted_run_coverage": coverage,
              "reranker_status": baseline["rerank_status"]}
    path = PROJECT_DIR / "reports" / "v3_retrieval_evaluation.json"
    path.write_text(json.dumps(report, indent=2), encoding="utf-8")
    print(json.dumps(means, indent=2))
    print("Coverage", sum(x["v3_found"] for x in coverage), "/", len(coverage))


if __name__ == "__main__":
    main()
