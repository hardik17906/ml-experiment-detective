"""Hybrid experiment-note search and separate offline ML-knowledge search."""

from functools import lru_cache
from pathlib import Path

from note_retrieval import (
    PROJECT_DIR, MODEL_ID, encode_queries_and_notes, keyword_rank,
    load_notes, semantic_rank,
)


RRF_K = 60
RERANKER_ID = "cross-encoder/ms-marco-MiniLM-L2-v2"
RERANKER_DIR = PROJECT_DIR / ".model_cache" / "reranker-ms-marco-MiniLM-L2-v2"


@lru_cache(maxsize=1)
def _reranker():
    if not (RERANKER_DIR / "config.json").is_file():
        raise FileNotFoundError(f"Reranker is not cached at {RERANKER_DIR}")
    from sentence_transformers import CrossEncoder

    return CrossEncoder(
        str(RERANKER_DIR), local_files_only=True, device="cpu",
    )


def hybrid_search_notes(query: str, top_k: int = 2, rerank: bool = False) -> dict:
    if not query.strip():
        raise ValueError("Search query must not be empty")
    if not 1 <= top_k <= 5:
        raise ValueError("top_k must be from 1 to 5")
    notes = load_notes()
    if not notes:
        return {"query": query, "matches": [], "stages": {}, "rerank_status": "no notes"}

    keyword = keyword_rank(query, notes)
    embeddings = encode_queries_and_notes([query], notes, local_only=True)
    semantic = semantic_rank(embeddings[0], embeddings[1:], notes)
    keyword_by_id = {
        path.stem: {"rank": rank, "score": score, "shared_words": shared}
        for rank, (score, path, shared, _) in enumerate(keyword, 1)
    }
    semantic_by_id = {
        path.stem: {"rank": rank, "cosine": round(score, 4)}
        for rank, (score, path, _) in enumerate(semantic, 1)
    }
    rows = []
    for path, observation in notes:
        kw = keyword_by_id.get(path.stem)
        sem = semantic_by_id[path.stem]
        score = (1 / (RRF_K + kw["rank"]) if kw else 0) + 1 / (RRF_K + sem["rank"])
        rows.append({
            "run_id": path.stem,
            "note_source": f"notes/{path.name}",
            "run_source": f"runs/{path.stem}.json",
            "observation": observation,
            "keyword_rank": kw["rank"] if kw else None,
            "keyword_score": kw["score"] if kw else 0,
            "keyword_shared_words": kw["shared_words"] if kw else [],
            "semantic_rank": sem["rank"],
            "cosine_similarity": sem["cosine"],
            "hybrid_score": round(score, 6),
        })
    rows.sort(key=lambda row: (-row["hybrid_score"], row["run_id"]))
    for rank, row in enumerate(rows, 1):
        row["hybrid_rank"] = rank
    hybrid_order = [dict(row) for row in rows]

    status = "disabled"
    if rerank:
        try:
            scores = _reranker().predict([(query, row["observation"]) for row in rows])
            for row, score in zip(rows, scores):
                row["reranker_score"] = round(float(score), 4)
            rows.sort(key=lambda row: (-row["reranker_score"], row["hybrid_rank"]))
            status = f"{RERANKER_ID} (local cache)"
        except FileNotFoundError:
            status = "model not cached; hybrid order used"
    for rank, row in enumerate(rows, 1):
        row["final_rank"] = rank
    return {
        "query": query,
        "embedding_model": MODEL_ID,
        "rrf_k": RRF_K,
        "rerank_status": status,
        "stages": {
            "KEYWORD RESULTS": [
                {"run_id": path.stem, "rank": i, "shared_word_count": score, "shared_words": shared}
                for i, (score, path, shared, _) in enumerate(keyword, 1)
            ],
            "SEMANTIC RESULTS": [
                {"run_id": path.stem, "rank": i, "cosine_similarity": round(score, 4)}
                for i, (score, path, _) in enumerate(semantic, 1)
            ],
            "HYBRID RESULTS": [
                {"run_id": row["run_id"], "rank": row["hybrid_rank"], "rrf_score": row["hybrid_score"]}
                for row in hybrid_order
            ],
            "RERANKED RESULTS": [
                {"run_id": row["run_id"], "rank": row["final_rank"], "reranker_score": row.get("reranker_score")}
                for row in rows
            ] if status.startswith(RERANKER_ID) else [],
        },
        "matches": rows[:top_k],
    }


def _knowledge_chunks() -> list[dict]:
    chunks = []
    for path in sorted((PROJECT_DIR / "knowledge").glob("*.md")):
        metadata, text = path.read_text(encoding="utf-8").split("Text:\n", 1)
        fields = dict(line.split(": ", 1) for line in metadata.splitlines() if ": " in line)
        chunks.append({
            "id": path.stem,
            "path": f"knowledge/{path.name}",
            "source_title": fields["Title"],
            "source_url": fields["URL"],
            "topic": fields["Topic"],
            "source_type": fields["Source-Type"],
            "text": text.strip(),
        })
    return chunks


def search_ml_knowledge(query: str, top_k: int = 2) -> dict:
    """Only curated general ML documentation; never experiment notes or run facts."""
    if not query.strip():
        raise ValueError("Search query must not be empty")
    chunks = _knowledge_chunks()
    if not 1 <= top_k <= max(1, len(chunks)):
        raise ValueError(f"top_k must be from 1 to {len(chunks)}")
    if not chunks:
        return {"query": query, "matches": []}
    note_pairs = [(Path(item["path"]), item["text"]) for item in chunks]
    embeddings = encode_queries_and_notes([query], note_pairs, local_only=True)
    ranked = semantic_rank(embeddings[0], embeddings[1:], note_pairs)
    keyword = keyword_rank(query, note_pairs)
    keyword_ranks = {path.stem: rank for rank, (_, path, _, _) in enumerate(keyword, 1)}
    by_id = {item["id"]: item for item in chunks}
    candidates = []
    for semantic_rank_number, (score, path, _) in enumerate(ranked, 1):
        keyword_rank_number = keyword_ranks.get(path.stem)
        rrf = 1 / (RRF_K + semantic_rank_number)
        if keyword_rank_number is not None:
            rrf += 1 / (RRF_K + keyword_rank_number)
        candidates.append({
            **by_id[path.stem],
            "semantic_rank": semantic_rank_number,
            "keyword_rank": keyword_rank_number,
            "cosine_similarity": round(score, 4),
            "hybrid_score": round(rrf, 6),
        })
    candidates.sort(key=lambda item: (-item["hybrid_score"], item["id"]))
    for rank, item in enumerate(candidates, 1):
        item["rank"] = rank
    return {
        "query": query,
        "source_category": "general ML knowledge",
        "embedding_model": MODEL_ID,
        "ranking_method": "keyword + MiniLM reciprocal rank fusion",
        "matches": candidates[:top_k],
    }
