import argparse
import hashlib
import json
import re
from datetime import datetime, timezone
from pathlib import Path
from urllib.request import Request, urlopen

from answer_checks import (
    METRICS,
    check_observations,
    require_complete_val_loss_history,
    rise_then_fall_patterns,
)


PROJECT_DIR = Path(__file__).resolve().parent
MODEL = "qwen3:1.7b"
OPTIONS = {"temperature": 0, "num_ctx": 4096, "num_predict": 512}

parser = argparse.ArgumentParser(description="Generate a grounded answer with local Ollama")
parser.add_argument("prompt_id", help="existing filename under prompts/, without .md")
args = parser.parse_args()

if not re.fullmatch(r"[a-z0-9_-]+", args.prompt_id):
    parser.error("prompt_id must use lowercase letters, numbers, underscores, or hyphens")

prompt_path = PROJECT_DIR / "prompts" / f"{args.prompt_id}.md"
answer_path = PROJECT_DIR / "answers" / f"{args.prompt_id}.md"
metadata_path = PROJECT_DIR / "answers" / f"{args.prompt_id}.json"
if not prompt_path.is_file():
    parser.error(f"prompt does not exist: {prompt_path}")
if answer_path.exists() or metadata_path.exists():
    parser.error("answer or metadata already exists; choose a new prompt ID")

prompt = prompt_path.read_text(encoding="utf-8")
packet_match = re.search(r"^\*\*Source packet:\*\* `([a-z0-9_-]+)`$", prompt, re.MULTILINE)
allowed_run_ids = sorted(set(re.findall(r"\]\(\.\./runs/([a-z0-9_-]+)\.json\)", prompt)))
if not allowed_run_ids:
    parser.error("prompt contains no linked run records")

response_schema = {
    "type": "object",
    "properties": {
        "answer": {"type": "string"},
        "observations": {
            "type": "array",
            "items": {
                "type": "object",
                "properties": {
                    "run_id": {"type": "string", "enum": allowed_run_ids},
                    "epoch": {"type": "integer"},
                    "metric": {"type": "string", "enum": list(METRICS)},
                    "value": {"type": "string"},
                },
                "required": ["run_id", "epoch", "metric", "value"],
                "additionalProperties": False,
            },
        },
    },
    "required": ["answer", "observations"],
    "additionalProperties": False,
}
request_body = {
    "model": MODEL,
    "stream": False,
    "think": False,
    "messages": [{"role": "user", "content": prompt}],
    "format": response_schema,
    "options": OPTIONS,
}
request = Request(
    "http://127.0.0.1:11434/api/chat",
    data=json.dumps(request_body).encode("utf-8"),
    headers={"Content-Type": "application/json"},
    method="POST",
)
with urlopen(request, timeout=300) as response:
    result = json.load(response)

raw_answer = result["message"]["content"].strip()
if not result.get("done") or result.get("done_reason") != "stop" or not raw_answer:
    raise RuntimeError("Ollama did not return a complete, nonempty answer")
parsed_answer = json.loads(raw_answer)
if not isinstance(parsed_answer, dict):
    raise RuntimeError("Ollama response is not a JSON object")
if not isinstance(parsed_answer.get("answer"), str) or not parsed_answer["answer"].strip():
    raise RuntimeError("Ollama response has no answer")
if not isinstance(parsed_answer.get("observations"), list):
    raise RuntimeError("Ollama response has no observations list")
if re.search(r"\d", parsed_answer["answer"]):
    raise RuntimeError("Put run-specific numbers in observations, not the direct answer")

for item in parsed_answer["observations"]:
    if not isinstance(item, dict) or item.get("run_id") not in allowed_run_ids:
        raise RuntimeError(f"Ollama returned an unapproved run ID: {item!r}")
verified_observations = check_observations(parsed_answer["observations"], PROJECT_DIR / "runs")
question_match = re.search(r"^> (.+)$", prompt, re.MULTILINE)
question = question_match.group(1).lower() if question_match else ""
verified_patterns = []
answer_text = parsed_answer["answer"].strip()
if "held-out error" in question and "spike and recover" in question:
    verified_patterns = rise_then_fall_patterns(verified_observations)
    if not verified_patterns:
        require_complete_val_loss_history(
            verified_observations, allowed_run_ids, PROJECT_DIR / "runs"
        )
    expected_reply = "yes" if verified_patterns else "no"
    if not re.match(rf"^{expected_reply}\b", answer_text, re.IGNORECASE):
        raise RuntimeError(
            f"Direct answer disagrees with verified validation-loss pattern: expected {expected_reply}"
        )
    answer_text = (
        'Yes. Treating "held-out error" as validation loss, the verified measurements show a rise followed by a decrease.'
        if verified_patterns
        else 'No rise followed by a decrease appears in the verified validation-loss measurements.'
    )

lines = ["# Answer", "", answer_text, ""]
if verified_patterns:
    lines.extend(["## Verified patterns", ""])
    for pattern in verified_patterns:
        epochs = pattern["epochs"]
        values = pattern["values"]
        lines.append(
            f"- Epoch {epochs[0]} {values[0]} → epoch {epochs[1]} {values[1]} "
            f"→ epoch {epochs[2]} {values[2]}. "
            f"[source](../runs/{pattern['run_id']}.json)"
        )
    lines.append("")
lines.extend(["## Verified measurements", ""])
for item in verified_observations:
    run_id = item["run_id"]
    label = METRICS[item["metric"]][0]
    lines.append(
        f"- {label} at epoch {item['epoch']}: {item['value']}. "
        f"[source](../runs/{run_id}.json)"
    )
lines.extend(
    [
        "",
        "## Limit",
        "",
        "These run records show what happened; they do not by themselves establish why it happened.",
    ]
)
answer = "\n".join(lines) + "\n"

metadata = {
    "prompt_id": args.prompt_id,
    "source_packet_id": packet_match.group(1) if packet_match else args.prompt_id,
    "prompt_path": str(prompt_path),
    "prompt_sha256": hashlib.sha256(prompt.encode("utf-8")).hexdigest(),
    "model": result["model"],
    "options": OPTIONS,
    "thinking_enabled": False,
    "generated_at_utc": datetime.now(timezone.utc).isoformat(),
    "done_reason": result.get("done_reason"),
    "prompt_tokens": result.get("prompt_eval_count"),
    "answer_tokens": result.get("eval_count"),
    "model_response": parsed_answer,
    "verified_observations": verified_observations,
    "verified_patterns": verified_patterns,
}

answer_path.parent.mkdir(parents=True, exist_ok=True)
with answer_path.open("x", encoding="utf-8") as answer_file:
    answer_file.write(answer)
with metadata_path.open("x", encoding="utf-8") as metadata_file:
    json.dump(metadata, metadata_file, indent=2)
    metadata_file.write("\n")

print(f"Answer: {answer_path}")
print(f"Metadata: {metadata_path}")
print(f"Model: {metadata['model']}")
print(f"Prompt tokens: {metadata['prompt_tokens']}")
print(f"Answer tokens: {metadata['answer_tokens']}")
print(f"Done reason: {metadata['done_reason']}")
print(f"Measurements verified: {len(verified_observations)}")
print(f"Rise-then-fall patterns verified: {len(verified_patterns)}")
