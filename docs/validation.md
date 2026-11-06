# Validation record

This document records measured results only. A running container alone does not mean the system has passed acceptance.

**Game scope:** There is no production game. Every Bitburner instance, including the game on the deployed VM, is a test game. The retained shared browser profile is the persistent test profile. Older uses of “production” refer only to the deployed service or VM, never to a separate production game or save.

| Acceptance item | Result | Evidence |
|---|---|---|
| VM boots and receives LAN networking | Passed | Dedicated Ubuntu Server 24.04.5 LTS VM boots, receives a private LAN lease, and responds to SSH and guest-agent queries. |
| Actual Ollama model generation | Passed (basic response) | Configured local Ollama endpoint returned `READY` from `qwen3.6:35b` in 0.81 seconds with thinking disabled and a 48-token cap. A prior 8-token probe was too short to produce a visible answer. |
| Agent browser action in Bitburner | Passed (initial interaction) | Browser Use with `qwen3.6:35b` visually identified the live game's offline-progress popup and clicked its visible close control. The action is recorded in the dashboard log. |
| Official game opens in Chromium | Passed (manual browser check) | Browser Use's Chromium session loaded the official game, displayed the tutorial, and later showed the in-game offline-progress dialog. This does not yet prove model control. |
| Model-controlled browser action | Passed (isolated gameplay cycle) | In a disposable v3.0.1 profile, the model queried the official `getHackingLevel` type, authored `mcp-check.js`, deployed it, corrected the UI navigation after a first run attempt found Terminal hidden, ran it visibly, and observed `mcp-check.js: Hacking Level: 1`. |
| Independently authored money-generating Netscript | Passed in eight isolated runs; extended autonomy remains incomplete | Runs 17, 19, 20, 22, 23, 25, 28, and 34 demonstrated model-authored scripts earning money. Run 34 independently inspected and ran a broken script, diagnosed `ns.getMoney is not a function` from the visible game error, authored and deployed a correction, then verified money rising from $1.262k to $1.838k (+$576 total; +$287 after the corrected run). Hacking remained level 1. It completed 11 actions in 5m13s with one runtime error, one dialog recovery, no inference transport failures, and one malformed progress baseline argument. See Runs 17–34 in [model-benchmark.md](model-benchmark.md). |
| Netscript creation and execution | Passed in isolated testing; persistent test-profile income also observed | The isolated `mcp-check.js` round trip and execution were verified by rendered output. The retained test profile later showed positive earnings and progression from model-authored scripts; recovery reliability remains pending. |
| Remote API connection and file round trip | Passed (isolated and persistent test profiles) | The retained test profile's Options > Remote API showed **Online** at `localhost:12525` with WSS disabled. An authenticated `pushFile → getFile → calculateRam` round trip returned exact read-back and 1.6 GB for a harmless, unexecuted smoke-test script. The sidecar has no published ports. |
| Model-authored income in the persistent test profile | Income demonstrated; recovery reliability pending | Qwen authored and deployed `nuke_n00dles.js` and `hack_n00dles.js`; Terminal showed `Running script with 1 thread, pid 1`. After the browser/container restart, the game's offline-progress dialog reported `Your scripts generated $3.764` during 19 seconds offline. The visible HUD subsequently showed $25.516k and Hacking 17, compared with the prior recorded $1.262k and Hacking 1. This confirms positive script earnings and game progress. Repeated launches later exhausted home RAM; Bitburner reported that `hack_n00dles.js` requires 1.70 GB and could not start it. Running that home-only file while connected to `n00dles` then failed because the script does not exist on that server. The agent has not yet completed a reliable diagnose-and-recover cycle or recorded current stats in its checkpoint. |
| Remote API security boundaries | Passed (isolated bridge) | Unauthenticated health returned 401; save read, server enumeration, and deletion methods were absent (404); convenience file routes and invalid file/server targets were rejected (403). Only home `.js` read/write/RAM and official type definitions remain allowlisted. |
| MCP bridge discovery and auth | Passed (disposable no-network container) | Unauthenticated REST/MCP requests returned 401. Authenticated MCP discovery listed only health, script read/write, RAM calculation, and official definitions. Save-read calls were unknown; traversal and non-home targets were rejected. An allowed write reached the bridge but correctly failed with no game attached. A live-game round trip remains separately required. Raw MCP does not carry the Browser Use adapter's deploy/run sequence guard. |
| Agent Zero isolated MCP setup | Passed (non-inference only) | Its own MCP client discovered the restricted tool list, observed the expected disconnected-game error, and received denials for forbidden calls. The app responded inside its container. Host UI publication was withheld because the isolated internal-only network did not expose it under the rootless daemon. No model or game was connected; gameplay comparison remains pending until tool and browser capabilities match. See [agent-zero-evaluation.md](agent-zero-evaluation.md). |
| MCP dependency audit | Passed after remediation | The upstream lockfile initially had 14 production advisories (10 high, 3 moderate, 1 critical). Compatible updates were applied in the isolated checkout; production `npm audit` reported zero vulnerabilities and the TypeScript build passed. |
| Remote live viewer | Passed (tunnel path) | noVNC page and internal VNC connection respond. A workstation SSH tunnel successfully reached both the health API and noVNC page; verify live game display during an agent session remains pending. |
| Core statistics update | Pending | The dashboard observation endpoint now returns a live rendered game UI summary and container RAM usage/limit. The model has not yet created and run a Netscript statistics display. |
| Browser/container restart preserves progress | Passed (profile data) | After a container recreate, Chromium reopened the same persistent profile and the game showed the existing character HUD and offline-progress summary. |
| Checkpoint durability and agent lifecycle | Test-game service source `60480e5` deployed; 152/152 tests passed | Coverage includes stop, overlap prevention, pause/resume, interruption and terminal-state recovery, atomic checkpoints, stagnation, bounded inference, restricted Remote API actions, guide loading, modal handling, terminal error reporting, stale editor guidance removal, repeat-run protection, constrained in-game `.js` copying, RAM rejection recovery, current API lookup, dialog detection, tutorial controls, verified money progress, and malformed baseline rejection. The network-disabled pinned container suite passed before deployment; the same source was rebuilt on the VM. |
| Auto-resume and session continuation | Deployed test-game service preserves operator stop; isolated benchmarks remain bounded | Every isolated trial used `AUTO_RESUME=0` and `MAX_SESSIONS=1`; step and time budgets varied by trial and are recorded in [model-benchmark.md](model-benchmark.md). Each trial was launched explicitly and its disposable containers were removed after a terminal result. The deployed test-game service retains `AUTO_RESUME=1` and `MAX_SESSIONS=0`; its persisted `operator_stopped` state was preserved across the update. |
| Local model gameplay benchmark | Eight isolated Qwen trials demonstrated verified income; extended autonomy and BitNode progression remain unverified | Runs 17, 19, 20, 22, 23, 25, 28, and 34 demonstrated income; Runs 18, 21b, 24, 26, and 27 did not. Run 34 recovered from a visible Netscript runtime error and verified a corrected script's contribution to a $287 post-correction money increase. Run 27 exposed the prior-PID collision fixed in the current candidate. Qwen3.8 remains unscored because the exact tag is not installed on the local inference endpoint. See [model-benchmark.md](model-benchmark.md). |
| Qwen client-options retest | Inference reliability improved; gameplay recovery failed | An isolated same-seed Qwen3.6:35b trial used explicit 16,384 context and `think=false`; all 11 requests completed without timeout (82,576 prompt and 3,025 completion tokens; 18.4–32.6 seconds/request). Qwen authored and deployed a script, but its first execution failed for lack of root access. After an authored revision, the next run returned the same old line-10 runtime error. The saved DOM shows the modal heading split into `RUNTIME` and `ERROR`; the detector required contiguous text at the time. A regression fix now normalizes visible whitespace before matching. No income or progress is claimed for this trial. Isolated artifacts remain private under ignored `local/benchmark-runs/`. |
| Run 33/34 Type Error recovery | Passed in an isolated follow-up | Run 33 exposed the bare-div `TYPE ERROR` surface and repeated dismissal failure. In Run 34, Qwen independently ran the saved `hack.js`, received the visible `ns.getMoney is not a function` error through the fresh-snapshot dialog handling, diagnosed the invalid call, authored and deployed a replacement, ran it visibly, and verified money growth. No code or correction was given to the model. The private Run 34 evidence includes model conversations, visible observations, action history, Ollama metrics, and final state. |
| Deterministic UI helper integration | Passed (offline and disposable live browser) | The pinned container passed 149/149 offline tests. A disposable Chromium profile completed the visible tutorial `Next` transition, explicit tutorial exit, allowlisted tab navigation, and a Terminal `ls`; the validator checks output after the latest command prompt so stale tutorial errors cannot masquerade as a successful run. The check used no model inference and did not touch the shared test profile. |
| Guided Qwen Run 16 (historical) | Failed; no verified income | An isolated `qwen3.6:35b` trial authored and ran `hack-n00dles.js`, but Bitburner returned a visible no-root runtime error. The model authored a revision using `ns.nuke` but did not run it; it repeated dialog dismissal six times and hit two 180-second inference timeouts. Runs 17 and 19 later demonstrated income; Run 18 failed before execution. See [model-benchmark.md](model-benchmark.md) for the subsequent results. |
| Deterministic visible UI helpers | Passed (disposable integration check) | A fresh semantic label opened Create Program, dismissed a known offline dialog once, and returned actual visible Terminal `ls` output in a copied test profile. Unit tests cover ambiguous targets, runtime-error dialogs, and visible transitions. |
| Tiny local UI-action model | Not run; not integrated | Laya and Fast Browser Use were reviewed for license, capabilities, runtime, and fit. No weights or dependencies were installed. A model was already loaded on shared local inference during this work, so no competing request was started. Neither candidate has Bitburner live-page results; see [ui-action-model-evaluation.md](ui-action-model-evaluation.md). |
| VM backup/snapshot and scheduled backup | Partial (shared test-game periodic exporter deployed; first scheduled exporter trigger pending) | A Proxmox rollback snapshot exists and the VM is included in the existing scheduled backup. Native export/archive and isolated restore passed. The periodic visible UI export and archive path passed in a disposable profile and is now deployed; its first six-hour scheduled trigger has not yet been observed. |
| Management exposure and isolation | Passed (configuration) | UFW defaults to deny inbound and allows SSH only from the management LAN. Dashboard and VNC bind to guest loopback, container drops all capabilities and sets `no-new-privileges`; tunnel access uses SSH. |

The deployed test-game service starts the existing persistent Chromium profile and opens the official game on container startup. After an agent-container recreation, the restricted bridge sidecar had to be recreated too because it shares the agent container's network namespace; the visible Remote API then reconnected and showed Online. A prior one-session Qwen gameplay attempt ran uninterrupted to its 15-step `done` result. It deployed and ran model-authored scripts but did not earn money; the first script targeted an invalid host, and diagnostic output was not retrieved. Shared test-game progress from earlier model-authored scripts remains documented above. A fresh read-only check on 2026-11-05 found the deployed agent service was terminally failed at session 0 / 0 steps while the game still showed Remote API Online; the persistent browser profile and save were left untouched. No deployed service or VM restart, agent restart, profile edit, or model-setting change was made. The new Run 19 income evidence came only from its disposable profile; its isolated image has not been deployed to the shared test-game service. Deployment-specific host, VM, model endpoint, and address details remain in ignored local records. Live emergency-stop acceptance remains pending.

Do not mark this project complete until each required acceptance item has reproducible evidence or a documented infrastructure blocker.

## Earlier deployed-service update (historical)

The latest deployed code fixes two harness defects found during a guided attempt on the deployed test-game service. First, the official Remote API can return a generic HTTP 500 when `getFile` checks for a script that does not exist; deployment now permits the write only for that exact missing-file response, then requires exact read-back and live RAM calculation. Second, Browser Use automatically generated a `navigate` action from the session URL even though navigation is intentionally excluded from the gameplay tool set; the agent now disables that implicit action because the application owns initial page setup. The rebuilt deployment image passed all 61 tests with network access disabled during the test run.

The persistent shared test profile and checkpoint were retained. A later bounded Qwen session was explicitly stopped after it timed out twice; the API confirmed `operator_stopped`, and the browser/game remained available with Remote API Online. No income or progression is attributed to that session. At that point the deployed service remained at commit `6c77967`; the explicit Ollama client options and split-line modal fix described above are candidate source changes, not yet deployed. The isolated Run 24 profile was disposable and the shared persistent test profile was not modified.

The optional tiny UI-action-model review is documented in [ui-action-model-evaluation.md](ui-action-model-evaluation.md). It remains an isolated evaluation and has not been integrated into production; no end-to-end evidence currently shows that it improves gameplay task performance.

The repeated deployment loop led to commits `f66d656` (detect formatting/JSDoc-only script rewrites), `dca9b9b` (reject an immediate repeat of a visibly successful `run` until a diagnostic Terminal command occurs), `9049640` (route RAM errors to concise process guidance), and `d43b229` (allow only the documented in-game `scp filename.js server` form). These are deployed. The official Bitburner getting-started guide documents `scp` for copying scripts to other servers. After the latest update, the game itself confirmed $3.764 of script-generated offline earnings and later reported `$30.463` of script generation in an offline-progress dialog; the live HUD subsequently showed $25.516k / Hacking 17. The agent's later retry failed because 1.70 GB was unavailable on home, then it connected to `n00dles` and tried to run the home-only file there. The `scp` allowance passed tool tests, but a shared-test-profile round trip was still pending at that point. The supervisor continues from a checkpoint; the shared test profile and services remain intact. The agent is again spending steps dismissing a visible message dialog and timing out; active-script cleanup remains open. This is evidence of real income generation, but reliable recovery is not yet established. The Tiny UI model would not address the repeated Terminal/dialog reasoning observed so far; no end-to-end A/B result justifies adding it.

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
Remote API showed Online. The shared test profile and model configuration were
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
inference route was rechecked or that test gameplay resumed.

## Isolated seed and completion-gate correction (2026-11-05)

The first post-outage trial stopped before making an inference request because
its seed path contained a nested `profile/` directory. The runner copied that
directory as the Chromium user-data root, so the game opened as a fresh tutorial
with Remote API disconnected. The runner correctly refused to spend inference.
I reconfigured a separate disposable profile through the visible Bitburner
Options UI, saved using the game, recreated its browser session, and verified
Remote API Online in both sessions. The shared test profile was not used.

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
inference. No shared test profile or service was used.

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
generation. The native-save backup endpoint currently reports zero archived
exports; periodic backup capture is implemented, but a visible game-native
export and isolated restore have not yet been verified.

## Production update (2026-11-05, 23:26 UTC)

Commit `e55905f` was deployed after a fresh API check showed the agent
terminally failed at session 0 / 0 steps. A gzip-verified private archive of
the persistent data volume was made before recreation. Its checkpoint SHA-256
remained unchanged after deployment. The prior image remains tagged for
rollback; the source release is staged locally and on the VM.

The candidate image was rebuilt from the committed source and passed all 118
tests on the VM with networking disabled. The agent and Remote API bridge were
recreated together. Afterward both containers were running, `/api/health`
reported the browser ready, noVNC returned HTTP 200, the visible game still
reported Remote API Online, and the same persistent `/state` data mount
remained attached (profile directory: 113,131,646 bytes). Runtime state remains
terminally `failed` at session 0 / 0 steps, despite `AUTO_RESUME=1` and
`MAX_SESSIONS=0`; deployment did not start gameplay or send an inference
request. No save import, model setting change, or unrelated service change was
made. At the time of this deployment check, native save export and isolated
restore remained unverified; the later verification is recorded below.

## Native save export and restore verification (2026-11-06)

Using a copy of the successful isolated Run 23 profile, the official Options →
System → Export Game control produced a 10,303-byte Bitburner `json.gz` save.
The gzip stream passed integrity validation. Bitburner's visible Import Game
flow accepted it as valid and restored it into a distinct copy of the clean
seed profile. Before import the test profile showed $1.262k / Hack 1; after
import it showed $3.461k / Hack 1 and an offline-progress message reporting
$220.624 in script earnings. The screenshot and source profile are retained
only in ignored local test artifacts.

The same visible Export Game action was then performed once in the shared test game,
while the browser was already on Options → System. It generated a 15,971-byte
native save; the production service remained up and the browser stayed on the
same game page. The archive worker validated the gzip and moved it from
`/state/saves` into its bounded backup store. The read-only backup API then
reported one archived export. No save was imported into the shared test game, no agent
inference was started, and the existing browser profile and active game scripts
were left running. Production runtime remained terminally failed at session 0 / 0
steps. The archive worker currently waits for exports; it does not yet generate
them periodically. The later isolated periodic-trigger test below closes that
source-validation gap; deployment to the shared test-game service remains pending.

## Periodic native export trigger test (2026-11-06)

The updated candidate image ran against a disposable copy of the Run 23 browser
profile with `AUTO_RESUME=0`, no inference endpoint configured, a 60-second
export interval, no host-published ports, and bounded container resources. The
browser opened the official game and the worker acknowledged the visible
offline-progress dialog once. It then used the visible Options → System → Export
Game control and recorded the downloaded native save (`bitburnerSave_…_BN1x1.json.gz`,
10,229 bytes). After the stability window, the worker archived it; the test
instance's backup API reported one archive and `gzip -t` passed. The instance
remained stopped with zero gameplay steps and was removed after the test. This
validates the scheduled trigger and archive path in isolation. It has **not**
not yet been deployed to the shared test-game service at that point; the
shared test profile and running services were not touched. The rebuilt deployment image passed all 122 tests in
a network-disabled run before this disposable browser test.

## Production deployment of periodic export and lifecycle fix (2026-11-06)

Commit `6c77967` was deployed to the existing dedicated VM after a fresh
read-only check found no active agent session (runtime state was terminally
failed at session 0 / 0 steps). Before replacing the containers, the existing
Chromium profile and runtime data were archived and the archive passed gzip
integrity validation. A fresh native export was also produced through the
visible Options → System → Export Game UI; the file was 16,080 bytes and was
validated and retained by the existing archive worker. The prior agent image
was kept as a rollback tag. The production image passed all 122 tests in a
network-disabled container with temporary writable state.

After recreation, both services were running, `/api/health` reported the
browser ready, noVNC returned HTTP 200, and the visible game still reported
Remote API Online. The browser restored the existing save and showed an offline
progress dialog reporting $93.428 of script earnings over 3 minutes 26 seconds.
After dismissing that known dialog once with the visible game helper, the HUD
showed $71.626k and Hacking 144 (before restart: $71.532k / Hacking 143). The
agent remained terminally failed, and no inference request or gameplay session
was started. The configured model was present at the local Ollama endpoint, but
this deployment check did not verify text generation. The periodic exporter is
deployed with a six-hour default; its first scheduled production trigger is
still pending. No save was imported and no model or inference-server setting
was changed.

## Historical deployed service update — commit `53d398e`

The production agent was already `operator_stopped` before deployment. The game
had a visible active script, so the existing browser profile was backed up
before recreating the containers. The profile archive passed `gzip -t` and a
SHA-256 checksum was recorded in the private deployment record. The prior
native Bitburner exports were retained. The application and restricted bridge
were recreated from the release; the agent remained `operator_stopped` at
session 0 / 0 steps, browser health returned ready, noVNC returned HTTP 200,
and the in-game Remote API showed Online. On reopen, Bitburner displayed its
offline-progress dialog with $25.172 in script-generated earnings, confirming
that the save and active-script progress survived the brief container restart.
The production env now explicitly sets the tested model options and records
request metrics. No production model request was started during deployment.
The previous application image and private env backup remain available for
rollback. Deployment-specific identifiers and backup checksums are kept in
ignored local records.

## Pending-deployment execution guard — source candidate (2026-11-06)

Run 26 showed that Qwen could successfully deploy a script, then spend the
remaining actions reading files and running diagnostics without executing it.
The candidate harness now blocks Remote API reads, reference lookups, unrelated
Terminal commands, and task completion until that exact deployed file receives
a visible run attempt from the visible `home` prompt. If the browser is
connected elsewhere, the agent may connect home once. This is a deterministic
workflow guard; it does not write code or select gameplay strategy.

The complete suite passes 128 tests in the pinned deployment image with
networking disabled and temporary state. Tests cover blocking reads and
references, preventing unrelated Terminal commands, requiring the home prompt,
clearing the guard after a visible run attempt, and refusing task completion
while a deployment is pending. This source candidate has not yet been deployed
to the shared persistent test profile. A fresh isolated Qwen trial will test
whether the guard improves completed gameplay.

Run 27 exercised the guard in a disposable test profile but failed to earn
money. Qwen visibly ran `hack.js` and received a root-access error, then issued
the invalid Terminal command `nuke n00dles`. After it deployed a revised
`hack.js`, the pending-run guard blocked further detours, but an existing
same-filename PID guard also blocked the required new run. A regression test
now confirms that the current source allows a pending changed deployment to
run once and still blocks an immediate repeat; the full suite passes 128/128.
Run 27 ended after 14 actions with one model timeout
and three subsequent Ollama connection failures; the final screenshot showed
$1.262k / Hacking 1 with no verified earnings. Its evidence is isolated under
ignored local benchmark records. The revised duplicate-run behavior still needs
another isolated gameplay trial; the source has not been deployed to the shared
persistent test profile.

Run 28 completed that isolated follow-up. The pending-deployment gate blocked a
premature `tail` attempt and required a visible run; the revised-file/PID
collision no longer occurred. After using the visible error to debug its own
script, Qwen observed successful in-game output and a balance increase from
$1.262k to $1.551k (+$289). The full task ended `completed` after 14 actions,
with two game errors, zero tool failures, and no inference timeout. Hacking
level remained 1. This demonstrates one successful bounded income objective;
it does not establish dependable long-term autonomy or BitNode completion.


## Latest deployed test-game service update — commit `ed08cb1` (2026-11-06)

The `ed08cb1` source was built and validated in a network-disabled container;
all 128 tests passed. The previous deployed release remains available as a
rollback image and source release. Before recreation, the service was
`operator_stopped`, with no active session, and the browser was ready. The
agent and restricted Remote API sidecar were recreated from the new release;
the existing persistent data mount was retained.

After startup, both services were healthy, the dashboard health API reported
the browser ready, noVNC returned HTTP 200, and the visible game still showed
Remote API Online. The game displayed its normal offline-progress dialog with
`Your scripts generated $3.057` during seven seconds offline, confirming that
the shared test-game save and script progress survived the restart. The agent
remained `operator_stopped` at session 0 / 0 steps. The effective service
configuration is `AUTO_RESUME=1`, `MAX_SESSIONS=0`; startup preserved the
explicit stop, so no gameplay or inference request was started. No save was
imported and no model configuration was changed. A live bridge check returned
401 without a bearer token and 200 with its configured token; the forbidden
`getSaveFile` route returned 404. No write operation was sent.

## Dialog-dismissal recovery guard deployment — commit `c3617d6` (2026-11-06)

Run 29's isolated trace showed repeated dismissal requests after the runtime
error modal had already closed. The game tool now returns `NO_PROGRESS` without
input when no dialog is visible, includes any remaining rendered Terminal
error for diagnosis, and permits another close only when a new modal is
visible. The pinned suite passed 131 tests in a network-disabled container.

The deployed test-game service was verified `operator_stopped` at session 0 /
0 steps before update. A gzip-validated archive of the persistent profile,
checkpoints, logs, screenshots, and native save backups was made before
recreation. The agent and restricted Remote API sidecar were recreated from
`c3617d6`; the data mount and service configuration were retained. After
startup, the health API reported the browser ready, both containers were
running, noVNC returned HTTP 200, and the visible game showed Remote API
Online. The agent remains `operator_stopped` at session 0 / 0 steps; no
gameplay or inference request was started. The visible game presented its
offline-progress dialog after restart. Source hashes in the running image
matched the deployed release for the dialog tool, system prompt, and detailed
agent guides. No save import or inference-server change was made.

## Gameplay instruction and progress-parser update — commit `aef25b7`

Run 31 showed Qwen attempting to hack before confirming visible root access,
using an un-awaited Netscript action, and rewriting a deployed script instead
of running it. The compact session instructions now state these workflow
prerequisites without supplying a target strategy or script. This release also
contains the corrected multiline visible-money parser from `43cef04`. The
pinned offline test image passed **133/133** tests with networking disabled.

Before update, the shared persistent test-game service was confirmed
`operator_stopped` at session 0 / 0 steps, with the browser ready and Remote
API Online. A gzip-validated archive of persistent data was retained, and the
previous agent image was tagged for rollback. Both containers were recreated
from `aef25b7` with the same data mount and private configuration. Afterward,
the health API reported `browser_ready`, both containers were running, noVNC
returned HTTP 200, and visible game UI still reported Remote API Online. The
service remained `operator_stopped` at session 0 / 0 steps. Prompt and game
tool source hashes in the image matched the checked-out release. No inference
request was made, and no Bitburner game is designated as production.

## Bitburner Type Error detector deployment — commit `21ff969` (2026-11-06)

Run 33 exposed a Bitburner v3.0.1 script-error panel rendered without dialog
roles or a MUI dialog root. Source commit `21ff969` recognizes that visible
error surface and permits dismissal only through a unique, currently visible
Close control in a fresh Browser Use accessibility snapshot. The pinned test
image passed all **142/142** offline tests before deployment. The exact error
panel could not be reproduced after reloading the disposable profile, so live
dismissal remains unverified.

Before recreating the deployed service containers, the shared persistent test
game reported `operator_stopped`, session 0 / 0 steps. A gzip-validated,
SHA-256-checked archive of the complete persistent data directory was retained
for rollback. Only the agent and restricted Remote API bridge containers were
recreated; their existing `/state` mount and private configuration were kept.
After startup, health reported `browser_ready`, the agent remained
`operator_stopped` at session 0 / 0 steps, the in-game Remote API showed Online,
noVNC returned HTTP 200, and both management listeners remained loopback-only.
No gameplay action, inference request, or save import was performed. The
private archive path and checksum are recorded only in the ignored local
instance record.

## Tutorial recovery and Run 34 deployment — commit `75e23e5` (2026-11-06)

Commit `75e23e5` adds a bounded `game_tutorial` action for a visible `Next` or
deliberately selected `Exit Tutorial` button, detects and reports a tutorial
block on a Terminal command, and verifies each resulting UI transition. The
fresh-selector logic also accepts native buttons without explicit ARIA roles.
The pinned container passed 149/149 offline tests. A disposable live Chromium
check verified tutorial advancement and exit, visible-tab navigation, and a
successful latest Terminal `ls`; it ran without model inference.

Before deployment, the shared test game was `operator_stopped` at session 0 /
0 steps, with the Remote API Online. A new verified archive of the persistent
data and a rollback image tag were created. The agent and restricted bridge
containers were rebuilt and recreated from `75e23e5` using the same persistent
data mount and private configuration. After startup, the service reported
`browser_ready`, remained `operator_stopped` at session 0 / 0 steps, retained
`AUTO_RESUME=1`, showed the game Remote API Online, and returned HTTP 200 from
noVNC. Management ports remained bound to guest loopback. The browser showed an
offline-progress dialog. An earlier check treated its first dollar figure as
the HUD balance; that was not valid evidence, so no before/after HUD balance is
claimed for this deployment. A later restart displayed `$3.515` of script
earnings during 9 seconds offline, but the current balance remained behind the
dialog and was not read. No shared-game action or inference request was made
during deployment. Instance-specific backup, node, address, and access details
remain in ignored local records.

## Progress-baseline validation deployment — commit `60480e5` (2026-11-06)

Commit `60480e5` rejects malformed visible-money and hacking-level baselines
with actionable errors while still returning the observed game statistics.
Three regression cases were added; the pinned suite passed 152/152 tests.
Before deployment, the shared persistent test game was stopped at session 0 /
0 steps. A gzip-validated data archive and rollback image were retained in
ignored deployment records. The agent and restricted bridge containers were
rebuilt with the existing persistent data mount and private configuration.
After startup, health reported `browser_ready` and `operator_stopped`; the API
reported session 0 / 0 steps, the game Remote API was Online, noVNC returned
HTTP 200, and management listeners stayed bound to guest loopback. No inference
request, agent session, or deliberate gameplay action was started during
deployment. A read-only status check later found the prior checkpoint still
describes a six-step failed session; its saved `active` label is historical,
while the authoritative runtime state remains `operator_stopped`.

The first rendered dollar amount after restart was part of the offline-progress
dialog (`$3.515` earned during 9 seconds offline), not a visible HUD balance.
The current balance after that restart was not read, so no balance persistence
claim or income attribution is made from this observation.
