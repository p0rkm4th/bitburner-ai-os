# Validation record

This document records measured results only. A running container alone does not mean the system has passed acceptance.

| Acceptance item | Result | Evidence |
|---|---|---|
| VM boots and receives LAN networking | Passed | Dedicated Ubuntu Server 24.04.5 LTS VM boots, receives a private LAN lease, and responds to SSH and guest-agent queries. |
| Actual Ollama model generation | Passed (basic response) | Configured local Ollama endpoint returned `READY` from `qwen3.6:35b` in 0.81 seconds with thinking disabled and a 48-token cap. A prior 8-token probe was too short to produce a visible answer. |
| Agent browser action in Bitburner | Passed (initial interaction) | Browser Use with `qwen3.6:35b` visually identified the live game's offline-progress popup and clicked its visible close control. The action is recorded in the dashboard log. |
| Official game opens in Chromium | Passed (manual browser check) | Browser Use's Chromium session loaded the official game, displayed the tutorial, and later showed the in-game offline-progress dialog. This does not yet prove model control. |
| Model-controlled browser action | Passed (initial interaction) | The model reported the current visible game state (`$1.262k`, level 1, game v3.0.1) and chose the popup close action. Longer gameplay validation is ongoing. |
| Netscript creation and execution | In progress, not passed | The model wrote an income script through the visible Script Editor and Bitburner reported `Identifier 'main' has already been declared`. The checkpoint records the error and a model-generated fix plan; a corrected, successfully running script is still required. |
| Remote live viewer | Passed (tunnel path) | noVNC page and internal VNC connection respond. A workstation SSH tunnel successfully reached both the health API and noVNC page; verify live game display during an agent session remains pending. |
| Core statistics update | Pending | The dashboard observation endpoint now returns a live rendered game UI summary and container RAM usage/limit. The model has not yet created and run a Netscript statistics display. |
| Browser/container restart preserves progress | Passed (profile data) | After a container recreate, Chromium reopened the same persistent profile and the game showed the existing character HUD and offline-progress summary. |
| Checkpoint durability and agent lifecycle | Passed (focused tests) | Seven lifecycle tests cover awaited stop, refusal to overlap sessions, pause/resume, inactivity suspension during pause, recovery after interruption, terminal-state recovery policy, positive BitNode completion confirmation, and preservation of the previous checkpoint after a failed atomic write. |
| Auto-resume and session continuation | Passed (deployed configuration) | The deployed service reports `AUTO_RESUME=1` and `MAX_SESSIONS=0` (unlimited). A container recreate resumed the saved objective and checkpoint; a live session is now continuing. |
| VM backup/snapshot and scheduled backup | Partial | A Proxmox rollback snapshot exists and the VM is included in the existing scheduled backup. The native game-save archive worker is implemented, but no actual exported save has yet been validated or restored. |
| Management exposure and isolation | Passed (configuration) | UFW defaults to deny inbound and allows SSH only from the management LAN. Dashboard and VNC bind to guest loopback, container drops all capabilities and sets `no-new-privileges`; tunnel access uses SSH. |

The service starts the persistent Chromium profile and opens the official game on container startup. Explicit emergency stop clears the durable auto-resume objective; an unplanned process or VM interruption retains it for recovery. Deployment-specific host, VM, model endpoint, and address details are kept in ignored local records. The lifecycle tests validate control and persistence behavior; live emergency-stop acceptance remains pending.

Do not mark this project complete until each required acceptance item has reproducible evidence or a documented infrastructure blocker.
