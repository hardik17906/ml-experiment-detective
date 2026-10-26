"""V3 search reuses the cached MiniLM encoder; V2 ranking stays untouched."""

import re
from pathlib import Path

from experiment_data import RUNS_DIR, load_run
from note_retrieval import encode_queries_and_notes, keyword_rank, load_notes, semantic_rank, words
from v2_retrieval import RRF_K, search_ml_knowledge
from v3.analysis import curve

STOPWORDS = set("a an the is are was were be been being do does did have has had we i you our it its this that which what when where why how before with without of to in on at for from and or as by about than every some seen run runs experiment experiments".split())
STOPWORDS.discard("without")


def tokens(text):
    # Preserve negation ('no', 'not') and configuration numbers.
    return words(text) - STOPWORDS


def derived_summary(record):
    c, m = record["config"], curve(record)
    if "incomplete" in m:
        return f"DERIVED_ANALYSIS {c['run_id']}: incomplete metrics {m['incomplete']}"
    behavior = "validation loss spike and recovery" if m["recoveries"] else "no recorded rise followed by recovery"
    if not m["largest_loss_rise"]:
        behavior += "; validation loss decreased or stayed flat every epoch"
    return (f"DERIVED_ANALYSIS machine-generated summary from runs/{c['run_id']}.json. "
            f"Run {c['run_id']}. Learning rate {c.get('learning_rate')}, dropout {c.get('dropout', 'unknown')}, "
            f"train size {c.get('train_size')}, model seed {c.get('model_seed')}, shuffle seed {c.get('shuffle_seed')}. "
            f"Final validation accuracy {m['final_accuracy_percent']} percent; final loss {m['final_loss']}; "
            f"largest validation loss rise {m['largest_loss_rise']}. {behavior}.")


def documents(include_derived=True, filters=None):
    filters = filters or {}
    if set(filters) - {"learning_rate", "dropout", "train_size", "run_id"}:
        raise ValueError("Unsupported retrieval filter")
    docs = []
    human = {path.stem: (path, text) for path, text in load_notes()}
    for path in sorted(RUNS_DIR.glob("*.json")):
        try:
            record = load_run(path.stem)
        except (ValueError, KeyError, TypeError):
            continue
        if any(record["config"].get(k) != v for k, v in filters.items()):
            continue
        if path.stem in human:
            p, text = human[path.stem]
            docs.append({"run_id": path.stem, "path": p, "text": text,
                         "source_type": "EXPERIMENT_NOTE", "source": f"notes/{p.name}"})
        elif include_derived:
            docs.append({"run_id": path.stem, "path": path, "text": derived_summary(record),
                         "source_type": "DERIVED_ANALYSIS", "source": f"runs/{path.name}"})
    return docs


def search_notes(query, top_k=3, *, include_derived=True, normalized=True, filters=None, semantic=True, source_policy="human_first"):
    if not isinstance(query, str) or not query.strip() or type(top_k) is not int or not 1 <= top_k <= 11:
        raise ValueError("Search needs a nonempty query and top_k between 1 and 11")
    docs = documents(include_derived, filters)
    pairs = [(x["path"], x["text"]) for x in docs]
    if not docs:
        return {"matches": [], "stages": {}, "mode": "empty"}
    if normalized:
        kw = [(len(tokens(query) & tokens(text)), path, [], text) for path, text in pairs]
        kw = sorted([x for x in kw if x[0]], key=lambda x: (-x[0], x[1].stem))
    else:
        kw = keyword_rank(query, pairs)
    mode = "keyword + cached MiniLM RRF"
    sem = []
    if semantic:
        try:
            embeddings = encode_queries_and_notes([query], pairs, local_only=True)
            sem = semantic_rank(embeddings[0], embeddings[1:], pairs)
        except (OSError, RuntimeError, ImportError) as exc:
            mode = f"APP POLICY: keyword fallback; MiniLM unavailable: {type(exc).__name__}"
    else:
        mode = "deterministic lexical fixture mode (no embeddings)"
    kr = {x[1].stem: i for i, x in enumerate(kw, 1)}
    sr = {x[1].stem: i for i, x in enumerate(sem, 1)}
    cos = {x[1].stem: float(x[0]) for x in sem}
    if source_policy not in {"human_first", "mixed"}:
        raise ValueError("Unknown source policy")
    if source_policy == "human_first":
        # Keep within-source ranks: adding derived documents must not perturb human-note order.
        groups = {d["run_id"]: d["source_type"] for d in docs}
        def within_source(ranks):
            counts, result = {}, {}
            for rid in sorted(ranks, key=ranks.get):
                source = groups[rid]
                counts[source] = counts.get(source, 0) + 1
                result[rid] = counts[source]
            return result
        kr, sr = within_source(kr), within_source(sr)
    exact = set(re.findall(r"[a-zA-Z0-9_-]+", query))
    rows = []
    for d in docs:
        rid = d["run_id"]
        score = (1 / (RRF_K + kr[rid]) if rid in kr else 0) + (1 / (RRF_K + sr[rid]) if rid in sr else 0)
        # Exact existing identifiers outrank text similarity, with the reason exposed.
        if score or rid in exact:
            rows.append({"run_id": rid, "source_type": d["source_type"], "source": d["source"],
                         "run_source": f"runs/{rid}.json", "observation": d["text"],
                         "keyword_rank": kr.get(rid), "semantic_rank": sr.get(rid),
                         "cosine_similarity": round(cos[rid], 4) if rid in cos else None,
                         "exact_run_id_match": rid in exact, "rrf_score": round(score, 6)})
    rows.sort(key=lambda x: (-int(x["exact_run_id_match"]),
              -int(source_policy == "human_first" and x["source_type"] == "EXPERIMENT_NOTE"), -x["rrf_score"], x["run_id"]))
    return {"query": query, "mode": mode, "source_policy": source_policy, "reranker": "disabled", "matches": rows[:top_k],
            "supplementary_derived_matches": [r for r in rows if r["source_type"] == "DERIVED_ANALYSIS"][:top_k],
            "stages": {"keyword": list(kr), "semantic": list(sr), "hybrid": [r["run_id"] for r in rows]},
            "corpus": {"human_notes": sum(x["source_type"] == "EXPERIMENT_NOTE" for x in docs),
                       "derived_summaries": sum(x["source_type"] == "DERIVED_ANALYSIS" for x in docs)}}


def knowledge(query, *, semantic=True):
    covered = re.search(r"learning.?rate|optimiz|gradient|sgd|dropout|overfit|validation|loss curve", query, re.I)
    if not covered:
        return {"matches": [], "limitation": "This topic is not covered by the small local ML knowledge base."}
    if semantic:
        try:
            result = search_ml_knowledge(query, top_k=2)
            result["matches"] = [dict(x, source_type="ML_KNOWLEDGE") for x in result["matches"]
                                 if tokens(query) & tokens(x["text"] + " " + x["topic"])]
            return result
        except (OSError, RuntimeError, ImportError) as exc:
            reason = f"APP POLICY: lexical knowledge fallback: {type(exc).__name__}"
    else:
        reason = "deterministic lexical fixture mode (no embeddings)"
    from v2_retrieval import _knowledge_chunks
    chunks = _knowledge_chunks()
    chunks.sort(key=lambda x: -len(tokens(query) & tokens(x["text"] + " " + x["topic"])))
    return {"matches": [dict(x, source_type="ML_KNOWLEDGE") for x in chunks
                        if tokens(query) & tokens(x["text"] + " " + x["topic"])][:2], "mode": reason}
