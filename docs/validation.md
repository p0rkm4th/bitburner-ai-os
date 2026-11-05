# Validation record

This document records measured results only. A running container alone does not mean the system has passed acceptance.

| Acceptance item | Result | Evidence |
|---|---|---|
| VM boots and receives LAN networking | Passed | Dedicated Ubuntu Server 24.04.5 LTS VM boots, receives a private LAN lease, and responds to SSH and guest-agent queries. |
| Actual Ollama model generation | Passed (basic response) | Configured local Ollama endpoint returned `READY` from `qwen3.6:35b` in 0.81 seconds with thinking disabled and a 48-token cap. A prior 8-token probe was too short to produce a visible answer. |
| Agent browser action in Bitburner | Passed (initial interaction) | Browser Use with `qwen3.6:35b` visually identified the live game's offline-progress popup and clicked its visible close control. The action is recorded in the dashboard log. |
| Official game opens in Chromium | Passed (manual browser check) | Browser Use's Chromium session loaded the official game, displayed the tutorial, and later showed the in-game offline-progress dialog. This does not yet prove model control. |
| Model-controlled browser action | Passed (isolated gameplay cycle) | In a disposable v3.0.1 profile, the model queried the official `getHackingLevel` type, authored `mcp-check.js`, deployed it, corrected the UI navigation after a first run attempt found Terminal hidden, ran it visibly, and observed `mcp-check.js: Hacking Level: 1`. |
| Netscript creation and execution | Passed (isolated test only) | The model-authored script was pushed through the official Remote API, read back, RAM-calculated at 1.65 GB, executed through the visible in-game Terminal, and confirmed by rendered output. Production money-generating execution remains unverified. |
| Remote API connection and file round trip | Passed (isolated and production profiles) | Production Options > Remote API shows **Online** at `localhost:12525` with WSS disabled. An authenticated production `pushFile → getFile → calculateRam` round trip returned exact read-back and 1.6 GB for a harmless, unexecuted smoke-test script. The sidecar has no published ports. |
| Production model-authored income attempt | Income demonstrated; recovery reliability pending | Qwen authored and deployed `nuke_n00dles.js` and `hack_n00dles.js`; Terminal showed `Running script with 1 thread, pid 1`. After the browser/container restart, the game's offline-progress dialog reported `Your scripts generated $3.764` during 19 seconds offline. The visible HUD subsequently showed $25.516k and Hacking 17, compared with the prior recorded $1.262k and Hacking 1. This confirms positive script earnings and game progress. Repeated launches later exhausted home RAM; Bitburner reported that `hack_n00dles.js` requires 1.70 GB and could not start it. Running that home-only file while connected to `n00dles` then failed because the script does not exist on that server. The agent has not yet completed a reliable diagnose-and-recover cycle or recorded current stats in its checkpoint. |
| Remote API security boundaries | Passed (isolated bridge) | Unauthenticated health returned 401; save read, server enumeration, and deletion methods were absent (404); convenience file routes and invalid file/server targets were rejected (403). Only home `.js` read/write/RAM and official type definitions remain allowlisted. |
| MCP dependency audit | Passed after remediation | The upstream lockfile initially had 14 production advisories (10 high, 3 moderate, 1 critical). Compatible updates were applied in the isolated checkout; production `npm audit` reported zero vulnerabilities and the TypeScript build passed. |
| Remote live viewer | Passed (tunnel path) | noVNC page and internal VNC connection respond. A workstation SSH tunnel successfully reached both the health API and noVNC page; verify live game display during an agent session remains pending. |
| Core statistics update | Pending | The dashboard observation endpoint now returns a live rendered game UI summary and container RAM usage/limit. The model has not yet created and run a Netscript statistics display. |
| Browser/container restart preserves progress | Passed (profile data) | After a container recreate, Chromium reopened the same persistent profile and the game showed the existing character HUD and offline-progress summary. |
| Checkpoint durability and agent lifecycle | Passed (focused tests) | Tests cover stop, overlap prevention, pause/resume, interruption recovery, terminal-state recovery, atomic checkpoints, stagnation, bounded inference, restricted Remote API actions, guide path resolution, modal handling, terminal error reporting, removal of stale editor guidance, cosmetic redeployment detection, repeat-run protection, constrained in-game `.js` copying, RAM rejection recovery, and model reference lookup. The current suite passes 81 tests in a network-disabled container using the deployment image's dependencies. |
| Auto-resume and session continuation | Production unchanged; benchmark runs isolated | The benchmark Compose configuration used `AUTO_RESUME=0`, `MAX_SESSIONS=1`, `MAX_STEPS=24`, and `MAX_SESSION_SECONDS=1800`; every trial was launched explicitly and its disposable containers were removed after a terminal result. Production auto-resume and its persistent objective were not changed by this benchmark. |
| Local model gameplay benchmark | 9 isolated scored trials completed; 0/9 successful | Three trials each for `qwen3.6:35b`, `devstral-small-2:24b-instruct-2512-q4_K_M`, and `gemma4:12b`. No model verified a money-making script; visible starting/final money remained about $1.262k and hacking stayed level 1. Full conditions, per-trial results, hardware data, and recommendation are in [model-benchmark.md](model-benchmark.md). Qwen3.8 was not scored because the existing Ollama endpoint rejected its pull with HTTP 412; its version was not upgraded. |
| Guided local gameplay after documentation and harness changes | Failed; no verified income | Seven isolated `qwen3.6:35b` runs were recorded. The latest authored and deployed `crimes.js`, but visible execution failed because it required 81.60 GB RAM; the model repeated deployment variants without resolving the error. Balance remained about $1.262k, hacking stayed level 1, and verified income was $0. See [model-benchmark.md](model-benchmark.md) for all runs. |
| Deterministic visible UI helpers | Passed (disposable integration check) | A fresh semantic label opened Create Program, dismissed a known offline dialog once, and returned actual visible Terminal `ls` output in a copied test profile. Unit tests cover ambiguous targets, runtime-error dialogs, and visible transitions. |
| Tiny local UI-action model | Not run; not integrated | Laya and Fast Browser Use were reviewed for license, capabilities, runtime, and fit. No weights or dependencies were installed. A model was already loaded on shared local inference during this work, so no competing request was started. Neither candidate has Bitburner live-page results; see [ui-action-model-evaluation.md](ui-action-model-evaluation.md). |
| VM backup/snapshot and scheduled backup | Partial | A Proxmox rollback snapshot exists and the VM is included in the existing scheduled backup. The native game-save archive worker is implemented, but no actual exported save has yet been validated or restored. |
| Management exposure and isolation | Passed (configuration) | UFW defaults to deny inbound and allows SSH only from the management LAN. Dashboard and VNC bind to guest loopback, container drops all capabilities and sets `no-new-privileges`; tunnel access uses SSH. |

The production service starts the existing persistent Chromium profile and opens the official game on container startup. After an agent-container recreation, the restricted bridge sidecar had to be recreated too because it shares the agent container's network namespace; the visible Remote API then reconnected and showed Online. A prior one-session Qwen gameplay attempt ran uninterrupted to its 15-step `done` result. It deployed and ran model-authored scripts but did not earn money; the first script targeted an invalid host, and diagnostic output was not retrieved. Production money remained $1.262k and hacking remained level 1. The current save and browser profile remain preserved, and the production model setting was not changed. The unguided isolated benchmark completed nine runs; none achieved verified income. Two guided trials have now failed before Netscript authoring; their issues and fixes are in [model-benchmark.md](model-benchmark.md). Its recorded outcome and the recommendation to retain Qwen3.6 for now are in [model-benchmark.md](model-benchmark.md). Deployment-specific host, VM, model endpoint, and address details remain in ignored local records. Live emergency-stop acceptance remains pending.

Do not mark this project complete until each required acceptance item has reproducible evidence or a documented infrastructure blocker.

## Latest production update

The latest deployed code fixes two harness defects found during the guided production attempt. First, the official Remote API can return a generic HTTP 500 when `getFile` checks for a script that does not exist; deployment now permits the write only for that exact missing-file response, then requires exact read-back and live RAM calculation. Second, Browser Use automatically generated a `navigate` action from the session URL even though navigation is intentionally excluded from the gameplay tool set; the agent now disables that implicit action because the application owns initial page setup. The rebuilt deployment image passed all 61 tests with network access disabled during the test run.

The persistent production profile and checkpoint were retained during deployment, and the visible Remote API remains Online. The current bounded Qwen session resumed from the saved objective after deployment. Its last confirmed gameplay action before this session was execution of model-authored `startHack.js`; Bitburner reported that `n00dles` requires root access. That run did not establish income. The current session has started, but no new income or progression result is claimed until visible evidence is recorded. The production setting remains `qwen3.6:35b`; no model benchmark workload was started as part of this deployment.

The optional tiny UI-action-model review is documented in [ui-action-model-evaluation.md](ui-action-model-evaluation.md). It remains an isolated evaluation and has not been integrated into production; no end-to-end evidence currently shows that it improves gameplay task performance.

The repeated deployment loop led to commits `f66d656` (detect formatting/JSDoc-only script rewrites), `dca9b9b` (reject an immediate repeat of a visibly successful `run` until a diagnostic Terminal command occurs), `9049640` (route RAM errors to concise process guidance), and `d43b229` (allow only the documented in-game `scp filename.js server` form). These are deployed. The official Bitburner getting-started guide documents `scp` for copying scripts to other servers. After the latest update, the game itself confirmed $3.764 of script-generated offline earnings and later reported `$30.463` of script generation in an offline-progress dialog; the live HUD subsequently showed $25.516k / Hacking 17. The agent's later retry failed because 1.70 GB was unavailable on home, then it connected to `n00dles` and tried to run the home-only file there. The `scp` allowance passed tool tests, but a production round trip is still pending. The supervisor continues from a checkpoint; the production profile and services remain intact. The agent is again spending steps dismissing a visible message dialog and timing out; active-script cleanup remains open. This is evidence of real income generation, but reliable recovery is not yet established. The Tiny UI model would not address the repeated Terminal/dialog reasoning observed so far; no end-to-end A/B result justifies adding it.

Session 7 ended in terminal failure after repeated inference timeouts while attempting to dismiss a message modal. The visible dialog had announced that `fl1ght.exe` was added to home and that the message is stored as `j0.msg`. The rendered UI exposed the content and one visible button, but the old modal detector ignored MUI presentation shells except for the offline earnings dialog. The helper now recognizes this exact visible message pattern and requires a unique visible button before it clicks. Commit `079b3d9` is deployed. Before rebuilding, the current browser profile, checkpoints, and logs were backed up and the gzip archive was verified. Both services are healthy after recreation; the persistent profile remains present, and the visible game reports Remote API Online.

The failed state persisted across container startup. A new session was manually started from the saved objective. Session 1 dismissed the offline earnings popup, scanned the visible network, and model-authored/deployed `hack_n00dles.js` through the restricted Remote API. Its first visible run attempt failed because home lacked the script's required 1.70 GB of free RAM. The model then repeated near-equivalent deployments and timed out three times at 150 seconds. Its final `done` action claimed it had run successfully, but the live Terminal still showed only the RAM error and no positive PID or successful output. The HUD showed $64.466k / hacking 49, but no session-specific money change was measured; this is not evidence that the new script earned income. Session 2 hit a false-positive modal block: the agent reported a visible `presentation` dialog, while the read-only rendered observation showed ordinary game UI and no dialog text. The helper was corrected to ignore presentation-role shells except when visible content matches a known game modal. All 68 tests passed in the network-disabled deployment image, and the fix was deployed as `4229ebf` after backing up the current profile/checkpoints/logs. The VM retained the 117 MB profile, Remote API Online, and the paused state; session 3 resumed from the saved objective. In this session the offline popup was dismissed and a visible `ls` Terminal command succeeded, confirming the false modal block is cleared. Qwen then received the official `ns.hack` reference and read `simple_hack.js`, but it has not confirmed a successful run or income; its latest intended action is to run that script.

The current source troubleshooting guide now explains the game's 1.6 GB minimum script RAM, that API usage adds cost, and why shortening code that uses the same APIs may not reduce the requirement. It directs the agent to inspect active processes and available rooted servers before rewriting or relocating scripts, based on the [official scripts documentation](https://github.com/bitburner-official/bitburner-src/blob/dev/src/Documentation/doc/en/basic/scripts.md). The compact always-loaded guide also now says `run file.js [args]` executes on the currently connected server; arguments do not select a destination. This addresses the latest visible failure, where `run simple_hack.js n00dles` still attempted execution on `home` and failed with the same 1.70 GB RAM error. Commit `10a77ba` was deployed after a verified backup of the current profile/checkpoints/logs. Services are healthy, Remote API is Online, and the profile remains 117 MB. Session 4 was paused at step 6 while repeating code after the visible RAM rejection. The new harness guard records the rejected file/host and blocks redeployment of that same file until `ps`, `mem`, or the visible Active Scripts page has been inspected; its state is restored from the checkpoint after interruption. The full suite passes 73 tests in the deployment image with networking disabled. The guard is validated locally and awaits deployment. A successful run and attributed income are still unverified.

## Isolated reliability follow-up (2026-11-05)

The source now recognizes missing script reads, accepts signature-shaped live
Netscript lookups, clears the repeat-run gate only after a verified changed
script deployment, and dismisses a visible runtime-error dialog once before a
later Terminal action. The benchmark runner has configurable step, time, and
context budgets. The deployment-image suite passes 81 tests, and the disposable
browser integration check handled the known offline dialog, opened a semantic
game tab, and returned the actual visible `ls` result.

Six sequential isolated `gemma4:e4b` runs were made on fresh copies of the same
game seed. No run verified money generation. Runs 04–07 stopped on repeated
missing-file reads or malformed API lookups (75–224 seconds of inference each).
Run 08 authored code and corrected an entry-point error, then failed to reach a
verified run (378.5 seconds of inference). Run 09 used 10 steps and 414.3
seconds of inference, authored and deployed a script, but the game still showed
`RUNTIME ERROR: ... does not have a main function`; no final HUD comparison or
income was recorded. Detailed metrics and the live observations are retained in
ignored local trial records. These were primary-model-only trials, not an
action-model comparison. Laya weights were not downloaded, Fast Browser Use
was not installed, and neither was run against the game. The user-facing
evaluation and recommendation are in [ui-action-model-evaluation.md](ui-action-model-evaluation.md).

At the latest read-only production check, the agent service had a terminal
`failed` state with no active session, the browser was ready, and the in-game
Remote API showed Online. The production profile and model configuration were
left intact. The isolated trials do not meet the income acceptance criterion;
autonomous gameplay remains unverified.

The tested reliability changes were then deployed at that failed-session
boundary. A fresh pre-deploy profile/checkpoint/log archive and source archive
both passed gzip integrity checks. After recreation, the agent and bridge
containers were healthy, Bitburner still showed Remote API Online, and the
persistent profile remained present (101 MB). The runtime state stayed
`failed` with zero active steps, so deployment did not resume gameplay. The
production model setting was not changed.

## Live recheck (2026-11-05)

A fresh read-only check found the control API healthy, the persistent Chromium
browser ready, and the game Remote API still Online. The agent runtime remains
terminally `failed`; the saved runtime state is not eligible for automatic
resume even though the deployed `AUTO_RESUME=1` and `MAX_SESSIONS=0`. Its most
recent failure was repeated inference/tool failure, and the latest checkpoint
also records a script RAM-limit error. The session count and progress were not
reset.

Inference reachability is currently the immediate blocker. The configured
`qwen3.6:35b` Ollama route returned HTTP 502 from the agent API; a read-only
`/api/tags` request from inside the VM container failed with `No route to host`,
and a workstation request timed out. These checks do not establish whether the
inference service itself is down or only unreachable from this VM. Lightweight
model-catalog requests to other local endpoints succeeded, but no generation
was sent and no production endpoint/model setting was changed. One alternate
endpoint already had a model loaded, so no competing inference workload was
started. Metadata for an installed `qwen3:8b` candidate reported tool calling
but no vision capability, so it does not meet this screenshot-and-tools
harness's model preflight. No compatible idle alternate was used for a trial.

The visible game remained at the official Bitburner page with Remote API
Online. Its current offline-progress dialog reported `$14.463` generated by
scripts. This is visible game evidence of existing script earnings, but it is
not attributed to the terminally failed sessions and does not replace an
isolated repeatable gameplay trial. A current money/hacking HUD reading was
not captured because the dialog remained open. The agent's action log does show
model-authored `simple_hack.js` deployment and visible `run` attempts, but the
latest session stopped after a RAM-limit error; a successful run and
session-attributed income were not confirmed.

The native save-backup API currently reports zero archived exports. The
persistent browser profile and prior pre-deploy archives remain intact, but a
game-native export/isolated restore test is still outstanding. No new production
session was started. Resume testing when the configured inference route returns
or a compatible, idle local endpoint can be used by an isolated profile; keep
the production model and profile unchanged meanwhile.
