# Hybrid note retrieval and reranking

`search_notes` searches only `notes/*.md`, which are clues to saved experiments. It does not take metrics from notes as the source of truth: after finding a note, the agent inspects the corresponding run JSON.

```text
question -> existing keyword_rank --------> rank of shared words --+
         -> MiniLM semantic_rank --------> cosine rank ----------+-> RRF order
                                                                  -> optional CrossEncoder order
                                                                  -> returned note IDs
```

Keyword rank counts shared words; semantic rank sorts MiniLM cosine similarities. Their raw scores have different meanings. Reciprocal Rank Fusion combines *positions*, with `score = 1/(60 + keyword_rank) + 1/(60 + semantic_rank)` when a note appears in both lists. A missing keyword rank contributes zero. For example, keyword rank 1 and semantic rank 2 gives `1/61 + 1/62 = 0.032522`. That number is a ranking score, not confidence.

For the saved full-trace question about unstable validation behavior like `lr_01_seed3`, keyword rank 1 was `baseline_gap_001`; semantic rank 1 was `lr_01_seed2`; RRF put `baseline_gap_001` first (0.032522) and `lr_01_seed2` second (0.032266). The trace exposes `KEYWORD RESULTS`, `SEMANTIC RESULTS`, `HYBRID RESULTS`, and, when enabled, `RERANKED RESULTS`, plus raw cosine and word matches. In this example the keyword shared words included “and” and “validation”, illustrating a weakness of the simple keyword ranker.

Optional reranking uses the locally cached `cross-encoder/ms-marco-MiniLM-L2-v2` to score query/note pairs after the cheap retrieval. It costs extra CPU work and can reorder candidates badly; it is off by default. A cross-encoder score is not truth or a probability.

## Actual five-case check

`evaluate_retrieval.py` uses the existing five labeled cases and all five notes. At `k=2`:

| Method | Mean Recall@2 | Mean MRR@2 |
| --- | ---: | ---: |
| Keyword | 0.90 | 0.80 |
| Semantic | 1.00 | 0.90 |
| Hybrid RRF | 0.90 | 0.90 |
| Hybrid then reranked | 0.80 | 0.70 |

The reranker missed both labeled notes in the “held-out error spike and recover” case at rank 2. These are five project-specific examples, not a general benchmark. Hybrid and reranking should be judged on a larger, representative set before changing the default.
