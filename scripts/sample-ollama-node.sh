#!/usr/bin/env bash
set -euo pipefail
: "${OLLAMA_BASE_URL:?Set a local Ollama endpoint}"
: "${GPU_SSH_TARGET:?Set a private SSH target for GPU telemetry}"
: "${METRICS_OUT:?Set a private output file}"
interval="${SAMPLE_INTERVAL:-5}"
ssh_args=(-o BatchMode=yes -o ConnectTimeout=4 -o IdentitiesOnly=yes -o StrictHostKeyChecking=yes)
if [[ -n "${GPU_SSH_KEY:-}" ]]; then ssh_args+=(-i "$GPU_SSH_KEY"); fi
mkdir -p "$(dirname "$METRICS_OUT")"
while :; do
  stamp="$(date -u +%Y-%m-%dT%H:%M:%SZ)"
  ollama="$(curl --max-time 4 -fsS "${OLLAMA_BASE_URL%/}/api/ps" 2>/dev/null || printf '{}')"
  gpu="$(ssh "${ssh_args[@]}" "$GPU_SSH_TARGET" \
    'nvidia-smi --query-gpu=name,memory.used,memory.total,utilization.gpu --format=csv,noheader' 2>/dev/null || true)"
  python3 - "$METRICS_OUT" "$stamp" "$ollama" "$gpu" <<'PY'
import json, sys
path, stamp, ollama, gpu = sys.argv[1:]
try:
    running = json.loads(ollama)
except json.JSONDecodeError:
    running = {"error": "invalid Ollama /api/ps response"}
row = {"time": stamp, "ollama_ps": running, "gpu_csv": gpu.splitlines()}
with open(path, "a", encoding="utf-8") as f:
    f.write(json.dumps(row, separators=(",", ":")) + "\n")
PY
  sleep "$interval"
done
