#!/usr/bin/env bash
set -euo pipefail
: "${TRIAL_ID:?Use a unique ID such as qwen38-01}"
: "${OLLAMA_BASE_URL:?Set the locally hosted Ollama API URL}"
: "${OLLAMA_MODEL:?Set the exact Ollama model tag}"
: "${INFERENCE_NODE:?Set a private descriptive node label}"
: "${GPU_SSH_TARGET:?Set the matching private SSH target for telemetry}"
: "${BENCH_SEED_PROFILE:?Set a copy of the clean seed Chromium profile}"
: "${BENCH_STATE_DIR:?Set a new, private directory for this trial}"
export BENCH_UID="${BENCH_UID:-$(id -u)}"
export BENCH_GID="${BENCH_GID:-$(id -g)}"
export GPU_SSH_KEY="${GPU_SSH_KEY:-}"

if [[ ! "$TRIAL_ID" =~ ^[A-Za-z0-9_-]+$ ]]; then
  echo "TRIAL_ID may contain only letters, numbers, underscores, and hyphens" >&2
  exit 2
fi
if [[ -e "$BENCH_STATE_DIR" ]]; then
  echo "Trial state already exists; refusing to reuse or overwrite it: $BENCH_STATE_DIR" >&2
  exit 2
fi
if [[ ! -d "$BENCH_SEED_PROFILE" ]]; then
  echo "Seed profile does not exist: $BENCH_SEED_PROFILE" >&2
  exit 2
fi

mkdir -p "$BENCH_STATE_DIR/profile" "$BENCH_STATE_DIR/logs"
cp -a "$BENCH_SEED_PROFILE/." "$BENCH_STATE_DIR/profile/"
env_file="${BENCH_ENV_FILE:-local/benchmark-run.env}"
mkdir -p "$(dirname "$env_file")"
printf 'OLLAMA_BASE_URL=%s\nOLLAMA_MODEL=%s\nINFERENCE_NODE=%s\nBENCH_STATE_DIR=%s\nBENCH_UID=%s\nBENCH_GID=%s\nMAX_STEPS=24\nMAX_SESSION_SECONDS=1800\nOLLAMA_NUM_CTX=16384\nOLLAMA_TEMPERATURE=0.2\nOLLAMA_SEED=7\n' \
  "$OLLAMA_BASE_URL" "$OLLAMA_MODEL" "$INFERENCE_NODE" "$BENCH_STATE_DIR" "$BENCH_UID" "$BENCH_GID" > "$env_file"
chmod 600 "$env_file"
project="bitburner-bench-${TRIAL_ID}"
compose=(docker compose --project-name "$project" --env-file config/.env --env-file "$env_file" \
  -f deployment/benchmark.compose.yaml)
sampler_pid=""
cleanup() {
  if [[ -n "$sampler_pid" ]]; then kill "$sampler_pid" 2>/dev/null || true; wait "$sampler_pid" 2>/dev/null || true; fi
  "${compose[@]}" down --remove-orphans >/dev/null 2>&1 || true
}
trap cleanup EXIT INT TERM

export OLLAMA_BASE_URL GPU_SSH_TARGET GPU_SSH_KEY
METRICS_OUT="$BENCH_STATE_DIR/logs/node-metrics.jsonl" \
  scripts/sample-ollama-node.sh >/dev/null 2>&1 &
sampler_pid=$!
"${compose[@]}" up -d --build

for _ in $(seq 1 120); do
  if curl --max-time 3 -fsS http://127.0.0.1:8180/api/health >/dev/null; then break; fi
  sleep 2
done
curl --max-time 3 -fsS http://127.0.0.1:8180/api/health >/dev/null || {
  echo "Benchmark agent did not become healthy" >&2; exit 1;
}
payload="$(python3 -c 'import json,pathlib; print(json.dumps({"objective": pathlib.Path("benchmarks/gameplay-objective.md").read_text()}))')"
curl --max-time 10 -fsS -X POST http://127.0.0.1:8180/api/start \
  -H 'Content-Type: application/json' --data-binary "$payload"

while :; do
  curl --max-time 8 -fsS http://127.0.0.1:8180/api/status > "$BENCH_STATE_DIR/logs/status-latest.json"
  state="$(python3 -c 'import json,sys;print(json.load(open(sys.argv[1])).get("state","unknown"))' \
    "$BENCH_STATE_DIR/logs/status-latest.json")"
  case "$state" in
    completed|exhausted|failed|operator_stopped|stopped) break ;;
  esac
  sleep 5
done
curl --max-time 8 -fsS http://127.0.0.1:8180/api/game-observation \
  > "$BENCH_STATE_DIR/logs/final-game-observation.json" || true
cp "$BENCH_STATE_DIR/logs/status-latest.json" "$BENCH_STATE_DIR/logs/final-status.json"
printf '\nTrial %s ended in state %s. Private evidence: %s/logs\n' \
  "$TRIAL_ID" "$state" "$BENCH_STATE_DIR"
