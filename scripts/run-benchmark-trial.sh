#!/usr/bin/env bash
set -euo pipefail
umask 077
: "${TRIAL_ID:?Use a unique ID such as qwen38-01}"
: "${OLLAMA_BASE_URL:?Set the locally hosted Ollama API URL}"
: "${OLLAMA_MODEL:?Set the exact Ollama model tag}"
: "${INFERENCE_NODE:?Set a private descriptive node label}"
: "${GPU_SSH_TARGET:?Set the matching private SSH target for telemetry}"
: "${BENCH_SEED_PROFILE:=}"
: "${BENCH_CONTINUE_FROM:=}"
: "${BENCH_STATE_DIR:?Set a new, private directory for this trial}"
export BENCH_UID="${BENCH_UID:-$(id -u)}"
export BENCH_GID="${BENCH_GID:-$(id -g)}"
export GPU_SSH_KEY="${GPU_SSH_KEY:-}"
MAX_STEPS="${MAX_STEPS:-24}"
MAX_SESSION_SECONDS="${MAX_SESSION_SECONDS:-1800}"
OLLAMA_NUM_CTX="${OLLAMA_NUM_CTX:-16384}"
OLLAMA_TEMPERATURE="${OLLAMA_TEMPERATURE:-0.2}"
OLLAMA_SEED="${OLLAMA_SEED:-7}"
OLLAMA_THINK="${OLLAMA_THINK:-}"
BENCH_AGENT_PORT="${BENCH_AGENT_PORT:-8180}"
BENCH_VNC_PORT="${BENCH_VNC_PORT:-6180}"
BENCH_OLLAMA_TIMEOUT="${BENCH_OLLAMA_TIMEOUT:-180}"
AGENT_URL="http://127.0.0.1:${BENCH_AGENT_PORT}"
if ! [[ "$MAX_STEPS" =~ ^[1-9][0-9]*$ && "$MAX_SESSION_SECONDS" =~ ^[1-9][0-9]*$ && "$OLLAMA_NUM_CTX" =~ ^[1-9][0-9]*$ ]]; then
  echo "MAX_STEPS, MAX_SESSION_SECONDS, and OLLAMA_NUM_CTX must be positive integers" >&2
  exit 2
fi
if ! [[ "$BENCH_AGENT_PORT" =~ ^[1-9][0-9]{0,4}$ && "$BENCH_VNC_PORT" =~ ^[1-9][0-9]{0,4}$ ]] || \
   ((BENCH_AGENT_PORT > 65535 || BENCH_VNC_PORT > 65535 || BENCH_AGENT_PORT == BENCH_VNC_PORT)); then
  echo "BENCH_AGENT_PORT and BENCH_VNC_PORT must be valid nonzero TCP ports" >&2
  exit 2
fi
python3 - "$BENCH_AGENT_PORT" "$BENCH_VNC_PORT" <<'PY'
import socket, sys
for port in map(int, sys.argv[1:]):
    sock = socket.socket()
    try:
        sock.bind(("127.0.0.1", port))
    except OSError:
        print(f"Loopback port {port} is already in use; choose unused BENCH_AGENT_PORT and BENCH_VNC_PORT before starting a trial.", file=sys.stderr)
        raise SystemExit(2)
    finally:
        sock.close()
PY
if ! [[ "$BENCH_OLLAMA_TIMEOUT" =~ ^[1-9][0-9]{0,2}$ ]] || ((BENCH_OLLAMA_TIMEOUT < 60 || BENCH_OLLAMA_TIMEOUT > 240)); then
  echo "BENCH_OLLAMA_TIMEOUT must be between 60 and 240 seconds" >&2
  exit 2
fi
if [[ -n "$OLLAMA_THINK" && "$OLLAMA_THINK" != "true" && "$OLLAMA_THINK" != "false" ]]; then
  echo "OLLAMA_THINK must be true or false when set" >&2
  exit 2
fi

if [[ ! "$TRIAL_ID" =~ ^[A-Za-z0-9_-]+$ ]]; then
  echo "TRIAL_ID may contain only letters, numbers, underscores, and hyphens" >&2
  exit 2
fi
if [[ -e "$BENCH_STATE_DIR" ]]; then
  echo "Trial state already exists; refusing to reuse or overwrite it: $BENCH_STATE_DIR" >&2
  exit 2
fi
if [[ -n "$BENCH_SEED_PROFILE" && -n "$BENCH_CONTINUE_FROM" ]] || \
   [[ -z "$BENCH_SEED_PROFILE" && -z "$BENCH_CONTINUE_FROM" ]]; then
  echo "Set exactly one of BENCH_SEED_PROFILE or BENCH_CONTINUE_FROM" >&2
  exit 2
fi
if [[ -n "$BENCH_SEED_PROFILE" && ! -d "$BENCH_SEED_PROFILE" ]]; then
  echo "Seed profile does not exist: $BENCH_SEED_PROFILE" >&2
  exit 2
fi
if [[ -n "$BENCH_CONTINUE_FROM" && ! -d "$BENCH_CONTINUE_FROM" ]]; then
  echo "Continuation source does not exist: $BENCH_CONTINUE_FROM" >&2
  exit 2
fi

# Browser Use sends screenshots with its tool prompt, so reject Ollama models
# that cannot accept both image data and tool definitions before starting a trial.
model_metadata="$(python3 - "$OLLAMA_BASE_URL" "$OLLAMA_MODEL" "$OLLAMA_THINK" <<'PY'
import json, sys, urllib.request
base, model, requested_think = sys.argv[1:]
try:
    request = urllib.request.Request(
        base.rstrip("/") + "/api/show",
        data=json.dumps({"name": model}).encode(),
        headers={"Content-Type": "application/json"},
    )
    with urllib.request.urlopen(request, timeout=10) as response:
        show = json.load(response)
except Exception as exc:
    print(f"Ollama model preflight failed for {model}: {type(exc).__name__}", file=sys.stderr)
    raise SystemExit(2)
capabilities = set(show.get("capabilities", []))
missing = {"vision", "tools"} - capabilities
if missing:
    print(f"Model {model} is incompatible with this screenshot-and-tools harness; missing: {', '.join(sorted(missing))}", file=sys.stderr)
    raise SystemExit(2)
thinking = show.get("thinking")
if requested_think:
    expected = requested_think == "true"
    values = thinking.get("values", []) if isinstance(thinking, dict) else []
    if expected not in values:
        print(f"Model {model} does not advertise requested think={expected}; supported values: {values}", file=sys.stderr)
        raise SystemExit(2)
details = show.get("details", {})
metadata = {
    "model_tag": model,
    "family": details.get("family"),
    "parameter_size": details.get("parameter_size"),
    "quantization_level": details.get("quantization_level"),
    "capabilities": sorted(capabilities),
    "thinking": thinking,
}
try:
    request = urllib.request.Request(base.rstrip("/") + "/api/tags")
    with urllib.request.urlopen(request, timeout=10) as response:
        tags = json.load(response).get("models", [])
    match = next((item for item in tags if item.get("name") == model or item.get("model") == model), None)
except Exception as exc:
    print(f"Unable to verify exact model digest for {model}: {type(exc).__name__}", file=sys.stderr)
    raise SystemExit(2)
if not match or not match.get("digest"):
    print(f"Exact model tag {model} is missing from /api/tags or has no digest", file=sys.stderr)
    raise SystemExit(2)
metadata["digest"] = match["digest"]
print(json.dumps(metadata, separators=(",", ":")))
PY
)"

continuation_metadata='{}'
seed_profile_label="$(basename "${BENCH_SEED_PROFILE:-}")"
if [[ -n "$BENCH_CONTINUE_FROM" ]]; then
  continuation_metadata="$(python3 scripts/prepare-benchmark-continuation.py \
    --source "$BENCH_CONTINUE_FROM" --destination "$BENCH_STATE_DIR" \
    --objective benchmarks/gameplay-objective.md --model-json "$model_metadata" \
    --think "${OLLAMA_THINK:-default}" --context "$OLLAMA_NUM_CTX" \
    --temperature "$OLLAMA_TEMPERATURE" --seed "$OLLAMA_SEED")"
  seed_profile_label="continuation:$(basename "$BENCH_CONTINUE_FROM")"
else
  mkdir -p "$BENCH_STATE_DIR/profile"
  cp -a "$BENCH_SEED_PROFILE/." "$BENCH_STATE_DIR/profile/"
fi
mkdir -p "$BENCH_STATE_DIR/logs"
python3 - "$BENCH_STATE_DIR/logs/trial-config.json" "$TRIAL_ID" "$INFERENCE_NODE" \
  "$OLLAMA_THINK" "$OLLAMA_NUM_CTX" "$OLLAMA_TEMPERATURE" "$OLLAMA_SEED" \
  "$MAX_STEPS" "$MAX_SESSION_SECONDS" "$BENCH_OLLAMA_TIMEOUT" \
  "$seed_profile_label" "$model_metadata" "$continuation_metadata" <<'PY'
import datetime, hashlib, json, pathlib, sys
path, trial_id, node, think, context, temperature, seed, steps, seconds, timeout, profile, model_json, continuation_json = sys.argv[1:]
model = json.loads(model_json)
continuation = json.loads(continuation_json)
objective = pathlib.Path("benchmarks/gameplay-objective.md").read_bytes()
config = {
    "trial_id": trial_id,
    "inference_node_label": node,
    "model": model,
    "think_setting": think or "default",
    "context_size": int(context),
    "temperature": float(temperature),
    "seed": int(seed),
    "max_steps": int(steps),
    "max_session_seconds": int(seconds),
    "request_timeout_seconds": int(timeout),
    "seed_profile_label": profile,
    "continuation": continuation,
    "objective_sha256": hashlib.sha256(objective).hexdigest(),
    "created_at_utc": datetime.datetime.now(datetime.timezone.utc).isoformat(),
}
pathlib.Path(path).write_text(json.dumps(config, indent=2) + "\n")
PY
env_file="${BENCH_ENV_FILE:-local/benchmark-run.env}"
mkdir -p "$(dirname "$env_file")"
printf 'OLLAMA_BASE_URL=%s\nOLLAMA_MODEL=%s\nINFERENCE_NODE=%s\nBENCH_STATE_DIR=%s\nBENCH_UID=%s\nBENCH_GID=%s\nBENCH_AGENT_PORT=%s\nBENCH_VNC_PORT=%s\nMAX_STEPS=%s\nMAX_SESSION_SECONDS=%s\nOLLAMA_NUM_CTX=%s\nOLLAMA_TEMPERATURE=%s\nOLLAMA_SEED=%s\nOLLAMA_THINK=%s\nBENCH_OLLAMA_TIMEOUT=%s\n' \
  "$OLLAMA_BASE_URL" "$OLLAMA_MODEL" "$INFERENCE_NODE" "$BENCH_STATE_DIR" "$BENCH_UID" "$BENCH_GID" \
  "$BENCH_AGENT_PORT" "$BENCH_VNC_PORT" \
  "$MAX_STEPS" "$MAX_SESSION_SECONDS" "$OLLAMA_NUM_CTX" "$OLLAMA_TEMPERATURE" "$OLLAMA_SEED" "$OLLAMA_THINK" \
  "$BENCH_OLLAMA_TIMEOUT" > "$env_file"
chmod 600 "$env_file"
project="bitburner-bench-${TRIAL_ID}"
compose=(docker compose --project-name "$project" --env-file config/.env --env-file "$env_file" \
  -f deployment/benchmark.compose.yaml)
sampler_pid=""
cleanup() {
  if [[ -n "$sampler_pid" ]]; then kill "$sampler_pid" 2>/dev/null || true; wait "$sampler_pid" 2>/dev/null || true; fi
  if [[ -d "$BENCH_STATE_DIR/logs" ]]; then
    "${compose[@]}" ps --all > "$BENCH_STATE_DIR/logs/compose-ps.txt" 2>&1 || true
    "${compose[@]}" logs --no-color > "$BENCH_STATE_DIR/logs/compose.log" 2>&1 || true
  fi
  "${compose[@]}" down --remove-orphans >/dev/null 2>&1 || true
}
trap cleanup EXIT INT TERM

export OLLAMA_BASE_URL GPU_SSH_TARGET GPU_SSH_KEY
METRICS_OUT="$BENCH_STATE_DIR/logs/node-metrics.jsonl" \
  scripts/sample-ollama-node.sh >/dev/null 2>&1 &
sampler_pid=$!
"${compose[@]}" up -d --build

for _ in $(seq 1 120); do
  if curl --max-time 3 -fsS "$AGENT_URL/api/health" >/dev/null; then break; fi
  sleep 2
done
curl --max-time 3 -fsS "$AGENT_URL/api/health" >/dev/null || {
  echo "Benchmark agent did not become healthy" >&2; exit 1;
}
remote_api_ready=0
for _ in $(seq 1 30); do
  if curl --max-time 8 -fsS "$AGENT_URL/api/game-observation" \
      > "$BENCH_STATE_DIR/logs/initial-game-observation.json"; then
    if python3 - "$BENCH_STATE_DIR/logs/initial-game-observation.json" <<'PY'
import json, sys
d = json.load(open(sys.argv[1]))
s = d.get("visible_ui", "")
raise SystemExit(0 if "Remote API: Online" in s or "Status:\n\tOnline" in s or "Status: Online" in s else 1)
PY
    then
      remote_api_ready=1
      break
    fi
  fi
  sleep 2
done
if [[ "$remote_api_ready" != 1 ]]; then
  echo "Disposable game did not visibly confirm Remote API Online; refusing to spend model inference." >&2
  exit 1
fi
payload="$(python3 -c 'import json,pathlib; print(json.dumps({"objective": pathlib.Path("benchmarks/gameplay-objective.md").read_text()}))')"
curl --max-time 10 -fsS -X POST "$AGENT_URL/api/start" \
  -H 'Content-Type: application/json' --data-binary "$payload"

poll_failures=0
while :; do
  status_tmp="$BENCH_STATE_DIR/logs/status-latest.json.tmp"
  if ! curl --retry 2 --retry-delay 1 --retry-connrefused --max-time 8 -fsS \
      "$AGENT_URL/api/status" > "$status_tmp"; then
    rm -f "$status_tmp"
    poll_failures=$((poll_failures + 1))
    if ((poll_failures >= 3)); then
      state="api_unavailable"
      printf '{"state":"api_unavailable","poll_failures":%d}\n' "$poll_failures" \
        > "$status_tmp"
      mv "$status_tmp" "$BENCH_STATE_DIR/logs/status-latest.json"
      echo "Benchmark agent API was unavailable for three consecutive status polls; preserving checkpoint and container diagnostics." >&2
      break
    fi
    sleep 5
    continue
  fi
  mv "$status_tmp" "$BENCH_STATE_DIR/logs/status-latest.json"
  poll_failures=0
  state="$(python3 -c 'import json,sys;print(json.load(open(sys.argv[1])).get("state","unknown"))' \
    "$BENCH_STATE_DIR/logs/status-latest.json")"
  case "$state" in
    completed|exhausted|failed|operator_stopped|stopped) break ;;
  esac
  sleep 5
done
cp "$BENCH_STATE_DIR/logs/status-latest.json" "$BENCH_STATE_DIR/logs/final-status.json"
if [[ "$state" == "api_unavailable" ]]; then
  printf '{"available":false,"reason":"agent_api_unavailable"}\n' \
    > "$BENCH_STATE_DIR/logs/final-game-observation.json"
else
  curl --max-time 8 -fsS "$AGENT_URL/api/game-observation" \
    > "$BENCH_STATE_DIR/logs/final-game-observation.json" || \
    printf '{"available":false,"reason":"final_observation_unavailable"}\n' \
      > "$BENCH_STATE_DIR/logs/final-game-observation.json"
fi
printf '\nTrial %s ended in state %s. Private evidence: %s/logs\n' \
  "$TRIAL_ID" "$state" "$BENCH_STATE_DIR"
if [[ "$state" == "api_unavailable" ]]; then exit 1; fi
