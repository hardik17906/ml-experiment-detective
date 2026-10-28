"""The six requested user journeys; '--live' uses the actual installed local models."""
import argparse
import json
from pathlib import Path
import time
from assistant import ResearchAssistant
from v2_state import SessionState
from v3.experiment_executor import execute
from v3.investigation_state import ROOT

INVESTIGATION="Investigate why lr_01_seed3 performed worse than lr_005_seed3. Search notes, check previous experiments, retrieve ML knowledge, and propose a controlled follow-up."


def main():
    parser=argparse.ArgumentParser()
    parser.add_argument("--live",action="store_true",help="use installed Ollama and cached MiniLM; training still dry-run only")
    args=parser.parse_args()
    out=ROOT/"reports/final"
    out.mkdir(exist_ok=True,parents=True)
    app=ResearchAssistant()
    session=SessionState()
    results=[]
    def ask(journey,question):
        started=time.monotonic()
        r=app.ask(question,session,offline=not args.live,semantic=args.live)
        assert r["status"]!="failed",r.get("last_error")
        results.append({"journey":journey,"question":question,"status":r["status"],"answer":r["answer"],
                        "elapsed_seconds":round(time.monotonic()-started,3),"trace":r["trace"]})
        print("PASS",journey,question,r["status"],flush=True)
        return r
    ask("1 Exploration","What experiments do we have?")
    ask("1 Exploration","Which had the best final validation accuracy?")
    curves=ask("1 Exploration","Show its training and validation curves.")
    assert curves["tool_results"][0][0]=="plot_run_metrics"
    session.clear()
    ask("2 Conversation","Tell me about lr_01_seed3.")
    ask("2 Conversation","Compare that run with lr_005_seed3.")
    mechanism=ask("2 Conversation","Why might the difference exist?")
    assert "Relevant ML knowledge" in mechanism["answer"]
    session.clear()
    rag=ask("3 RAG","Have we seen unstable validation-loss behavior before?")
    assert {name for name,_ in rag["tool_results"]}>={"search_notes","get_experiment"}
    session.clear()
    investigation=ask("4 Investigation",INVESTIGATION)
    assert investigation["status"]=="awaiting_approval",investigation.get("last_error")
    store=app.investigator.store
    p=store.proposal(investigation["proposal_id"])
    blocked=[]
    for decision in ("pending","rejected"):
        if decision=="rejected":store.decide(p["id"],p["hash"],"rejected",actor="development_dry_run")
        try:execute(store,p["id"],p["hash"],"dry_run")
        except PermissionError:blocked.append(decision)
        else:raise AssertionError("Unapproved/rejected execution was not blocked")
    assert blocked==["pending","rejected"]
    final=app.investigator.decide(investigation["investigation_id"],p["hash"],"approved",actor="development_dry_run",reason="Final development demonstration; dry run only")
    assert final["status"]=="dry_run_completed" and not final["execution"]["ingested"]
    results.append({"journey":"5 Human approval","blocked_states":blocked,"outcome":final["status"],"live_training":False})
    print("PASS 5 Human approval",blocked,final["status"],flush=True)
    session.clear()
    for q in ("Who won the football World Cup?","Show lr_01_seed33","Plot it."):
        ask("6 Error handling",q)
    final["conversation_after_question"]=investigation.get("conversation_after")
    final["demonstration_mode"]="live Ollama and cached MiniLM; dry-run execution" if args.live else "deterministic offline; lexical retrieval; dry-run execution"
    (out/"investigation.json").write_text(json.dumps(final,indent=2),encoding="utf-8")
    (out/"investigation.md").write_text(final["report"],encoding="utf-8")
    (out/"journeys.json").write_text(json.dumps({"mode":final["demonstration_mode"],"results":results},indent=2),encoding="utf-8")
    print("SAVED",final["investigation_id"],out,flush=True)


if __name__=="__main__":main()
