import argparse

from note_retrieval import filter_notes, keyword_rank, load_notes, words


parser = argparse.ArgumentParser(description="Search experiment observation notes")
parser.add_argument("query", help="words to look for in the observations")
parser.add_argument("--top-k", type=int, default=3, help="maximum notes to show")
parser.add_argument("--dropout", type=float, help="exact dropout value of the note's primary run")
parser.add_argument("--train-size", type=int, help="exact training size of the note's primary run")
args = parser.parse_args()

query_words = words(args.query)
if not query_words:
    parser.error("query must contain at least one letter or digit")
if args.top_k < 1:
    parser.error("--top-k must be at least 1")

notes = filter_notes(load_notes(), dropout=args.dropout, train_size=args.train_size)
matches = keyword_rank(args.query, notes)
print(f"Matching notes: {len(matches)}")
for score, path, shared_words, observation in matches[: args.top_k]:
    print(f"\n{path.stem} | score {score} | shared words: {', '.join(shared_words)}")
    print(f"Source note: {path}")
    print(f"Observation: {observation}")
