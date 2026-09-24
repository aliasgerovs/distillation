#!/usr/bin/env bash
# Build .venv for the Distillation Game replication.
# pyproject.toml leaves every dependency unpinned; these pins are one mutually compatible set:
#   - transformers 4.x: run_distill() decodes apply_chat_template() output directly, which needs the
#     4.x behaviour of returning a plain list of token ids.
#   - trl >= 0.20: run_distill() passes SFTConfig(max_length=...), the post-rename argument name.
#   - torch 2.8.0 so the prebuilt flash-attn 2.8.3 wheel matches (building from source takes ~1 h).
set -euo pipefail
cd "$(dirname "$0")/.."

uv venv --python 3.11 --seed .venv
PY=.venv/bin/python

uv pip install --python "$PY" torch==2.8.0 --index-url https://download.pytorch.org/whl/cu128
uv pip install --python "$PY" \
  "transformers==4.56.2" "trl==0.23.1" "peft==0.17.1" "accelerate==1.10.1" \
  "datasets==4.1.1" "math-verify==0.8.0" "latex2sympy2-extended==1.10.2" \
  "pydantic>=2.7" "PyYAML>=6.0.1" "rich>=13.7" "numpy<2.4" "matplotlib" "pandas" "sentencepiece" "hf_transfer"
uv pip install --python "$PY" \
  "https://github.com/Dao-AILab/flash-attention/releases/download/v2.8.3/flash_attn-2.8.3+cu12torch2.8cxx11abiTRUE-cp311-cp311-linux_x86_64.whl"
uv pip install --python "$PY" --no-deps -e .

"$PY" - <<'PY'
import torch, transformers, trl, peft, datasets, flash_attn, math_verify
print("torch", torch.__version__, "cuda", torch.version.cuda, "| transformers", transformers.__version__,
      "| trl", trl.__version__, "| peft", peft.__version__, "| datasets", datasets.__version__,
      "| flash_attn", flash_attn.__version__)
PY
