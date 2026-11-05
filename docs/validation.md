# Validation record

This document records measured results only. A running container alone does not mean the system has passed acceptance.

| Acceptance item | Result | Evidence |
|---|---|---|
| VM boots and receives LAN networking | Passed | Dedicated Ubuntu Server 24.04.5 LTS VM boots, receives a private LAN lease, and responds to SSH and guest-agent queries. |
| Actual Ollama model generation | Passed (basic response) | Configured local Ollama endpoint returned `READY` from `qwen3.6:35b` in 0.81 seconds with thinking disabled and a 48-token cap. A prior 8-token probe was too short to produce a visible answer. |
| Agent browser action in Bitburner | Passed (initial interaction) | Browser Use with `qwen3.6:35b` visually identified the live game's offline-progress popup and clicked its visible close control. The action is recorded in the dashboard log. |
| Official game opens in Chromium | Passed (manual browser check) | Browser Use's Chromium session loaded the official game, displayed the tutorial, and later showed the in-game offline-progress dialog. This does not yet prove model control. |
| Model-controlled browser action | Passed (isolated gameplay cycle) | In a disposable v3.0.1 profile, the model queried the official `getHackingLevel` type, authored `mcp-check.js`, deployed it, corrected the UI navigation after a first run attempt found Terminal hidden, ran it visibly, and observed `mcp-check.js: Hacking Level: 1`. |
| Independently authored money-generating Netscript | Passed in three isolated runs; completion reliability remains incomplete | Runs 17 and 19 showed model-authored scripts running and money increasing from $1.262k to $1.583k. Run 19's visible Terminal output attributed $320.651 to a successful `n00dles` hack, with PID 1 for `hack_n00dles.js`; Hack stayed at level 1. Run 20 showed the model-authored script active, money rising from $1.262k to $1.838k, and $576.303 script production at $0.022/sec; Hack stayed at level 1. The model received visible success evidence in Runs 19 and 20 but did not return a final report. Run 18 failed before execution. See Runs 17–20 in [model-benchmark.md](model-benchmark.md). |
| Netscript creation and execution | Passed in isolated testing; production income also observed | The isolated `mcp-check.js` round trip and execution were verified by rendered output. Separately, the production game later showed positive earnings and progression from model-authored scripts; recovery reliability remains pending. |
| Remote API connection and file round trip | Passed (isolated and production profiles) | Production Options > Remote API shows **Online** at `localhost:12525` with WSS disabled. An authenticated production `pushFile → getFile → calculateRam` round trip returned exact read-back and 1.6 GB for a harmless, unexecuted smoke-test script. The sidecar has no published ports. |
| Production model-authored income attempt | Income demonstrated; recovery reliability pending | Qwen authored and deployed `nuke_n00dles.js` and `hack_n00dles.js`; Terminal showed `Running script with 1 thread, pid 1`. After the browser/container restart, the game's offline-progress dialog reported `Your scripts generated $3.764` during 19 seconds offline. The visible HUD subsequently showed $25.516k and Hacking 17, compared with the prior recorded $1.262k and Hacking 1. This confirms positive script earnings and game progress. Repeated launches later exhausted home RAM; Bitburner reported that `hack_n00dles.js` requires 1.70 GB and could not start it. Running that home-only file while connected to `n00dles` then failed because the script does not exist on that server. The agent has not yet completed a reliable diagnose-and-recover cycle or recorded current stats in its checkpoint. |
| Remote API security boundaries | Passed (isolated bridge) | Unauthenticated health returned 401; save read, server enumeration, and deletion methods were absent (404); convenience file routes and invalid file/server targets were rejected (403). Only home `.js` read/write/RAM and official type definitions remain allowlisted. |
| MCP dependency audit | Passed after remediation | The upstream lockfile initially had 14 production advisories (10 high, 3 moderate, 1 critical). Compatible updates were applied in the isolated checkout; production `npm audit` reported zero vulnerabilities and the TypeScript build passed. |
| Remote live viewer | Passed (tunnel path) | noVNC page and internal VNC connection respond. A workstation SSH tunnel successfully reached both the health API and noVNC page; verify live game display during an agent session remains pending. |
| Core statistics update | Pending | The dashboard observation endpoint now returns a live rendered game UI summary and container RAM usage/limit. The model has not yet created and run a Netscript statistics display. |
| Browser/container restart preserves progress | Passed (profile data) | After a container recreate, Chromium reopened the same persistent profile and the game showed the existing character HUD and offline-progress summary. |
| Checkpoint durability and agent lifecycle | Passed (focused tests) | Tests cover stop, overlap prevention, pause/resume, interruption recovery, terminal-state recovery, atomic checkpoints, stagnation, bounded inference, restricted Remote API actions, guide path resolution, modal handling, terminal error reporting, removal of stale editor guidance, cosmetic redeployment detection, repeat-run protection, constrained in-game `.js` copying, RAM rejection recovery, model reference lookup, persistence of the pending script-run guard across sessions, stable pending-run signatures across changing source/UI with reset after a successful diagnostic, visible progress verification after a duplicate observation, same-host `connect` rejection with different-host connection preserved, multiline runtime-error reporting, and delayed runtime-error metrics. The latest source passes 114 tests in the deployment dependency image with networking disabled (2026-11-05). |
| Auto-resume and session continuation | Production unchanged; benchmark runs isolated | Every isolated trial used `AUTO_RESUME=0` and `MAX_SESSIONS=1`; step and time budgets varied by trial and are recorded in [model-benchmark.md](model-benchmark.md). Each trial was launched explicitly and its disposable containers were removed after a terminal result. Production auto-resume and its persistent objective were not changed by these trials. |
| Local model gameplay benchmark | Three guided Qwen trials demonstrated verified income; Run 21b did not | Earlier baseline and recovery runs did not meet the money-generation acceptance test. Guided Qwen Runs 17, 19, and 20 demonstrated income; Run 18 failed before execution. Run 21b consulted the live `ns.nuke` reference and revised its own script, but confused script location with target root access, repeated blocked runs, and finished with unchanged $1.262k / Hacking 1. Runs 19 and 20 did not return a final report; Run 21b ended on the repeated-failure guard. Qwen3.8 remains unscored because the exact tag is not installed on the local inference endpoint. See [model-benchmark.md](model-benchmark.md). |
| Guided Qwen Run 16 (historical) | Failed; no verified income | An isolated `qwen3.6:35b` trial authored and ran `hack-n00dles.js`, but Bitburner returned a visible no-root runtime error. The model authored a revision using `ns.nuke` but did not run it; it repeated dialog dismissal six times and hit two 180-second inference timeouts. Runs 17 and 19 later demonstrated income; Run 18 failed before execution. See [model-benchmark.md](model-benchmark.md) for the subsequent results. |
| Deterministic visible UI helpers | Passed (disposable integration check) | A fresh semantic label opened Create Program, dismissed a known offline dialog once, and returned actual visible Terminal `ls` output in a copied test profile. Unit tests cover ambiguous targets, runtime-error dialogs, and visible transitions. |
| Tiny local UI-action model | Not run; not integrated | Laya and Fast Browser Use were reviewed for license, capabilities, runtime, and fit. No weights or dependencies were installed. A model was already loaded on shared local inference during this work, so no competing request was started. Neither candidate has Bitburner live-page results; see [ui-action-model-evaluation.md](ui-action-model-evaluation.md). |
| VM backup/snapshot and scheduled backup | Partial | A Proxmox rollback snapshot exists and the VM is included in the existing scheduled backup. The native game-save archive worker is implemented, but no actual exported save has yet been validated or restored. |
| Management exposure and isolation | Passed (configuration) | UFW defaults to deny inbound and allows SSH only from the management LAN. Dashboard and VNC bind to guest loopback, container drops all capabilities and sets `no-new-privileges`; tunnel access uses SSH. |

The production service starts the existing persistent Chromium profile and opens the official game on container startup. After an agent-container recreation, the restricted bridge sidecar had to be recreated too because it shares the agent container's network namespace; the visible Remote API then reconnected and showed Online. A prior one-session Qwen gameplay attempt ran uninterrupted to its 15-step `done` result. It deployed and ran model-authored scripts but did not earn money; the first script targeted an invalid host, and diagnostic output was not retrieved. Production progress from earlier model-authored scripts remains documented above. A fresh read-only check on 2026-11-05 found the production agent terminally failed at session 0 / 0 steps while the game still showed Remote API Online; the persistent browser profile and save were left untouched. No production service or VM restart, agent restart, profile edit, or model-setting change was made. The new Run 19 income evidence came only from its disposable profile; its isolated image has not been deployed to production. Deployment-specific host, VM, model endpoint, and address details remain in ignored local records. Live emergency-stop acceptance remains pending.

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
context budgets. The deployment-image suite passes 86 tests, and the disposable
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

At the time of this check, inference reachability was the immediate blocker. The configured
`qwen3.6:35b` Ollama route returned HTTP 502 from the agent API; a read-only
`/api/tags` request from inside the VM container failed with `No route to host`,
and a workstation request timed out. A fresh workstation check also failed to
reach TCP 22 and 11437; SSH reported `No route to host`. The VM's neighbor
table marked the configured inference host `FAILED`. This points to network
unreachability before the Ollama API, but does not distinguish a powered-off
host from a link, addressing, or filtering problem. Lightweight
model-catalog requests to other local endpoints succeeded, but no generation
was sent and no production endpoint/model setting was changed. One alternate
endpoint already had a model loaded, so no competing inference workload was
started. Metadata for an installed `qwen3:8b` candidate reported tool calling
but no vision capability, so it does not meet this screenshot-and-tools
harness's model preflight. A later isolated trial used a compatible local
vision-and-tools model; results are recorded below.

The visible game remained at the official Bitburner page with Remote API
Online. Its current offline-progress dialog reported `$14.463` generated by
scripts. This is visible game evidence of existing script earnings, but it is
not attributed to the terminally failed sessions and does not replace an
isolated repeatable gameplay trial. A current money/hacking HUD reading was
not captured because the dialog remained open. The agent's action log does show
model-authored `simple_hack.js` deployment and visible `run` attempts, but the
latest session stopped after a RAM-limit error; a successful run and
session-attributed income were not confirmed.

The native save-backup API reported zero archived exports at this check. The
persistent browser profile and prior pre-deploy archives remain intact, but a
game-native export/isolated restore test is still outstanding. No new production
session was started. The configured node was subsequently restarted and used
for an isolated Qwen trial; this does not establish that the production VM's
inference route was rechecked or that production gameplay resumed.

## Isolated seed and completion-gate correction (2026-11-05)

The first post-outage trial stopped before making an inference request because
its seed path contained a nested `profile/` directory. The runner copied that
directory as the Chromium user-data root, so the game opened as a fresh tutorial
with Remote API disconnected. The runner correctly refused to spend inference.
I reconfigured a separate disposable profile through the visible Bitburner
Options UI, saved using the game, recreated its browser session, and verified
Remote API Online in both sessions. The production profile was not used.

An isolated local `gemma4:e4b` (8B, Q4_K_M) trial then wrote and deployed
scripts but did not achieve income. The first run ended after 6 steps: it made
an empty filename read, generated unsupported Netscript calls, received a
malformed structured response, and explicitly reported that it had not run its
script. A completion guard was added and tested so a successful `done` response
for a money/income
objective requires both a visible positive script-run confirmation and an
increased visible balance. The next bounded trial ended exhausted with 11
Browser Use history entries (10 recorded action steps). It made repeated
speculative deployments, received the actual visible `main function` runtime
error, and stopped without running a verified money-making program. The final
visible UI showed the runtime error dialog; no balance increase or hacking
progression was verified. The gate's rejection and acceptance behavior passed
automated tests, but the model still did not complete the objective.

The second trial used 16,384 context, temperature 0.2, seed 7, a 10-step limit,
and a 15-minute session limit. It made 11 inference requests over 7m 04s of
wall-clock session time: 49,501 prompt tokens, 2,927 completion tokens, and
418.2 seconds summed request time. The warm Ollama model reported about 3.75 GB
VRAM allocation; GPU samples peaked at 3.3 GB and 2.1 GB on the two devices,
with utilization samples up to 100%. CPU offload was not independently
measured. Trial state, prompts, and scripts remain in ignored local records.

The initial trial-profile setup problem is corrected. The isolated income
objective remains unmet. The UI-action-model experiment stays deferred until a
local primary model completes the money-generation objective.

## Post-restart Qwen trial (2026-11-05)

After the owner restarted the local inference node, repeated checks found the
Ollama endpoint responding. The model catalog listed `qwen3.6:35b`; `/api/show`
reported completion, vision, tools, and thinking capabilities. Before the run,
`/api/ps` showed no loaded model and the available accelerator devices were
idle. A disposable copy of the saved seed showed Remote API Online before
inference. No production profile or service was used.

Run 12 ended exhausted after 10 Browser Use history steps (10-step cap; 15-
minute session cap). On Bitburner v3.0.1, Qwen queried `ns.hack`, authored and
deployed `hack-n00dles.js`, then visibly ran it; Terminal confirmed PID 1. The
HUD at that confirmation still showed $1.262k and Hack 1. The later runtime
dialog said `formatNumber: Function removed in 3.0.0. Please use
ns.format.number() instead.` The model reported the task incomplete. No income
or hacking progression was verified.

There were 10 inference requests, with 77,964 prompt and 1,314 completion
tokens reported across responses with token counts. Summed reported request
duration was 508.3 seconds; the cold first load took 49.2 seconds. Telemetry
spanned 11m46s. Ollama reported 23.3 GB aggregate VRAM allocation; CPU offload
was not measured. At the post-run sample, the model was still loaded after
benchmark-container cleanup; after the later Run 14 cleanup, `/api/ps` was
empty.

The error itself names the replacement API, but the model did not call
`game_troubleshoot`, query its live definition, or repair and rerun within its
step budget. A version-specific troubleshooting note and session instruction
now require that recovery sequence without providing gameplay code. The final
after-error HUD was not separately captured; the last visible post-run HUD
remained $1.262k / Hack 1. Production was not rechecked or changed after the
inference node restart.

A second isolated Qwen run used the same seed and model with a 16-step and
30-minute cap. Remote API Online was verified, but the copied game profile
opened on a visible offline-progress dialog. Qwen called `game_observe` three
times; the deterministic no-progress/repeated-failure guard stopped the session
after 3 steps. It did not author or deploy a script. This exposed a startup
instruction gap rather than an inference or Remote API outage. The session
prompt now directs the model to read and dismiss an initial dialog once, and
the on-demand troubleshooting note explains how to handle the normal
offline-progress dialog.

The next isolated retry (Qwen3.6:35b, same disposable seed, 16-step and
30-minute caps) confirmed that correction: Qwen dismissed the offline-progress
dialog, then proceeded to terminal observation. The run failed at step 5 when
two Ollama requests failed with `Server disconnected without sending a
response` and then `Failed to connect to Ollama`. Three earlier inference
requests had returned successfully. The session ended without authoring or
deploying Netscript; the final visible state remained $1.262k / Hack 1. The
captured UI showed Remote API Online. The isolated runner removed its
containers; production was not involved.

Afterward, read-only HTTP checks to the inference endpoint returned Ollama
version 0.40.14 and an empty `/api/ps` model list. An SSH process/service-manager check could
not authenticate from this session, so the cause and service-process
provenance of the transient disconnect remain undetermined. No service restart,
inference retry, or production recheck was performed. Across fifteen
documented isolated runs, none has met the acceptance criterion of verified
AI-authored income.

## Read-back / stale-list recovery trial (2026-11-05)

Run 15 used a fresh copy of the disposable Remote API Online seed with
`qwen3.6:35b`, 16,384 context, temperature 0.2, seed 7, a 16-step cap, and a
30-minute session cap. No production service or profile was used. The initial
offline-progress dialog was dismissed successfully.

Qwen scanned nearby servers and made six model-authored deployments across two
filenames. Each `game_deploy_script` result said the write was read-back
verified and included the calculated RAM. Qwen repeatedly treated its earlier
Terminal `ls` output as proof that those later writes had failed. It never
called `game_run_script` or entered a visible `run` command; its final response
explicitly said it had failed. The final visible balance remained $1.262k and
Hacking remained level 1. No income or execution was verified.

The 13 inference attempts produced 12 responses and one read timeout. The
successful responses reported 101,469 prompt and 17,456 completion tokens;
their summed Ollama request duration was 702.5 seconds. The first model-load
duration was 16.1 seconds; trial telemetry spanned 14m57s. `/api/ps` reported
about 23.0 GB aggregate VRAM allocation. Per-device GPU sampling could not
authenticate over SSH, and CPU offload was not measured. After this run, one
verified write without visible execution was made the deployment limit; the
agent must run the latest verified file before attempting another write.
Automated tests cover the limit and its reset after a visible run.
They also verify that the pending run requirement and filename survive a
checkpoint and are restored into the next session.

## Production read-only check (2026-11-05)

At 15:17 UTC, the production control API reported a terminal `failed` state with
zero active steps. The persistent browser remained available, the visible game
reported Remote API Online, and an offline-progress dialog was present. No
browser interaction or service restart was performed. Agent events record
earlier Ollama connection failures. A separate read-only request to the
configured Ollama `/api/tags` endpoint returned HTTP 200 and listed the
configured model. This confirms catalog reachability only; no generation
request was sent after the owner's Ollama/Herd rollout began, so inference
success remains unverified. At 15:23 UTC, the latest gameplay guard was
deployed after a gzip-verified backup of the active profile, checkpoints, logs,
screenshots, and save archives. The agent and bridge containers were recreated
together. The browser reopened the same profile (110 MB), the game Remote API
remained Online, and persisted runtime state remained terminally `failed` with
zero active steps; startup did not resume gameplay. The new deployment image
and deployed source file were verified by digest. No model generation request
was made during this deployment.

At 15:29 UTC, a follow-up deployment added durable storage for the pending
script-run guard. The 90-test suite passed in the candidate image with
networking disabled. Before recreation, a second gzip-verified archive covered
the active profile, checkpoints, logs, screenshots, and save archives. The
agent and bridge restarted together; afterward the browser was ready on the
same 110 MB profile, Remote API remained Online, and runtime remained `failed`
with zero active steps. The running module reported a one-write limit and the
checkpoint restore helper was present. No inference request or gameplay action
was made.

## Production status recheck (2026-11-05, 18:48 UTC)

Read-only checks confirmed the production agent and Remote API bridge containers
are running, but the agent runtime is terminally `failed` at session 0 / 0
steps. The recorded failure followed two failed sessions with Ollama timeouts
and connection errors earlier that day. `AUTO_RESUME=1` and `MAX_SESSIONS=0`
are deployed; a terminal `failed` state remains preserved across startup and
does not automatically revive. The browser is still on the official game, the
Remote API indicator is Online, and an offline-progress dialog reports
`$18.132` of script earnings over 28 seconds offline. This verifies retained
game progress, not current script income rate or the health of the agent loop.

From the production VM, read-only Ollama calls now return version 0.40.14; the
configured `qwen3.6:35b` tag is installed and resident at 65,536 context. No
generation request was sent during this check, so model generation after the
earlier outage remains unverified. The production agent has not been started
again, and no browser interaction, save edit, service restart, or model-setting
change was made. A bounded recovery run requires an available, coordinated
inference window.

## Production update (2026-11-05, 21:30 UTC)

Commit `e99eaea` was deployed after a fresh read-only check confirmed the agent
was terminally failed at session 0 / 0 steps, with the browser ready and the
game Remote API Online. Before replacing the image, an archive of the active
profile, checkpoints, logs, screenshots, and save archives passed gzip
integrity validation. The current checkpoint's SHA-256 still matches the
pre-deployment archive after the update. The previous agent image was retained
as a local rollback tag; service credentials and the private archive remain
outside the public repository.

The candidate image was built from the published source and passed all 114
tests in a network-disabled container with temporary state and a read-only
source mount. Compose recreated the agent and Remote API bridge together. After
recreation, both containers were running, `/api/health` returned `ok` with the
browser ready, the visible game still reported Remote API Online, and the
noVNC page returned HTTP 200. The persistent profile remains mounted at the
same data volume. Runtime state remains terminally `failed` at session 0 / 0
steps; deployment did not start gameplay or send an inference request. The
configured model remains `qwen3.6:35b`, with `AUTO_RESUME=1` and
`MAX_SESSIONS=0`. No save import, profile edit, inference-server change, or
unrelated infrastructure change was made. A new gameplay run still requires a
bounded, coordinated local inference window. The deployed control API's
read-only inference check returned the configured model in the local Ollama
catalog; this confirms model-tag reachability only and does not verify text
generation.
