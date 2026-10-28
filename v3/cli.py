"""python investigate.py: start, list, show, resume, decide, modify, export."""

import argparse
import json
from pathlib import Path

from v3.service import Investigator


def main(argv=None):
    p = argparse.ArgumentParser(description="ML Experiment Detective Research Investigator")
    p.add_argument("--db", help="optional local SQLite path")
    sub = p.add_subparsers(dest="command", required=True)
    start = sub.add_parser("start")
    start.add_argument("question")
    start.add_argument("--offline", action="store_true", help="use Python fallbacks for investigation planning and hypothesis selection")
    start.add_argument("--lexical", action="store_true", help="fixture/debug mode without embedding imports")
    sub.add_parser("list")
    for name in ("show", "resume", "export", "cancel"):
        s = sub.add_parser(name)
        s.add_argument("investigation_id")
    dec = sub.add_parser("decide")
    dec.add_argument("investigation_id")
    dec.add_argument("decision", choices=("approved", "rejected", "deferred"))
    dec.add_argument("--hash", required=True, help="exact displayed proposal hash")
    dec.add_argument("--mode", choices=("dry_run", "live"), default="dry_run")
    dec.add_argument("--reason", default="")
    mod = sub.add_parser("modify")
    mod.add_argument("investigation_id")
    mod.add_argument("proposal_file")
    args = p.parse_args(argv)
    app = Investigator(args.db)
    if args.command == "cancel":
        print(app.cancel(args.investigation_id))
        return
    if args.command == "list":
        print(json.dumps(app.store.list(research_only=True), indent=2))
        return
    if args.command == "start":
        state = app.start(args.question, model_enabled=not args.offline, semantic=not args.lexical)
    elif args.command == "decide":
        state = app.decide(args.investigation_id, args.hash, args.decision, mode=args.mode, reason=args.reason)
    elif args.command == "modify":
        state = app.modify(args.investigation_id, json.loads(Path(args.proposal_file).read_text(encoding="utf-8")))
    elif args.command == "resume":
        state = app.resume(args.investigation_id)
    else:
        state = app.store.load(args.investigation_id)
    print(f"{state['investigation_id']} | {state['status']}")
    if state.get("last_error"):
        print(state["last_error"])
        raise SystemExit(1)
    if state.get("proposal_id"):
        row = app.store.proposal(state["proposal_id"])
        print("PROPOSAL:", row["id"], "|", row["status"], "| SHA256:", row["hash"])
        print(json.dumps(row["payload"], indent=2))
    if args.command == "show":
        print(json.dumps(state, indent=2))
    else:
        print(state.get("answer") or state.get("report", ""))
    print("SAVED REPORT:", app.export(state["investigation_id"]))


if __name__ == "__main__":
    main()
