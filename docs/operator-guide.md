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

## Inference

Set `OLLAMA_BASE_URL`, `OLLAMA_MODEL`, and `INFERENCE_NODE` in the private `.env` file. Use “Check inference” to inspect `/api/tags`; it does not generate text. The actual inference request must be tested before selecting a model for unattended play.

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
