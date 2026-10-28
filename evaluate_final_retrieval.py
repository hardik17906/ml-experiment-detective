"""Frozen additional relevance labels plus explicit coverage checks; no ranking tuning."""
import json
from statistics import mean
from pathlib import Path
from note_retrieval import load_notes, encode_queries_and_notes, keyword_rank, semantic_rank
from v3.retrieval import search_notes

NEW_CASES=[
 ("heldout_paraphrase","Did validation loss increase and subsequently recover?",["baseline_gap_001","lr_01_seed2"],"Both notes explicitly record a rise then fall."),
 ("early_spike","Which observation describes a loss jump at the second epoch?",["baseline_gap_001"],"Only this note describes the epoch-one to epoch-two spike."),
 ("late_spike","Which alternate-seed observation has a loss rise at epoch four?",["lr_01_seed2"],"Explicit alternate-seed epoch-four peak."),
 ("monotonic_synonym","Find the learning-rate experiment with steadily declining validation loss.",["lr_005_gap_001"],"Its five saved validation losses decrease."),
 ("lr_identifier","What did the note for lr_005_gap_001 observe?",["lr_005_gap_001"],"Exact existing technical run identifier."),
 ("regularized_small","Find the 1000-image experiment using dropout probability 0.5.",["small_dropout_05_001"],"Explicit training size and dropout metadata."),
 ("unregularized_small","Find the small training subset run without dropout.",["small_no_dropout_001"],"The note explicitly says no dropout."),
 ("dropout_accuracy","Which dropout run achieved 76.45 validation accuracy after 40 epochs?",["small_dropout_05_001"],"Numbers and settings are in the human observation."),
 ("no_dropout_accuracy","Which no-dropout experiment achieved 76.85 validation accuracy?",["small_no_dropout_001"],"The note's primary run has that measured value."),
 ("seed_variation","Find a temporary loss increase under different initialization and shuffle seeds.",["lr_01_seed2"],"Alternate model/shuffle seeds and a temporary increase are explicit."),
 ("technical_error","Which observations show a transient held-out error spike?",["baseline_gap_001","lr_01_seed2"],"Held-out error is interpreted as validation loss for this label."),
 ("small_training_score","Find the regularized small-data run with training accuracy 81.00 percent.",["small_dropout_05_001"],"Exact post-epoch training-accuracy observation.")]


def score(ids, relevant):
    return {"recall_at_2":len(set(ids[:2])&set(relevant))/len(relevant),
            "mrr_at_2":next((1/i for i,r in enumerate(ids[:2],1) if r in relevant),0)}


def main():
    old=json.loads(Path("retrieval_eval_cases.json").read_text())
    extra=[dict(id=i,query=q,relevant=r,reason=reason) for i,q,r,reason in NEW_CASES]
    cases=old+extra
    notes=load_notes()
    results=[]
    for c in cases:
        kw=keyword_rank(c["query"],notes)
        vectors=encode_queries_and_notes([c["query"]],notes,local_only=True)
        sem=semantic_rank(vectors[0],vectors[1:],notes)
        hybrid=search_notes(c["query"],top_k=2)
        reranked=search_notes(c["query"],top_k=2,rerank=True)
        rankings={"keyword":[p.stem for _,p,_,_ in kw],"semantic":[p.stem for _,p,_ in sem],
                  "hybrid":[r["run_id"] for r in hybrid["matches"]],"reranked":[r["run_id"] for r in reranked["matches"]]}
        results.append({**c,"methods":{m:dict(score(ids,c["relevant"]),top_ids=ids[:2]) for m,ids in rankings.items()},"reranker_status":reranked["reranker"]})
        print("CASE",c["id"],flush=True)
    def aggregate(rows):
        return {m:{k:round(mean(r["methods"][m][k] for r in rows),4) for k in ("recall_at_2","mrr_at_2")} for m in rankings}
    human={p.stem for p,_ in notes}
    coverage=[]
    for path in sorted(Path("runs").glob("*.json")):
        if path.stem not in human:
            result=search_notes(f"Show recorded behavior of {path.stem}")
            coverage.append({"run_id":path.stem,"found_first":result["matches"][0]["run_id"]==path.stem})
    report={"historical_five":aggregate(results[:5]),"additional_twelve":aggregate(results[5:]),"all_seventeen":aggregate(results),
            "cases":results,"exact_unnoted_coverage":coverage,
            "scope":"17 note-relevance labels plus 6 exact-ID coverage cases. New labels are explicit local judgments, not a blind external benchmark. No tuning after scoring."}
    Path("reports/final").mkdir(exist_ok=True,parents=True)
    Path("reports/final/retrieval.json").write_text(json.dumps(report,indent=2),encoding="utf-8")
    print(json.dumps({k:v for k,v in report.items() if k!="cases"},indent=2))


if __name__=="__main__":main()
