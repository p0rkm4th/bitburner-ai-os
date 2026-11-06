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
| Checkpoint durability and agent lifecycle | Test-game service source `6e8f68a` deployed; 158/158 tests passed | Coverage includes stop, overlap prevention, pause/resume, interruption and terminal-state recovery, atomic checkpoints, stagnation, bounded inference, restricted Remote API actions, guide loading, modal handling, terminal error reporting, stale editor guidance removal, repeat-run protection, constrained in-game `.js` copying, RAM rejection recovery, current API lookup, dialog detection, tutorial controls, verified money progress, malformed baseline rejection, session-number continuity after stop, delayed Terminal observation/duplicate protection, visible-RAM-based execution host selection, stale failed-subobjective invalidation, and semantic deduplication of code variants blocked by the same RAM/host error. The pinned runtime image suite passed before deployment; the updated image was rebuilt on the VM with network disabled. |
| Auto-resume and session continuation | Deployed test-game service preserves operator stop; isolated benchmarks remain bounded | Every isolated trial used `AUTO_RESUME=0` and `MAX_SESSIONS=1`; step and time budgets varied by trial and are recorded in [model-benchmark.md](model-benchmark.md). Each trial was launched explicitly and its disposable containers were removed after a terminal result. The deployed test-game service retains `AUTO_RESUME=1` and `MAX_SESSIONS=0`; its persisted `operator_stopped` state was preserved across the update. |
| Local model gameplay benchmark | Eight isolated Qwen trials demonstrated verified income; extended autonomy and BitNode progression remain unverified | Runs 17, 19, 20, 22, 23, 25, 28, and 34 demonstrated income; Runs 18, 21b, 24, 26, and 27 did not. Run 34 recovered from a visible Netscript runtime error and verified a corrected script's contribution to a $287 post-correction money increase. Run 27 exposed the prior-PID collision fixed in the current candidate. The exact `qwen3.8:27b-q4_K_M` tag is now present in the local model catalog but remains unscored; no gameplay generation has been run with it. See [model-benchmark.md](model-benchmark.md). |
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
request was sent after the owner's local inference rollout began, so inference
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

## Session-number continuity deployment — commit `e3a1a62` (2026-11-06)

The supervisor previously reset the visible session counter to zero on
`/api/start`; after a stop, this could reuse session numbers even though the
checkpoint recorded a later session. The new helper selects the highest number
from current status, saved runtime, and the latest checkpoint; explicit stop
also persists its in-memory number. Two regression tests cover checkpoint and
runtime reconciliation and explicit start; the stop test asserts persistence.
The pinned runtime suite passed 154/154 tests.

Before rollout, the shared test-game service was `operator_stopped`, session 0
/ 0 steps. A gzip-validated persistent-data archive and rollback image were
retained in ignored local deployment records. The source was archived from the
commit, copied to the VM, and the agent image rebuilt there with network access
disabled. Only the agent and restricted bridge containers were recreated with
the same persistent data mount and private configuration. After startup, the
service remained `operator_stopped` at session 0 / 0 steps, `AUTO_RESUME=1`,
the game Remote API was Online, noVNC returned HTTP 200, and management
listeners remained loopback-only. A read-only call to the deployed helper
returned the checkpoint's saved session number, 1. No agent session, inference
request, or game action was started during rollout. The next explicit start was
not invoked, so no new inference session number is claimed.

## Terminal observation reliability deployment — commit `c2379de` (2026-11-06)

The Terminal helper now waits up to 2.5 seconds after Enter for a fresh rendered
command echo or a recognized UI result. On timeout it reports that the command
may have executed and blocks a blind duplicate. Delayed-render and timeout
regression cases passed in the 156/156 pinned runtime suite. Before deployment,
the shared test game was `operator_stopped` at session 2 / 16 steps. A full
persistent-data archive passed gzip validation at
`/opt/bitburner-agent/backups/data-before-c2379de-20261106T082512Z.tar.gz`
(SHA-256 `2661d13b19bc0c5ba08051414392e5115d4886e9e5fea4afa76099d149cd6af3`),
and rollback image `bitburner-agent:rollback-before-c2379de` retained the prior
image (`sha256:2d7fc86d704743850343bf167bd3e62f0e04ed6aba63a092ebbc2306240d362e`).
The source archive was built on the VM with network access disabled; only the
agent and restricted Remote API bridge were recreated, with the same persistent
data mount and private configuration. Post-deploy, health reports
`operator_stopped`, session 2 / 0 steps, and browser ready. The rendered game
still shows Remote API Online; `AUTO_RESUME=1`; noVNC returns HTTP 200; and
dashboard/noVNC listeners remain loopback-only. The deployed image is
`sha256:7c7a9745c4b20d777aa7c59d9f12d897b9d1de105a8defa8eed7e3e888ff9fac`.
No agent session or inference request was started during rollout. Gameplay has
not yet validated this helper change.

## Execution-host and checkpoint recovery deployment — commit `667e4ab` (2026-11-06)

Run 36 revealed that the system prompt incorrectly required every script to
run on `home`, even after a visible RAM rejection. The compact prompt now
chooses a host from visible root/RAM evidence and permits the documented
in-game copy/connect flow. Checkpoint summaries now mark the prior subobjective
as historical after a failed tool result; the running agent also clears that
stale subobjective on continuation. Unit coverage verifies both behaviors.
The full pinned runtime suite passed 157/157 tests.

The shared test game was `operator_stopped` at session 3 / 8 steps before
deployment. A full persistent-data archive passed gzip validation at
`/opt/bitburner-agent/backups/data-before-667e4ab-20261106T084957Z.tar.gz`
(SHA-256 `24586793ee9f314850c967b9063839f5abb42d31179cde364932df2aaae4af42`);
rollback image `bitburner-agent:rollback-before-667e4ab` retained the prior
image (`sha256:7c7a9745c4b20d777aa7c59d9f12d897b9d1de105a8defa8eed7e3e888ff9fac`).
The source archive was built on the VM with networking disabled; only the
agent and restricted bridge containers were recreated with the same
persistent-data mount and private config. Post-deploy, the health API reports
`operator_stopped`, session 3 / 0 steps, and browser ready. The rendered game
shows Remote API Online; `AUTO_RESUME=1`; noVNC returns HTTP 200; and dashboard
and noVNC listeners remain loopback-only. The deployed image is
`sha256:5f287a145974c20c13378ef46eacc151cfd1b8a95743b85d920fb2879d3c4640`.
A read-only check through the deployed container produced the corrected
checkpoint summary from Run 36's actual failed-action checkpoint. No gameplay
or inference was started during rollout; the corrected prompt is awaiting a
bounded gameplay trial.

## RAM-retry stagnation deployment — commit `6e8f68a` (2026-11-06)

The stagnation signature now canonicalizes a repeated deployment rejection by
script filename, execution host, and required RAM. Changing proposed source
cannot reset the repeated-failure budget when the tool returns the same visible
RAM/host rejection. A focused regression test and the full 158/158 runtime
suite passed. An in-container check against two different code variants
confirmed they produce the same failure signature.

Before rollout, the shared test game was `operator_stopped` at session 4 / 6
steps. The persistent data archive
`/opt/bitburner-agent/backups/data-before-6e8f68a-20261106T085936Z.tar.gz`
passed gzip validation (SHA-256
`e5d98aa0a9f3ee6799fb95c0e463026396b4dfd473b4815a6702bf78dcc453d8`). Rollback
image `bitburner-agent:rollback-before-6e8f68a` retained prior image
`sha256:5f287a145974c20c13378ef46eacc151cfd1b8a95743b85d920fb2879d3c4640`.
The source archive was built on the VM with networking disabled; only the agent
and restricted Remote API bridge were recreated, preserving the same data
mount and private configuration. Post-deploy, health reports
`operator_stopped`, session 4 / 0 steps, browser ready, Remote API Online,
`AUTO_RESUME=1`, noVNC HTTP 200, and loopback-only dashboard/noVNC listeners.
The deployed image is
`sha256:adbd1cf008a47ce09334927dab205e0a22392e27b85c8ff364e2c6fc679e3866`.
The new signature has not yet been exercised in a live gameplay session.

## Hidden Terminal and pending-run recovery — commit `d8bb369` (2026-11-06)

Run 38 exposed an ordering defect: `game_run_script(expected_host=...)` and the
pending-deployment check looked for a visible Terminal prompt before invoking
the documented shortcut that opens Terminal. The deployed `hack.js` therefore
could not be run even though the visible UI later showed a home prompt. The
local fix opens Terminal through the normal UI before host validation, clears
visible blocking dialogs first, and preserves the pending-run instruction when
continuing from a failed checkpoint. No hidden game state is used.

The focused regression tests and full pinned runtime suite passed (160 tests).
Before rollout the game was terminally failed after Run 38, so no active agent
session was interrupted. A full persistent-data archive passed gzip validation
at `/opt/bitburner-agent/backups/data-before-d8bb369-20261106T091554Z.tar.gz`
(SHA-256 `3448a27e568a8d850759e9da3a3635f59ec896b8dc2a38ca81879e0bacf5bfd8`),
and the prior image was tagged for rollback. The image was built with network
access disabled; only the agent and restricted Remote API bridge were
recreated, preserving the same persistent data mount and private config.
Post-deploy checks report the preserved terminal `failed` state at session 6,
browser ready, `AUTO_RESUME=1`, Remote API Online, noVNC HTTP 200, and
loopback-only management listeners. A read-only visible observation shows an
offline-progress dialog, so it does not establish a current balance or income
attributable to this change. No gameplay session or inference request was
started. Every Bitburner profile referenced by this project is a test game;
there is no separate production game. Live gameplay validation of the ordering
fix remains pending.

### Visible Terminal host parsing follow-up — pending deployment

Run 39 tested `d8bb369` and confirmed the Terminal opens after the offline
progress dialog is dismissed, but the live accessibility snapshot presents the
prompt host as separate rendered text (`home` followed by `]>`). The guard's
prompt parser still required the normal bracketed host/path representation and
rejected two consecutive attempts to run the pending deployment. The operator
stopped the trial after three steps; no script ran. A read-only post-dismissal
HUD observation captured $71.789k and hacking 155 as the baseline. The parser
now recognizes both prompt renderings, with focused coverage and 162 pinned
runtime tests passing. This parser update is not yet deployed; another live
trial is required to validate execution.

### Cross-file RAM diagnosis gate — pending deployment

The continued Run 39 trial validated the split-line prompt parser and reached
Bitburner's actual execution error. The visible Terminal reported that
`hack.js` required 1.70 GB and `simple_hack.js` required 1.85 GB on `home`; no
script ran. The model then authored/deployed `tiny_hack.js` without first
checking the visible process list or Active Scripts. The run was stopped after
nine agent steps to avoid repeating the RAM-blocked cycle. A post-dialog
baseline was $71.796k / hacking 155; no income or progression is attributed.

The deployment tool now blocks *any* new filename after an unresolved visible
RAM rejection until the model checks `ps` or opens Active Scripts. The gate
clears after diagnosis and a subsequent verified new deployment. The focused
regression tests and all 164 pinned runtime tests pass. This correction awaits
deployment and a bounded gameplay recheck.

### Pending-run continuation priority — pending deployment

After the cross-file RAM guard deployed, the next session still chose Terminal
`ls` twice because the generic benchmark objective requested a listing while a
checkpoint required running `tiny_hack.js` first. Both calls were blocked by
the pending-run guard; the agent was stopped after three steps. No script ran.
The session task builder now adds a state-specific priority instruction when a
verified deployment is pending, explicitly making that required run the first
action and overriding generic file-listing guidance. When no deployment is
pending but a RAM rejection remains unresolved, it prioritizes visible process
inspection before any new script authoring. Two focused prompt-priority tests
and the full 166-test suite pass. Deployment and live validation remain pending.

### Pending-run priority recovery deployment — commit `5552257` (2026-11-06)

A generic file-listing request repeatedly overrode the pending deployment
checkpoint in Qwen's action selection. The task builder now injects a compact,
state-specific first-action instruction when a verified deployment is pending,
and tells the model to inspect visible processes before new authoring after an
unresolved RAM rejection. The 166-test pinned suite passed. Before deployment,
the shared test game was `operator_stopped` at session 9; a full persistent
data archive passed gzip validation at
`/opt/bitburner-agent/backups/data-before-5552257-20261106T094141Z.tar.gz`
(SHA-256 `c12eae5f07c65ffbde2bf91a20ce72d9d5747bc66414793c57f22b4b657b14f6`),
and the previous image was tagged for rollback. The image build used no network
access; only the agent and restricted Remote API bridge were recreated,
preserving the shared test profile. Postflight: `operator_stopped`, session 9,
browser ready, `AUTO_RESUME=1`, Remote API Online, noVNC HTTP 200, and
loopback-only management listeners. A read-only in-container check confirmed
the pending-script instruction is loaded. Live gameplay validation remains
pending.

### Pre-run money baseline and fresh PID confirmation — pending deployment

Run 39's session 10 reached a successful visible `run tiny_hack.js` on rooted
`n00dles` (PID 5), after `home` rejected it for insufficient free RAM. The
script was model-authored as a one-shot `ns.hack` call. It did not visibly
produce an attributable balance increase. Active Scripts showed an aggregate
$0.471/s rate on `home`; the model incorrectly attributed it to `tiny_hack.js`,
and the completion guard rejected that claim. The final visible HUD was
$71.821k / hacking 156; the run did not preserve its immediate pre-run HUD
baseline, so no money delta is recorded.

The run helper now samples visible money immediately before sending a script
command, only counts a PID confirmation found after the fresh command echo,
and passes that pre-run balance to `game_progress` and the completion gate.
The tool guide warns against attributing aggregate Active Scripts production
to a particular file without its row or output. All 170 pinned tests pass.
Commit `d3c3691` was deployed and exercised in Run 39 session 11 below.

### Run 39 session 11 — model-authored Netscript cycle

The deployed model independently read `simple_hack.js`, wrote
`hack_n00dles.js`, deployed it through the restricted Remote API, recovered
from a visible 2.05 GB `home` RAM rejection by copying the file to rooted
`n00dles`, and started it visibly (PID 5). The script log showed weaken/grow
operations and successful hacks for `$0.005` and `$0.010`, each with 3.300
hacking experience. Later read-only observations showed further successful
`$0.014` and `$0.019` hacks. The HUD was `$71.840k` when the agent stopped and
later showed `$71.842k` while the model-authored script remained active. This
is a displayed `$2` increase after the trial began, but the entire HUD delta
cannot be attributed to the script: its individually observed successful
transactions total cents, and Active Scripts' `$0.467/s` figure was aggregate.
Hacking remained level 156.

The bounded agent session was stopped after 14 tool calls when it repeated
`tail hack_n00dles.js` after the tool returned `NO_PROGRESS`. It had zero
framework failures and seven game/tool errors. The agent is explicitly
`operator_stopped`; the authored Netscript remains active in the shared test
game, whose profile was preserved. This verifies independent authorship,
deployment, visible execution, RAM recovery, and positive hack results. The
visible balance changed after the trial, but its full delta is not attributable
to this script. Per-request
token and latency metrics were not persisted. The script remains active in the
test game; next validation should observe the existing game state without
starting another model request.

The run exposed a repetition-detection gap: identical rejected `NO_PROGRESS`
actions were assigned new failure signatures whenever background game output
changed the DOM. The harness now ignores that DOM churn for explicit
`NO_PROGRESS` failures while still keying on the action and rejection. A
focused regression test was added; all 171 tests pass in a no-network
container.

### Repeat-guard deployment — commit `6018a62`

The tested `NO_PROGRESS` signature fix was deployed to the existing test-game
VM. A complete persistent-data archive and rollback image were retained; only
the agent and restricted Remote API bridge containers were recreated.
Postflight confirmed the source matched the release, `operator_stopped`
persisted, the browser was ready, Remote API was Online, and noVNC returned
HTTP 200. The reopened browser showed the saved script-log UI and an
offline-progress modal. Its generated-since-offline amount is not treated as
current balance or as earnings from the model-authored script. Management
listeners remain loopback-bound. A short visible verification continuation is
pending coordination for the shared inference slot.

A read-only call to the documented Remote API `getFile` method after restart
confirmed that `hack_n00dles.js` remains on `home`. The authored script formats
its custom dollar output with `toFixed(0)`, which rounds sub-dollar hacks to
`$0`; Bitburner's visible operation log separately showed the fractional
successful hacks. No script write, gameplay action, or save access occurred.

A regression test now confirms that an offline-progress modal's aggregate
`Your scripts generated` amount is not parsed as the player's current balance.
The no-network suite passes 172/172 tests. This is test-only; deployed runtime
behavior did not change.

## Modal-transition diagnosis follow-up (2026-11-06)

A bounded Qwen3.6:35b check made three visible dialog-dismissal attempts. The
offline-progress modal transitioned to a Netscript runtime-error dialog, but
the helper reported only that a presentation dialog remained. A fresh rendered
observation showed `hack_n00dles.js@home (PID -4)` failed at `weaken` with
dynamic RAM 1.80 GB / allocation 1.70 GB. This is the visible error from a
home-server attempt; the HUD was covered, so no current balance or income was
verified. The agent wrote, deployed, or launched no script. It was stopped and
the persisted runtime state is `operator_stopped`.

Ollama logged four responses across three tool calls: 20,430 prompt tokens,
1,324 completion tokens, 86.829 seconds summed request time (21.707 seconds
mean), and 15.851 seconds summed model-load time. Post-run `/api/ps` reported
23.05 GB VRAM allocated at 16K context; this was not a peak sample. Per-GPU
utilization during the run was not recorded.

The source helper now fingerprints the visible dialog before and after one
close attempt. If the original dialog is replaced by a different visible
dialog, it reports the transition and returns the new dialog text for
diagnosis, instead of saying the original dialog remains. A focused regression
and the full network-disabled suite pass (176/176). This source change is not
deployed yet; the existing test-game browser/profile remains intact. Deployment
and live validation are deferred to a safe boundary before the next gameplay
session.

## Modal-transition fix deployment — commit `8f996db` (2026-11-06)

The modal-transition helper and regression test were deployed while the agent
was `operator_stopped`. Before container recreation, the persistent data was
archived and gzip-validated; the prior agent image was tagged for rollback.
The updated runtime source hash matches the archived release. Only the agent
and restricted Remote API bridge containers were recreated.

Postflight: agent health is good, browser is ready, the state remains
`operator_stopped` at session 12 / 0 steps, Remote API is Online, and noVNC
returns HTTP 200. The browser reopened the same persistent game profile and
shows the offline-progress dialog; its displayed aggregate remains excluded
from balance/income claims. This deploy did not make a gameplay or inference
request. The modal-transition behavior is covered by a mocked regression test
in the 176/176 network-disabled suite; live verification still needs a bounded
model session to close the offline dialog and inspect any newly revealed game
error.

The task-specific system prompt and compact game guide explicitly explain
that dismissing one dialog can reveal another. They direct the agent to inspect
the new visible text before choosing an action. The 177/177 source suite passes;
this prompt/documentation update is deployed in commit `26151ba` below.

## Dialog-recovery prompt deployment — commit `26151ba` (2026-11-06)

The compact game guide, troubleshooting notes, and gameplay instructions now
tell the agent to inspect a newly revealed dialog instead of repeating the
previous dismissal. The full 177-test suite passed with networking disabled.
Before deployment, the persistent test-game data was archived and the previous
image retained for rollback. The runtime source hashes match the release; only
the agent and restricted Remote API bridge containers were recreated.

Postflight: health is good, browser ready, `operator_stopped` at session 12 / 0
steps, `AUTO_RESUME=1`, 16-step session bound, unlimited configured session
count, 16,384 context, Remote API Online, and noVNC HTTP 200. The same game
profile reopened behind its offline-progress modal; the modal total is not
counted as balance or income. No inference or gameplay action ran during this
deployment. Live modal-transition behavior and independent script repair remain
unverified until the next bounded local-model trial.

## Dynamic-RAM recovery guidance deployment — commit `21b9749` (2026-11-06)

The on-demand troubleshooting lookup now routes dynamic/runtime RAM errors to
the focused RAM recovery notes. They direct the agent to compare visible RAM
allocation and usage, inspect the named API functions, consult the live API
documentation, and verify a later run. A regression test checks this route.
The network-disabled full suite passes 177/177.

The release was deployed while the test agent was `operator_stopped`. Before
recreating the agent and restricted Remote API bridge, the persistent data
directory was archived and gzip-validated, and the previous image was tagged
for rollback. Postflight verified the deployed source hashes, `AUTO_RESUME=1`,
16 steps per session, unlimited configured session count, 16,384 context,
browser readiness, Remote API health, and noVNC HTTP 200. Runtime remains
`operator_stopped` at session 12 / 0 steps. The browser restored its existing
profile. Its current offline-progress modal shows `$8.910` aggregate offline
generation; this is not treated as the current balance or attributable income.
No inference or gameplay action ran during deployment. A coordinated bounded
recovery trial is still required to verify that the model can diagnose the
runtime RAM failure and achieve attributable income.

## Run 41 and Terminal recovery fix (2026-11-06)

The bounded local Qwen recovery run ended `failed` at 11:52:27 UTC after two
consecutive failed sessions. The visible page showed the existing
`hack_n00dles.js` and repeated `$0` output; the model did not edit or deploy a
script, and no attributable income was verified. It reported `$71.893k` and
hacking level 157, but no fresh baseline comparison was captured. The model's
visible `scan-analyze 2` result showed `n00dles` root access and required
hacking level 1; it nevertheless did not reach a script repair.

Thirteen local model responses processed 84,230 prompt and 3,872 completion
tokens in 309.661 seconds total (23.820 seconds mean), plus 15.905 seconds
model-load time. At 16,384 context, Ollama reported about 23.05 GB VRAM
allocated; this was not a peak sample. No generation-time GPU peak was
recorded.

The rendered Terminal eventually showed commands that its helper had reported
unconfirmed after 2.5 seconds. The helper now polls up to 6 seconds and, on
timeout, returns `UNCONFIRMED` with the latest visible UI and an explicit
no-repeat instruction. The duplicate-command guard remains active. The system
prompt and tool guide direct the model to inspect with `game_observe` or read a
listed script with `game_read_script`. Delayed-output and duplicate-prevention
tests pass; the network-disabled suite passes 180/180. This runtime fix has not
yet been validated in a live agent session. It was deployed as `f02ded9`; the
deployment postflight then exposed that a terminal failure record omitted its
session counter. `738d751` now persists that counter and restores the highest
recorded session from the durable checkpoint without reviving a failed agent.

The `738d751` release was built and deployed while the test agent remained
terminal `failed`. Before recreating the agent and restricted Remote API
bridge, the persistent data directory was archived and gzip-validated, and the
previous image was tagged for rollback. Postflight verified marker `738d751`,
agent health and browser readiness, terminal `failed` at session 14 / 0 steps,
`AUTO_RESUME=1`, 16 steps per session, 16,384 context, Remote API Online, and
noVNC HTTP 200. The existing profile was restored behind an offline-progress
modal displaying `$11.835` aggregate offline generation; that amount is not
current balance or attributable income. No inference or gameplay action ran
during deployment. The network-disabled suite passes 180/180. A further
bounded local-model session is needed to validate Terminal recovery and
autonomous Netscript repair; no income has been verified.

## Run 42 — test-game script attempt and visible error recovery (2026-11-06)

The test VM passed a fresh inference-capacity preflight. Local `qwen3.6:35b`
ran from 12:25:31 to 12:30:14 UTC with 16,384 context and an eight-action cap. It
independently inspected memory, stopped the prior script, authored and
deployed `hack_n00dles_fast.js`, and attempted visible Terminal execution. The
browser displayed a Bitburner `REFERENCE ERROR` (`ReferenceError: ns is not
defined`, line 16). The run tool returned `UNCONFIRMED` after its six-second
confirmation window; a later read-only rendered observation confirmed the
error modal. The model repeated dialog dismissal twice because the helper did
not recognize that heading. The session was explicitly emergency-stopped at
eight actions, and runtime state is `operator_stopped` at session 15. No
current money balance or hacking-level change was visible; no income or
successful debugging is claimed. The existing test profile and script state
were preserved.

Eight local model responses processed 72,435 prompt tokens and 2,066
completion tokens in 238.785 seconds summed Ollama request duration (29.854
seconds mean response time). Mean model-load duration was 1.987 seconds. A
post-run sample showed 0% GPU utilization with 7.329/5.059/6.201/5.207 GiB
allocated across four GPUs; it is not a peak inference measurement.

The harness now recognizes the visible `REFERENCE ERROR` form and can close
it using a fresh, unique visible Close control. Focused regression tests pass;
the full network-disabled suite passes 181/181. Remote API was Online in the
last rendered observation; noVNC remained available. The agent was explicitly
stopped, and `AUTO_RESUME=1` does not revive this operator-stopped state.

Commit `9b8d82d` was then deployed while the agent was stopped. Persistent test
data was archived and validated; the previous image was retained for rollback.
Postflight source hashes match the release, both containers are healthy, the
browser is ready, Remote API is Online, and noVNC returns HTTP 200. Runtime
remains `operator_stopped` at session 15 despite `AUTO_RESUME=1`; the existing
browser profile reopened behind an offline-progress modal. Its aggregate
amount is not current balance or attributable income. Management and viewer
ports remain bound to localhost. No inference or gameplay action ran during
deployment.

## Run 43 — live ReferenceError recovery (2026-11-06)

After deployment, the isolated test game was resumed with local
`qwen3.6:35b` at 16,384 context. The new dialog detector worked against the
actual rendered `REFERENCE ERROR`: the agent dismissed it, read its own
model-authored script, diagnosed that code outside `main(ns)` caused
`ns is not defined`, authored and deployed a revision, and launched it. The
revised script then produced a visible `TYPE ERROR` because `spawn` rejected
an array-valued script argument at line 20. The agent had identified the
second error in its checkpoint, but the run was emergency-stopped before it
could correct it. The requested eight-action cap was exceeded by one action
while the stop raced the next tool response; runtime state is
`operator_stopped` at session 16 / 9 steps.

The UI showed positive Terminal PIDs for two run attempts. Final read-only
observation showed the visible HUD at `$71.947k`, hacking level 157, Remote API
Online, and no modal; no comparable before balance was captured. This run
therefore verifies model-authored deployment and visible start, plus recovery
from the first runtime error, but not successful autonomous debugging or
attributable income. Ten Ollama responses processed 76,863 prompt and 2,212
completion tokens in 218.516 seconds summed request duration (21.857 seconds
mean). The model was resident; preflight sampled 0% GPU utilization and
7.329/5.059/6.201/5.207 GiB allocated across four GPUs. No generation-time
peak or CPU offload measurement was collected. The exclusive inference slot
was released with no queued or in-flight requests.

A read-only visible observation at 12:55:31 UTC showed `$71.949k`, up from
`$71.947k` at 12:48:50. The Terminal contained `$0`/`$1` lines from
`hack_n00dles.js` and positive PIDs for the new script, but several scripts
may be involved and the new script's second runtime error was not verified as
resolved. The displayed $2 increase is recorded as un-attributed and is not
claimed as the new script's income.

## Run 44 — Netscript concurrency error (2026-11-06)

Qwen3.6:35b continued the preserved test game from 13:05:08 to 13:08:53 UTC
at 16,384 context. It read the current script, attempted an equivalent
deployment that the no-op guard rejected, reran the script, dismissed the
visible `TYPE ERROR`, authored and deployed a changed script, and launched it.
The final read-only observation showed a Bitburner `CONCURRENCY ERROR`:
`weaken` was called without awaiting its asynchronous result. The agent did
not verify income and was explicitly stopped at eight actions. Runtime remains
`operator_stopped` at session 17. No balance was visible behind the error
dialog, so no gameplay progress or income is claimed.

Eight local-model responses processed 55,710 prompt and 2,988 completion
tokens in 190.024 seconds summed request time (23.759 seconds mean). The model
was resident; preflight sampled 0% GPU utilization and 7.329/5.059/6.201/5.207
GiB allocated across the inference GPUs. No generation peak or CPU offload
measurement was collected. The exclusive inference slot was released with no
active or queued request.

## Run 45 — concurrency error dialog recognition (2026-11-06)

The test-game agent resumed at 13:30:16 UTC with Qwen3.6:35b at 16,384
context. It reread its script several times and repeated dialog dismissal after
the tools reported no visible dialog. The final read-only UI observation still
showed the `CONCURRENCY ERROR` modal and its visible Close button. This exposed
that the deployed dialog detector recognized ReferenceError but not the
concurrency-error heading. The agent did not use troubleshooting or live API
lookup, change the script, or verify income. It was explicitly stopped after
seven actions when the no-progress pattern repeated; a tool action raced the
stop. Runtime is `operator_stopped` at session 18.

Eight local-model responses processed 45,749 prompt and 2,163 completion
tokens in 149.110 seconds summed request time (18.644 seconds mean). Qwen was
resident; preflight showed 0% GPU utilization and 7.329/5.059/6.201/5.207 GiB
allocated across four GPUs. No generation peak or CPU offload measurement was
collected. The concurrent-error modal detector fix has a focused test passing
locally. No income or gameplay progress is claimed.

### Detector deployment postflight

Commit `677b5ea` (including the `3ad84ba` modal fix and the earlier
`cdc0061` guidance changes) was deployed to the isolated test VM after creating
and validating a persistent-data archive and tagging the prior image for rollback.
Only the agent and restricted Remote API bridge containers were recreated.
Runtime hashes matched for the game tools, docs retriever, prompt, and bundled
troubleshooting guide. The agent remained explicitly `operator_stopped` at
session 18; the persistent browser profile and checkpoint were retained.
Health reported the browser
ready, the VNC page returned HTTP 200, and the rendered Bitburner UI still
showed Remote API Online. Runtime configuration remained `AUTO_RESUME=1`,
`MAX_STEPS=16`, `MAX_SESSIONS=0`, and `OLLAMA_NUM_CTX=16384`. This validates
deployment and preservation only; gameplay recovery and income remain
unverified.

## Run 46 — concurrency recovery, deployment, and unverified income (2026-11-06)

The isolated agent resumed at 13:45:24 UTC with Qwen3.6:35b at 16,384 context.
The deployed dialog detector closed the visible concurrency error. Qwen read
its script, attempted an equivalent write that the no-op guard rejected, ran
the old revision and observed the error again, then authored and deployed a
changed version with `await` on `hack`, `grow`, and `weaken`. The visible
Terminal confirmed it launched as PID 4. The agent recorded a $71,979 baseline
and hacking level 157; its subsequent progress check showed no output from the
new script. The rendered UI later showed about $71.983k and hacking 157, plus
`$2`/`$0` messages labeled `hack_n00dles.js`. Because those messages identify a
separate script and the balance is rounded, the change cannot be attributed to
the model-authored `hack_n00dles_fast.js`. No verified income or level
progression is claimed.

The run ended at 13:50:55 UTC after 12 actions and 12 tool calls (2 failed, 2
game errors). After the progress check, Qwen twice sent a malformed
`game_open_tab` argument; the no-progress guard stopped the loop and the
operator stop persisted `operator_stopped` at session 19. Thirteen Ollama
responses processed 103,939 prompt and 3,418 completion tokens in 316.947
seconds summed request time (24.381 seconds mean). Wall-clock duration was
331 seconds. Preflight showed zero GPU utilization and the model already
resident at 16K; no generation-time peak or CPU offload sample was collected.
The post-run Herd queue is empty. The persistent game remains open and
in-game scripts may continue after the agent stops.

### Follow-up: constrain malformed navigation targets

Run 46 exposed two identical malformed `game_open_tab` arguments after a
progress check. The local tool now declares its `tab` argument as a finite
enum of visible navigation labels and returns the exact valid values when
called incorrectly. The Browser Use registry schema was inspected to verify
that it publishes the enum, and the full suite passes 184/184 in the project
container. Before deployment, the current test profile was archived and the
previous image tagged for rollback. Commit `e9b9f11` was then deployed and the
agent/bridge containers recreated at the stopped boundary. Runtime hashes
match for the updated game tools and tool guide. Postflight reports
`operator_stopped` at session 19, browser ready, Remote API Online, and VNC
HTTP 200; `AUTO_RESUME=1`, `MAX_STEPS=16`, `MAX_SESSIONS=0`, and 16K context
remain configured. The restored game showed an offline-progress dialog
reporting `$20.398` generated by scripts during about one minute offline. This
confirms the profile and script progress survived recreation, but the dialog
does not attribute earnings to `hack_n00dles_fast.js`.

## Run 47 — script process exited before output (2026-11-06)

After the `e9b9f11` deployment and restored profile, Qwen3.6:35b resumed at
14:10 UTC with 16K context. It dismissed the offline-progress dialog, used
Terminal to inspect the existing file and list home, then visibly launched
`hack_n00dles_fast.js` as PID 3. The next `tail` showed: no matching script
with the requested filename and empty args was running on home. Qwen repeated
the same tail command; the guard rejected the repeat. The run was explicitly
stopped at session 20 after 7 action steps / 7 tool calls, with 2 game errors
and no infrastructure-call failures. The persisted state is
`operator_stopped`; the supervisor was prevented from continuing into another
session.

Eight Ollama responses processed 75,112 prompt and 1,352 completion tokens in
188.024 seconds summed request time (23.503 seconds mean). A later visible HUD
showed $72.012k and hacking 157, but no fresh starting balance was recorded.
Visible `$0`/`$3` output belonged to `hack_n00dles.js`. No attributable income,
hacking progression, or working autonomous script from this run is claimed.
The new tab enum was deployed, but this trial did not call `game_open_tab`.

### Post-Run 47 terminal-recovery deployment

The `game_terminal` result now preserves the exact “no script named … is
running” game text and adds a bounded next step: inspect Active Scripts/`ps` or
read the listed source, without repeating `tail`. `game_troubleshoot` maps this
error to active-process guidance. The focused regression tests and full
185-test suite passed in the project container. Commit `82c83e4` was deployed
after a validated profile archive and rollback image tag. Runtime hashes match
for the tool implementation, docs retriever, and bundled guides. Postflight
retained `operator_stopped` at session 20, browser ready, Remote API Online,
VNC HTTP 200, AUTO_RESUME=1, MAX_STEPS=16, MAX_SESSIONS=0, and 16K context.
The restored page showed an offline-progress dialog reporting `$6.428` from
scripts during 19 seconds offline. Profile persistence is confirmed; that
aggregate amount is not attributed to the model-authored file.
