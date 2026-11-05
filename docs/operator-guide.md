# Operator guide

## Access

The deployment binds dashboard port 8080 and viewer port 6080 to VM loopback only. From an authorized workstation, establish SSH forwards for both ports, then open `http://localhost:8080`. The noVNC link in the dashboard opens the Chromium display. The default viewer is read-only; setting `VNC_INTERACTIVE=1` in `/opt/bitburner-agent/config/.env` and recreating the service enables keyboard and mouse input.

## Service commands

Run these on the VM:

```sh
cd /opt/bitburner-agent/deployment
docker compose --env-file ../config/.env ps
docker compose --env-file ../config/.env logs -f --tail=100
docker compose --env-file ../config/.env restart
docker compose --env-file ../config/.env down
docker compose --env-file ../config/.env up -d --build
```

Use the dashboard controls to start, pause, resume, or emergency-stop bounded sessions. The emergency stop ends the active session; the persistent browser profile is retained. Session objective/result checkpoints and action/error entries live under `/opt/bitburner-agent/data/`.

## Game-specific Browser Use actions

The agent has game-specific actions on the same Browser Use controller:

- `game_observe` and `game_progress` read only the rendered game interface.
- `game_dismiss_dialog` tries one semantic close or Escape action and verifies the dialog disappears.
- `game_terminal(command)` uses the documented Alt+T shortcut when needed, reacquires the visible input, submits one safe single-line command, and returns the rendered result.
- `game_run_script(filename, args)` runs through the in-game terminal and returns its visible result.
- `game_help(topic)` and `game_troubleshoot(error)` return allowlisted local documentation; `game_netscript_reference(symbol)` reads the connected game's version-specific definitions.
- `game_read_script(filename)` and `game_deploy_script(filename, content)` use the restricted Remote API when configured. Deployment verifies read-back and game-calculated RAM.

Generic index-based clicks, arbitrary text entry, browser navigation, and evaluation are removed from the model's tool registry. If a dialog remains after one dismissal attempt or a UI transition cannot be confirmed, inspect with `game_observe` and report the blocker instead of retrying blindly. The model still chooses strategy, authors and debugs Netscript, and confirms progress itself.

## Restricted Remote API bridge

The optional bridge is a sidecar in the agent's private network namespace. It publishes no ports. Set `BITBURNER_REMOTE_API_TOKEN` in the ignored `config/.env` to a random value (`openssl rand -hex 32`), then start the Compose stack. In the game's visible Options > Remote API page, set hostname `localhost`, port `12525`, leave WSS unchecked, and connect. The HTTPS game blocks plain WebSockets to non-loopback hostnames; the shared network namespace makes loopback work without exposing the listener.

The bridge enforces four Remote API operations: read one simple `.js` filename on `home`, write model-authored `.js` content on `home` and read it back, calculate the game's RAM cost for that script, and read the game's official type definitions. It rejects save reads, server enumeration, deletion, bulk file access, path traversal, other servers, and convenience file endpoints. Browser Use still runs scripts through the visible Terminal and observes the visible game.

The optional agent actions are `game_read_script`, `game_deploy_script`, and `game_netscript_reference`. They appear only when both the bridge URL and token are configured. Never put the token in the repository or prompt.

## Inference

Set `OLLAMA_BASE_URL`, `OLLAMA_MODEL`, and `INFERENCE_NODE` in the private `.env` file. Use “Check inference” to inspect `/api/tags`; it does not generate text. The actual inference request must be tested before selecting a model for unattended play.

`MAX_STEPS` bounds each agent session (default 16); `MAX_SESSIONS=0` allows the supervisor to continue until a configured stop condition. `MAX_HISTORY_ITEMS` and `CHECKPOINT_PROMPT_LIMIT` keep continuation prompts compact. `LLM_TIMEOUT`, `STEP_TIMEOUT`, and `OLLAMA_TIMEOUT` bound slow local inference calls; defaults allow up to 150 seconds for a model response within a 180-second step. Tune these values in the private `.env` when the model needs more room or inference latency requires shorter sessions.

## Backups

The VM is included in the Proxmox scheduled backup job, and VM snapshots are kept as deployment rollback points. The active game save is in Chromium's persistent profile. Use the game's visible save UI to export a native `.json.gz` save. The service waits for a completed download, checks its gzip integrity, and archives it under `/opt/bitburner-agent/data/backups/`; it keeps the latest 30 verified exports. `/api/backups` and the dashboard list those exports. No export is considered validated until an actual file appears there.

To restore a verified export, preserve the active profile first, then use the game's visible Import Save UI with a copy of the archived file. Never edit save contents or import a backup to gain progress. Test restoration in a separate browser profile before restoring the primary profile.

## Troubleshooting

- `docker compose ps` and `docker compose logs` show container state and errors.
- `curl http://127.0.0.1:8080/api/health` checks the local control API.
- “Check inference” confirms endpoint reachability and configured model presence without inference generation.
- `/api/backups` reports archived game-native exports and sizes; the service log records successful archive validation.
- If a session stops unexpectedly, review `/api/status`, the latest checkpoint, and `data/logs/actions.jsonl`; start a new session from the latest objective/result.

Instance-specific VM ID, address, endpoint, access key, and tested backup commands belong in an ignored local instance record, never this public guide.
