"""Ask local Ollama to select two source-backed hypothesis templates."""

import argparse
import hashlib
import json
import re
from datetime import datetime, timezone
from pathlib import Path
from urllib.request import Request, urlopen

from build_hypothesis_worksheet import analyze_pair, build_worksheet, rise_text


PROJECT_DIR = Path(__file__).resolve().parent
MODEL = "qwen3:1.7b"
OPTIONS = {"temperature": 0, "num_ctx": 4096, "num_predict": 700}
ID = re.compile(r"[a-z0-9_-]+")
CANDIDATE_TEXT = {
    "loss_rise": {
        "description": "The higher learning rate may be associated with larger temporary validation-loss rises in this setup.",
        "missing_evidence": "More matched seed blocks and finer training measurements would show whether this pattern persists and help investigate the training trajectory.",
    },
    "accuracy_drop": {
        "description": "The higher learning rate may reduce final validation accuracy across seed blocks.",
        "missing_evidence": "More matched seed blocks on the same validation split would show how often the final-accuracy difference is negative.",
    },
    "seed_dependence": {
        "description": "The final-accuracy effect of learning rate may depend on the model and shuffle seeds.",
        "missing_evidence": "More matched seed blocks, each with both learning rates and the same validation split, would show how often the final-accuracy difference changes direction.",
    },
}


def evidence_catalog(case: dict) -> tuple[list[dict], dict]:
    """Build facts and candidate evidence roles from checked learning-rate pairs."""
    build_worksheet(case)  # Validates matched configurations and distinct seed blocks.
    pairs = [analyze_pair(item["low"], item["high"]) for item in case["pairs"]]
    evidence = []
    candidates = {
        name: {**wording, "support_ids": [], "against_ids": []}
        for name, wording in CANDIDATE_TEXT.items()
    }
    for number, pair in enumerate(pairs, start=1):
        low_id, high_id = pair["low_id"], pair["high_id"]
        low_lr = pair["low_config"]["learning_rate"]
        high_lr = pair["high_config"]["learning_rate"]
        seed_label = (
            f"model/shuffle seeds {pair['low_config']['model_seed']}/"
            f"{pair['low_config']['shuffle_seed']}"
        )
        accuracy_delta = 100 * (pair["high_accuracy"] - pair["low_accuracy"])
        rise_id, accuracy_id = f"E{3 * number - 1}", f"E{3 * number}"
        rise_role = "support_ids" if pair["high_rise"][0] > pair["low_rise"][0] else "against_ids"
        accuracy_role = "support_ids" if accuracy_delta < 0 else "against_ids"
        candidates["loss_rise"][rise_role].append(rise_id)
        candidates["accuracy_drop"][accuracy_role].append(accuracy_id)
        candidates["seed_dependence"]["support_ids"].append(accuracy_id)
        evidence.extend(
            [
                {
                    "id": f"E{3 * number - 2}",
                    "claim": f"For {seed_label}, the recorded configurations differ only in learning rate ({low_lr:g} versus {high_lr:g}).",
                    "sources": [low_id, high_id],
                },
                {
                    "id": rise_id,
                    "claim": f"For {seed_label}, the largest one-epoch validation-loss rise was {rise_text(pair['low_rise'])} at learning rate {low_lr:g} and {rise_text(pair['high_rise'])} at {high_lr:g}.",
                    "sources": [low_id, high_id],
                },
                {
                    "id": accuracy_id,
                    "claim": f"For {seed_label}, final validation accuracy was {100 * pair['low_accuracy']:.2f}% at learning rate {low_lr:g} and {100 * pair['high_accuracy']:.2f}% at {high_lr:g} ({accuracy_delta:+.2f} percentage points for high minus low).",
                    "sources": [low_id, high_id],
                },
            ]
        )

    deltas = [100 * (pair["high_accuracy"] - pair["low_accuracy"]) for pair in pairs]
    mixed_directions = any(delta < 0 for delta in deltas) and any(delta >= 0 for delta in deltas)
    summary_id = f"E{3 * len(pairs) + 1}"
    evidence.append(
        {
            "id": summary_id,
            "claim": f"Across {len(pairs)} matched seed blocks, the high-minus-low final validation-accuracy differences were {', '.join(f'{delta:+.2f}' for delta in deltas)} percentage points in listed order; the direction {'varied' if mixed_directions else 'did not vary'}.",
            "sources": [run_id for pair in pairs for run_id in (pair["low_id"], pair["high_id"])],
        }
    )
    candidates["accuracy_drop"]["support_ids" if all(delta < 0 for delta in deltas) else "against_ids"].append(summary_id)
    candidates["seed_dependence"]["support_ids" if mixed_directions else "against_ids"].append(summary_id)
    return evidence, candidates


def source_links(run_ids: list[str]) -> str:
    return ", ".join(f"[{run_id}](../runs/{run_id}.json)" for run_id in run_ids)


def validate_hypotheses(response: dict, evidence_ids: set[str], candidates: dict) -> list[dict]:
    if not isinstance(response, dict) or set(response) != {"selected"}:
        raise ValueError("Model response must contain only selected")
    selected = response["selected"]
    if not isinstance(selected, list) or len(selected) != 2:
        raise ValueError("Model must select exactly two candidates")
    seen = set()
    for item in selected:
        if not isinstance(item, dict) or set(item) != {"type", "support_ids", "against_ids"}:
            raise ValueError("Selection has missing or extra fields")
        category = item["type"]
        if category not in candidates or category in seen:
            raise ValueError(f"Unknown or repeated candidate: {category!r}")
        seen.add(category)
        for field in ("support_ids", "against_ids"):
            supplied = item[field]
            expected = candidates[category][field]
            if not isinstance(supplied, list) or any(
                not isinstance(value, str) or value not in evidence_ids for value in supplied
            ):
                raise ValueError(f"{category} has invalid {field}")
            if set(supplied) != set(expected) or len(supplied) != len(expected):
                raise ValueError(f"{category} has incorrect {field}; expected {expected}")
    return selected


def render_hypotheses(hypotheses: list[dict], evidence: list[dict], candidates: dict) -> str:
    by_id = {item["id"]: item for item in evidence}
    lines = [
        "# Model-selected hypothesis candidates", "",
        "Ollama selected two of three prepared, testable candidates. Python supplied their wording, measured evidence, and run links.",
    ]
    for number, item in enumerate(hypotheses, start=1):
        candidate = candidates[item["type"]]
        lines.extend(["", f"## Candidate {number}: {item['type'].replace('_', ' ')}", "", candidate["description"], ""])
        for heading, ids in (
            ("Supporting observations", item["support_ids"]),
            ("Evidence to weigh against it", item["against_ids"]),
        ):
            lines.extend([f"### {heading}", ""])
            if not ids:
                lines.append("- None selected from these saved runs.")
            for evidence_id in ids:
                fact = by_id[evidence_id]
                lines.append(
                    f"- **{evidence_id}:** {fact['claim']} Sources: {source_links(fact['sources'])}."
                )
            lines.append("")
        lines.extend(["### Missing evidence", "", candidate["missing_evidence"], ""])
    lines.extend(
        [
            "## Evidence boundary", "",
            "Python checked the selected candidate types and exact evidence assignments. The selected hypotheses remain unproven; the saved runs do not establish a causal mechanism or a general effect across seeds.",
        ]
    )
    return "\n".join(lines) + "\n"


def main() -> None:
    parser = argparse.ArgumentParser(description="Generate grounded local hypothesis candidates")
    parser.add_argument("case_id", help="ID from hypothesis_cases.json")
    parser.add_argument("--output-id", required=True, help="new artifact ID")
    args = parser.parse_args()
    if not ID.fullmatch(args.case_id) or not ID.fullmatch(args.output_id):
        parser.error("IDs must use lowercase letters, numbers, underscores, or hyphens")
    cases = json.loads((PROJECT_DIR / "hypothesis_cases.json").read_text(encoding="utf-8"))
    case = next((item for item in cases if item["id"] == args.case_id), None)
    if case is None:
        parser.error(f"unknown case ID: {args.case_id}")

    prompt_path = PROJECT_DIR / "hypothesis_prompts" / f"{args.output_id}.md"
    report_path = PROJECT_DIR / "hypotheses" / f"{args.output_id}.md"
    metadata_path = PROJECT_DIR / "hypotheses" / f"{args.output_id}.json"
    if any(path.exists() for path in (prompt_path, report_path, metadata_path)):
        parser.error("prompt or report already exists; choose a new output ID")

    evidence, candidates = evidence_catalog(case)
    ids = {item["id"] for item in evidence}
    evidence_text = "\n".join(
        f"- {item['id']}: {item['claim']} Sources: {', '.join(item['sources'])}."
        for item in evidence
    )
    candidate_text = "\n".join(
        f"- `{category}`: {candidate['description']} Support: {', '.join(candidate['support_ids'])}. "
        f"Against: {', '.join(candidate['against_ids']) or 'none'}."
        for category, candidate in candidates.items()
    )
    prompt = f"""# Hypothesis selection request

Question: {case['question']}

The evidence items are descriptive facts calculated from saved run JSON. A valid evidence ID does not by itself make a causal explanation true.

{evidence_text}

Prepared candidate hypotheses and their evidence assignments:
{candidate_text}

Select exactly two candidates that are most informative for the question. Return only JSON with a `selected` array. Each selection contains its `type`, `support_ids`, and `against_ids` copied exactly from the prepared candidate list. Do not write any free-text explanation; Python will render the selected candidates and source links.
"""
    prompt_path.parent.mkdir(parents=True, exist_ok=True)
    prompt_path.write_text(prompt, encoding="utf-8")

    evidence_id_schema = {"type": "string", "enum": sorted(ids)}
    response_schema = {
        "type": "object",
        "properties": {
            "selected": {
                "type": "array",
                "items": {
                    "type": "object",
                    "properties": {
                        "type": {"type": "string", "enum": sorted(candidates)},
                        "support_ids": {"type": "array", "items": evidence_id_schema},
                        "against_ids": {"type": "array", "items": evidence_id_schema},
                    },
                    "required": ["type", "support_ids", "against_ids"],
                    "additionalProperties": False,
                },
            }
        },
        "required": ["selected"],
        "additionalProperties": False,
    }
    request_body = {
        "model": MODEL, "stream": False, "think": False,
        "messages": [{"role": "user", "content": prompt}],
        "format": response_schema, "options": OPTIONS,
    }
    request = Request(
        "http://127.0.0.1:11434/api/chat",
        data=json.dumps(request_body).encode("utf-8"),
        headers={"Content-Type": "application/json"}, method="POST",
    )
    with urlopen(request, timeout=300) as response:
        result = json.load(response)
    raw = result["message"]["content"].strip()
    if not result.get("done") or result.get("done_reason") != "stop" or not raw:
        raise RuntimeError("Ollama did not return a complete response")
    parsed = json.loads(raw)
    try:
        hypotheses = validate_hypotheses(parsed, ids, candidates)
    except ValueError as exc:
        rejected_path = PROJECT_DIR / "hypotheses" / f"{args.output_id}.rejected.json"
        rejected_path.parent.mkdir(parents=True, exist_ok=True)
        with rejected_path.open("x", encoding="utf-8") as file:
            json.dump(
                {"reason": str(exc), "model_response": parsed, "evidence_catalog": evidence},
                file,
                indent=2,
            )
            file.write("\n")
        raise RuntimeError(f"Rejected model response saved to {rejected_path}: {exc}") from exc
    report = render_hypotheses(hypotheses, evidence, candidates)
    metadata = {
        "case_id": args.case_id,
        "output_id": args.output_id,
        "prompt_sha256": hashlib.sha256(prompt.encode("utf-8")).hexdigest(),
        "model": result["model"], "options": OPTIONS,
        "generated_at_utc": datetime.now(timezone.utc).isoformat(),
        "prompt_tokens": result.get("prompt_eval_count"),
        "answer_tokens": result.get("eval_count"),
        "evidence_catalog": evidence,
        "candidate_templates": candidates,
        "model_response": parsed,
    }
    report_path.parent.mkdir(parents=True, exist_ok=True)
    with report_path.open("x", encoding="utf-8") as file:
        file.write(report)
    with metadata_path.open("x", encoding="utf-8") as file:
        json.dump(metadata, file, indent=2)
        file.write("\n")
    print(f"Prompt: {prompt_path}")
    print(f"Report: {report_path}")
    print(f"Metadata: {metadata_path}")
    print(f"Model: {result['model']}")
    print(f"Evidence items: {len(evidence)} | hypotheses: {len(hypotheses)}")
    print(f"Prompt tokens: {metadata['prompt_tokens']} | answer tokens: {metadata['answer_tokens']}")


if __name__ == "__main__":
    main()
