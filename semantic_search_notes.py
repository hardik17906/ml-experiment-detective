import argparse

from note_retrieval import (
    MODEL_ID,
    encode_queries_and_notes,
    filter_notes,
    load_notes,
    semantic_rank,
)


parser = argparse.ArgumentParser(description="Search experiment notes by meaning")
parser.add_argument("query", help="question or description to search for")
parser.add_argument("--top-k", type=int, default=3, help="maximum notes to show")
parser.add_argument("--dropout", type=float, help="exact dropout value of the note's primary run")
parser.add_argument("--train-size", type=int, help="exact training size of the note's primary run")
args = parser.parse_args()

if not args.query.strip():
    parser.error("query must not be empty")
if args.top_k < 1:
    parser.error("--top-k must be at least 1")

all_notes = load_notes()
if not all_notes:
    parser.error("no observation notes found")
notes = filter_notes(all_notes, dropout=args.dropout, train_size=args.train_size)
if not notes:
    print("Notes after filters: 0")
    raise SystemExit(0)

embeddings = encode_queries_and_notes([args.query], notes)
ranked = semantic_rank(embeddings[0], embeddings[1:], notes)

print(f"Model: {MODEL_ID}")
print(f"Embedding dimensions: {len(embeddings[0])}")
if args.dropout is not None or args.train_size is not None:
    print(f"Notes after filters: {len(notes)}")
print(f"Notes scored: {len(ranked)}")
for score, path, observation in ranked[: args.top_k]:
    print(f"\n{path.stem} | cosine similarity {score:.3f}")
    print(f"Source note: {path}")
    print(f"Observation: {observation}")
