"""Interactive experiment assistant with educational agent modes."""

import argparse

from simple_agent import answer_question as answer_simple
from v2_agent import print_trace, run_manual
from v2_state import SessionState


def main() -> None:
    parser = argparse.ArgumentParser(description="Ask questions about saved ML experiments")
    parser.add_argument("--question", help="ask one question and exit")
    parser.add_argument("--no-trace", action="store_true", help="hide tool requests and results")
    parser.add_argument("--agent", choices=("assistant", "manual", "graph", "simple", "research"), default="assistant")
    parser.add_argument("--offline", action="store_true", help="primary assistant uses visible Python fallbacks without Ollama")
    parser.add_argument("--lexical", action="store_true", help="primary assistant searches without embedding imports")
    parser.add_argument("--rerank", action="store_true", help="opt in to the cached cross-encoder reranker")
    args = parser.parse_args()

    if args.agent == "research":
        from v3.cli import main as research_cli
        if args.question:
            research_cli(["start", args.question])
        else:
            print('Use: python investigate.py start "Investigate ..."; list/show/resume/decide/export manage saved work.')
        return

    print(f"ML Experiment Detective ({args.agent} agent, local evidence)")
    if args.question is None:
        print("Ask about runs, observations, or ML knowledge. Type clear to reset memory; exit to quit.")
    session = SessionState()

    while True:
        if args.question is not None:
            question = args.question
        else:
            try:
                question = input("\n> ").strip()
            except (EOFError, KeyboardInterrupt):
                print("\nGoodbye.")
                return
            if question.lower() in {"exit", "quit"}:
                print("Goodbye.")
                return
            if question.lower() == "clear":
                session.clear()
                print("Session memory cleared.")
                continue
            if not question:
                continue

        print(f"\nUSER -> {question}")
        try:
            if args.agent == "assistant":
                from assistant import ResearchAssistant
                result = ResearchAssistant().ask(question, session, offline=args.offline, semantic=not args.lexical, rerank=args.rerank)
                if not args.no_trace:
                    print_trace(result["trace"])
                answer = result["answer"]
            elif args.agent == "simple":
                answer = answer_simple(question, trace=not args.no_trace)
            else:
                if args.agent == "manual":
                    result = run_manual(question, session, rerank=args.rerank)
                else:
                    from graph_agent import run_graph

                    result = run_graph(question, session, rerank=args.rerank)
                if not args.no_trace:
                    print_trace(result["trace"])
                answer = result["answer"]
            print("\nANSWER")
            print(answer)
        except (OSError, ValueError, RuntimeError) as exc:
            print(f"Could not answer: {exc}")
        if args.question is not None:
            return


if __name__ == "__main__":
    main()
