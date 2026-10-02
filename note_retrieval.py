import json
import re
from functools import lru_cache
from pathlib import Path


PROJECT_DIR = Path(__file__).resolve().parent
MODEL_ID = "sentence-transformers/all-MiniLM-L6-v2"
MODEL_REVISION = "1110a243fdf4706b3f48f1d95db1a4f5529b4d41"


def words(text):
    return set(re.findall(r"[a-z0-9]+", text.lower()))


def load_notes():
    notes = []
    for path in sorted((PROJECT_DIR / "notes").glob("*.md")):
        text = path.read_text(encoding="utf-8")
        if "Observation: " in text:
            notes.append((path, text.split("Observation: ", 1)[1].strip()))
    return notes


def filter_notes(notes, *, dropout=None, train_size=None, run_id=None):
    if dropout is None and train_size is None and run_id is None:
        return notes

    filtered = []
    for path, observation in notes:
        if run_id is not None and path.stem != run_id:
            continue
        run_path = PROJECT_DIR / "runs" / f"{path.stem}.json"
        config = json.loads(run_path.read_text(encoding="utf-8"))["config"]
        if dropout is not None and config.get("dropout") != dropout:
            continue
        if train_size is not None and config.get("train_size") != train_size:
            continue
        filtered.append((path, observation))
    return filtered


def keyword_rank(query, notes):
    query_words = words(query)
    matches = []
    for path, observation in notes:
        shared_words = query_words & words(observation)
        if shared_words:
            matches.append((len(shared_words), path, sorted(shared_words), observation))
    return sorted(matches, key=lambda match: (-match[0], match[1].stem))


@lru_cache(maxsize=2)
def _embedding_model(local_only):
    from sentence_transformers import SentenceTransformer

    return SentenceTransformer(
        MODEL_ID,
        revision=MODEL_REVISION,
        cache_folder=str(PROJECT_DIR / ".model_cache"),
        local_files_only=local_only,
    )


def encode_queries_and_notes(queries, notes, *, local_only=False):
    return _embedding_model(local_only).encode(
        queries + [observation for _, observation in notes]
    )


def cosine_similarity(first, second):
    import numpy as np

    return float(np.dot(first, second) / (np.linalg.norm(first) * np.linalg.norm(second)))


def semantic_rank(query_embedding, note_embeddings, notes):
    matches = [
        (cosine_similarity(query_embedding, embedding), path, observation)
        for (path, observation), embedding in zip(notes, note_embeddings)
    ]
    return sorted(matches, key=lambda match: (-match[0], match[1].stem))
