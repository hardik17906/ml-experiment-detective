"""Fixed worker entry point; never accepts a shell command or model-written code."""

import json
from pathlib import Path
import sys

from v3.experiment_designer import validate_config
from v3.investigation_state import ROOT


def main():
    payload = json.loads(Path(sys.argv[1]).read_text(encoding="utf-8"))
    config = payload["config"]
    validate_config(config)
    expected = ROOT / "runs" / f"{config['run_id']}.json"
    if Path(payload["output_path"]).resolve() != expected.resolve():
        raise ValueError("Worker output must be the fixed run-ID-derived JSON path")
    from phase0 import run_training
    import torch
    torch.set_num_threads(2)
    run_training(config, expected, download=False, provenance=payload["provenance"], max_seconds=600,
                 cancel_path=payload.get("cancel_path"))


if __name__ == "__main__":
    main()
