"""Download the optional 62.5 MB MiniLM L2 reranker to the D: project cache."""

import os
from pathlib import Path

PROJECT = Path(__file__).resolve().parent
CACHE = PROJECT / ".model_cache"
TARGET = CACHE / "reranker-ms-marco-MiniLM-L2-v2"
for name, folder in {
    "HF_HOME": CACHE,
    "HF_HUB_CACHE": CACHE / "hub",
    "HF_XET_CACHE": CACHE / "xet",
}.items():
    folder.mkdir(parents=True, exist_ok=True)
    os.environ[name] = str(folder)

from huggingface_hub import snapshot_download  # noqa: E402 - env must be set first

snapshot_download(
    repo_id="cross-encoder/ms-marco-MiniLM-L2-v2",
    local_dir=TARGET,
    cache_dir=CACHE / "hub",
    allow_patterns=[
        "config.json", "model.safetensors", "tokenizer.json", "tokenizer_config.json",
        "special_tokens_map.json", "vocab.txt", "modules.json", "sentence_bert_config.json",
    ],
    max_workers=2,
)
print(f"Reranker cached at: {TARGET}")
print(f"Model weights bytes: {(TARGET / 'model.safetensors').stat().st_size}")
