#!/bin/zsh
set -euo pipefail

ROOT="$(cd "$(dirname "$0")" && pwd)"
cd "$ROOT"
PYTHON="${PYTHON:-python3}"
MODEL_NAME="vosk-model-small-ru-0.22"
MODEL_DIR="$ROOT/models/$MODEL_NAME"

"$PYTHON" -m venv "$ROOT/.venv"
"$ROOT/.venv/bin/python" -m pip install --upgrade pip
"$ROOT/.venv/bin/python" -m pip install -r "$ROOT/requirements.txt"

if [[ ! -f "$MODEL_DIR/conf/model.conf" ]]; then
  MODEL_BASE="https://huggingface.co/Derur/vosk-models/resolve/main/stt/ru/$MODEL_NAME"
  MODEL_FILES=(
    "README"
    "am/final.mdl"
    "conf/mfcc.conf"
    "conf/model.conf"
    "graph/Gr.fst"
    "graph/HCLr.fst"
    "graph/disambig_tid.int"
    "graph/phones/word_boundary.int"
    "ivector/final.dubm"
    "ivector/final.ie"
    "ivector/final.mat"
    "ivector/global_cmvn.stats"
    "ivector/online_cmvn.conf"
    "ivector/splice.conf"
  )
  for file in "${MODEL_FILES[@]}"; do
    mkdir -p "$MODEL_DIR/$(dirname "$file")"
    curl -fL --connect-timeout 15 "$MODEL_BASE/$file" -o "$MODEL_DIR/$file"
  done
fi

"$ROOT/.venv/bin/python" -m unittest discover -s "$ROOT/tests" -t "$ROOT" -v
printf '\nГотово. Запуск: %s/run.sh\n' "$ROOT"
