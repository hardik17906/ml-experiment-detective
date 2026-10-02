# Local Ollama setup for ML Experiment Detective

## Hardware and model choice

- Windows 11; Intel Core i5-10300H; about 16 GB RAM; NVIDIA GTX 1650 Ti with 4 GB VRAM.
- Chosen first model: `qwen3:1.7b` (about 1.4 GB in the [Ollama model list](https://ollama.com/library/qwen3/tags)). This is a small text model; the larger default `qwen3` tag was not pulled.

## Installed and verified on D:

- Official Windows installer downloaded to `D:\Ollama\OllamaSetup.exe`. Windows Authenticode reported `Valid`, signer `Ollama Inc.`.
- Installed with the documented `/DIR="D:\Ollama"` option. The executable is `D:\Ollama\ollama.exe`, version `0.35.0`.
- Persistent Windows user environment variable: `OLLAMA_MODELS=D:\Ollama\models`.
- Before pulling a model, the server startup log at `D:\Ollama\serve.stderr.log` reported `OLLAMA_MODELS:D:\Ollama\models`, and `/api/tags` returned an empty model list.
- Pulled only `qwen3:1.7b` (digest `8f68893c685c3ddff2aa3fffce2aa60a30bb2da65ca488b61fff134a4d1730e7`). Its manifest and blobs are in `D:\Ollama\models` (about 1.36 GB of model files); the default `C:\Users\ASUS\.ollama\models` folder does not exist.
- A local `/api/chat` smoke test returned `READY.`. `ollama ps` reported the model running `100% GPU` with a 4096-token context during the grounded answer run.
- Ollama created small logs and configuration under the Windows user profile on C:, but the application binaries and downloaded model are on D:.

## Verification commands

```powershell
[Environment]::GetEnvironmentVariable('OLLAMA_MODELS', 'User')
& 'D:\Ollama\ollama.exe' --version
& 'D:\Ollama\ollama.exe' list
& 'D:\Ollama\ollama.exe' ps
```

The local API listens at `http://127.0.0.1:11434`. If it is not running after a restart, launch the installed Ollama app or run `D:\Ollama\ollama.exe serve` in a terminal. The user-level model-path setting must be inherited by the server process; check its startup log before pulling any additional model.

## First grounded answer

- `generate_answer.py` sends a prepared prompt to the local `/api/chat` endpoint with model `qwen3:1.7b`, `temperature=0`, `num_ctx=4096`, `num_predict=512`, `think=false`, and `stream=false`.
- The first raw answer contradicted its own facts. Later raw answers had correct facts but omitted clickable citations. A structured JSON response now supplies `run_id` with each fact; Python checks the IDs and renders source links.
- The first structured answer invented missing measurements. The final factual-answer format asks only for an answer and observed facts; Python adds a fixed caveat about unknown causes.
- The audited result is `answers/held_out_spike_005.md`, with generation settings and the raw structured response in `answers/held_out_spike_005.json`. Earlier attempts remain saved for learning.
- The model's wording still requires fact checking. The audit compared the answer's displayed loss values to the linked run JSON files.
