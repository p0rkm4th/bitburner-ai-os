# Local model gameplay benchmark

## Scope and controls

All inference used existing local Ollama servers. The x1 laptop hosted only the
isolated browser and agent containers; no model was loaded there. Every game
is a test game. The retained shared browser profile is persistent test state;
benchmark trials did not modify that profile, save, or model settings. Each
run got a new copy of the same disposable Bitburner profile with the Remote API
visibly Online. No trial shared game progress with another trial.

The scored runs used the same objective, browser and restricted Remote API
tools, 16,384-token context, temperature 0.2, seed 7, one session, and the same
retry, history, and inactivity limits. Step and session ceilings varied by
trial and are recorded below; Run 23 used 16 steps and 20 minutes. The game
objective supplied no code, target, or Netscript correction.
The model had to observe the game, consult documentation when needed, write
its own code, deploy it through the allowlisted API, run it through the visible
terminal, debug errors, and verify a money change. Runs ended sooner when the
existing stagnation/failure limit fired. Trials ran sequentially.

Private per-call Ollama metadata and sampled hardware records are retained in
ignored local files. Public results below summarize those records without
including prompts, model responses, saves, credentials, node names, or network
addresses. The benchmark logs token counts and elapsed response time, not
reasoning tokens. “Session time” is from objective start to supervisor exit;
“inference time” sums Ollama response wall times.

## Candidates and availability

| Role | Exact Ollama tag | Weights | Capabilities and license | Placement and availability |
|---|---|---|---|---|
| Baseline | `qwen3.6:35b` | 35.5B, Q4_K_M; 23.3 GB model, 23.3 GB reported GPU allocation | Vision and tool support; Apache-2.0 | Deep inference pool; installed and benchmarked |
| Primary challenger | `qwen3.8:27b-q4_K_M` | 27B Q4_K_M; 16.5 GiB catalog size | Vision and tool support; Apache-2.0 | Read-only local model catalog check on 2026-11-06 found the exact tag available and unloaded. Not scored; no generation or gameplay trial has been performed. |
| Coding challenger | `devstral-small-2:24b-instruct-2512-q4_K_M` | 24B, Q4_K_M; 15.2 GB model, 18.2 GB reported GPU allocation | Vision and tool support; Apache-2.0 | Deep inference pool; installed and benchmarked |
| VRAM-sized candidate | `gemma4:12b` | 11.9B, Q4_K_M; 8.7 GB model, 8.7 GB reported GPU allocation | Vision and tool support; Apache-2.0 | Compact inference pool; installed and benchmarked |

Catalog tags and requirements were checked before pulling Devstral. Its exact
tag requires Ollama 0.13.3 or later; the serving endpoint was 0.31.1 during
that benchmark. The official Ollama catalog lists Qwen3.8's 27B model. A
read-only local catalog check on 2026-11-06 confirms the quantized
`qwen3.8:27b-q4_K_M` tag is present and unloaded. No generation or gameplay
trial has been performed, so compatibility with this agent harness and
gameplay quality remain unverified.
All three tested models reported the entire
weight allocation in GPU memory via `/api/ps`; no weight CPU offload was
reported. GPU sampling observed four 8 GiB cards for the deep pool and two
8 GiB cards for the compact pool. The per-GPU sampler did not return data in
Gemma trial 3; its Ollama allocation was still reported as fully GPU resident.

Sources: [Qwen3.6 model card](https://huggingface.co/Qwen/Qwen3.6-35B-A3B),
[Qwen3.8 Ollama tags](https://ollama.com/library/qwen3.8/tags),
[Qwen3.8 model card](https://huggingface.co/Qwen/Qwen3.8-27B),
[Devstral Small 2 exact Ollama tag](https://ollama.com/library/devstral-small-2%3A24b-instruct-2512-q4_K_M),
[Devstral Small 2 model card](https://huggingface.co/mistralai/Devstral-Small-2-24B-Instruct-2512),
[Gemma 4 Ollama tags](https://ollama.com/library/gemma4/tags), and
[Gemma 4 12B model card](https://huggingface.co/google/gemma-4-12B-it).
Each model card specifies Apache-2.0.

## Unguided baseline results

**No candidate completed a verified money-making gameplay cycle.** Across the
nine scored trials, no script both executed successfully and produced
measurable income. Initial and final visible balance was approximately $1.262k
and hacking remained level 1 in every run. Therefore time to first successful
script and useful gameplay was not reached for any model; the average and
median are not available. Money earned and hacking progression were both zero.

| Model | Trials | Session time (mean / median) | Ollama calls; prompt / output tokens | Response latency (mean / median) | Success |
|---|---:|---:|---:|---:|---:|
| `qwen3.6:35b` | 3 | 14m 42s / 13m 15s | 48; 528,301 / 13,068 | 50.7s / 49.9s | 0/3 |
| `devstral-small-2:24b-instruct-2512-q4_K_M` | 3 | 20m 12s / 17m 11s | 63; 536,407 / 11,754 | 54.2s / 48.1s | 0/3 |
| `gemma4:12b` | 3 | 10m 58s / 10m 53s | 18; 43,792 / 1,688 | 99.2s / 119.5s | 0/3 |

“Success” requires visible confirmation that the model-authored script ran and
increased money. The mean/median time to success for each row is **not
reached**. Output counts include successful responses; timed-out calls have no
token count. Mean generation speed from Ollama's evaluation duration was
approximately 34.5 tokens/s for Qwen3.6, 8.2 for Devstral Small 2, and 10.1
for Gemma 4. Loading overhead was small relative to response time: summed over
three trials, 18.6s, 25.4s, and 9.2s respectively.

The harness records issued action bundles and retains tool responses in its
private conversation snapshots, but it does not normalize every tool response
into an independently countable event. The error categories and recovery
outcomes below are based on those snapshots and terminal checkpoints; exact
per-tool invalid-call counts are unavailable and are not estimated.

### Individual trials

| Model / trial | Session, steps, calls | Actions and observed result |
|---|---|---|
| Qwen3.6 / 1 | 13m 15s, 13 steps, 14 calls | Authored and ran `grow_home.js`. First run failed on an undefined server money value; its next attempt hit the removed `nFormat` API. It recognized both errors but did not correct the script before repetitive actions triggered the stagnation limit. Balance and hacking level did not change. |
| Qwen3.6 / 2 | 20m 52s, 24 steps, 24 calls | Read official API definitions and authored `hack.js`/`earn.js`. The first target was `home` (game rejected hacking it); later deployments hit RAM calculation errors and scripts without a usable `main`. It attempted several corrections but never verified income. |
| Qwen3.6 / 3 | 9m 59s, 10 steps, 10 calls | Authored `makemoney.js`, targeted `home`, and tried invalid path-style filenames. It recognized the simple-filename error but did not produce a working run. |
| Devstral / 1 | 17m 11s, 24 steps, 24 calls | Repeated stale element-index clicks while seeking the editor; no Netscript was authored or run. |
| Devstral / 2 | 26m 24s, 24 steps, 26 calls | Authored and deployed `money_maker.js`, but its first target lacked root access. The visible runtime-error modal blocked the terminal; repeated attempts did not recover. No verified income. |
| Devstral / 3 | 17m 00s, 13 steps, 13 calls | Tried terminal/editor-based authoring and several tool paths. Two calls timed out at 120s. It did not verify a successful script or income. |
| Gemma 4 / 1 | 10m 53s, 5 steps, 5 calls | Four 120s Ollama read timeouts; one response made an invalid dropdown selection. No Netscript authored. |
| Gemma 4 / 2 | 11m 12s, 5 steps, 7 calls | Two 120s read timeouts and repeated invalid/empty action responses. It only established initial visible money and hacking level. |
| Gemma 4 / 3 | 10m 48s, 5 steps, 6 calls | Three 120s Ollama read timeouts, with empty actions after them. No Netscript authored. |

### Hardware and inference observations

The baseline used about 23.3 GB of GPU memory across four GPUs and generated
about 34 tokens/s. Devstral used about 18.2 GB across four GPUs and generated
about 8 tokens/s. Gemma used about 8.7 GB across two GPUs and generated about
10 tokens/s; response calls were frequently near or above the 120s HTTP timeout.
Observed GPU utilization varied widely from moment to moment, including 100%
samples; individual snapshots are not a sustained utilization measure. Ollama
reported the full model weight size in VRAM, with no CPU weight offload. The
agent/browser containers were limited to 2 CPUs and 3 GiB RAM, with the bridge
limited to 0.5 CPU and 384 MiB RAM.

## Recommendation

Keep `qwen3.6:35b` as the deployed test-game service's configured model for now.
It was the most reliable of these tested candidates at generating tool actions and Netscript attempts, read
official definitions in one run, and was the fastest tested model. It still
failed the gameplay goal in all three trials, so this benchmark does **not**
validate autonomous gameplay. Devstral's code focus did not offset its lower
throughput and inability to recover from a blocked dialog. Gemma 4 should not
be selected for this harness given repeated long timeouts and zero script
authoring.

Do not switch the deployed test-game service to a challenger based on these
runs. At the time of this initial benchmark, Qwen3.8 could not be pulled because
the serving Ollama version was too old. The exact quantized tag is now present
in the local catalog, but compatibility with this agent harness and gameplay
quality have not yet been measured. Revisit model selection through a controlled
isolated comparison. No deployed test-game model setting was changed.

## Guided trial after documentation and harness changes

The unguided results above remain the baseline. Two isolated Qwen3.6 trials were
then run with the compact guide, allowlisted on-demand help, bounded visible
tools, and a fresh copy of the same starting profile. Two earlier trial starts
stopped before inference because the guide path in the flat container layout
was wrong and Browser Use requires `max_history_items` greater than 5; both
setup defects were corrected and are not counted as gameplay trials.

| Trial | Session result | Visible progress | Authoring/execution | Inference metrics |
|---|---|---|---|---|
| Guided Qwen3.6 / 1 | 9 steps; 12m 50s total; ended exhausted | $1.262k → $1.262k; hacking 1 → 1; $0 verified income | No script authored, deployed, or run. It called `scan`, twice used invalid `scan-analyze` syntax, requested `brutessh` through the Netscript reference tool, then emitted two empty actions after 120s Ollama read timeouts. | 8 requests: 6 responses, 2 timeouts; 48,674 prompt tokens and 1,004 output tokens in successful responses; 591s summed request wall time. Ollama `/api/ps` reported the Qwen weights fully in VRAM (23.3 GB; 16,384 context). Per-GPU sampling returned no data in this trial. |
| Guided Qwen3.6 / 2 | 4 steps; 2m 29s agent session; ended exhausted | $1.262k → $1.262k; hacking 1 → 1; $0 verified income | No script authored, deployed, or run. It called `game_dismiss_dialog` twice while the offline summary remained visible, then returned one malformed structured response and ended with `success: false`. | 4 responses; 16,591 prompt tokens, 642 output tokens, 146.5s summed response wall time. Ollama `/api/ps` reported 23.3 GB fully in VRAM at 16,384 context. Per-GPU sampling again returned no data. |

The first run showed repeated invalid Terminal syntax and that command errors
were not included in checkpoints. The second showed that the modal can be an
`aria-modal` presentation wrapper containing only an unlabeled close button;
the helper treated it as absent, so the model repeated dismissal. The core guide
and error accounting have been updated, and the helper now clicks a unique
visible button only when it is inside an active modal. Tests cover the wrapper
and button cases. These trials do not yet establish that the documentation
improves gameplay performance; neither produced Netscript.

Three more guided Qwen3.6 sessions were recorded after those initial runs. They
also used the isolated starting profile and did not change production.

| Trial | Session outcome | Observable result |
|---|---|---|
| Guided Qwen3.6 / 3 | Exhausted after 9 steps; 8 inference requests, including 2 timeouts | No income or hacking increase. It attempted a money script but used `home` as a hack target and invalid path-style filenames. |
| Guided Qwen3.6 / 4 | Exhausted after 4 steps; 4 inference responses | No script or progress. It repeated dialog-dismissal actions; the helper's modal interpretation was corrected afterward. |
| Guided Qwen3.6 / 5 | Operator-stopped after 7 steps; 7 inference requests | Stopped during an unproductive session; no verified script or progress. |
| Guided Qwen3.6 / 6 | Exhausted after 8 steps; 8 requests, including 1 timeout | No verified script or progress. It cleared a visible popup, then guessed unsupported terminal/help commands instead of consulting the available game guide. |
| Guided Qwen3.6 / 7 | Exhausted after 14 steps and 15m 17s; 14 requests, including 2 timeouts | Authored and deployed `crimes.js`, but visible execution failed because it required 81.60 GB RAM. Money remained about $1.262k and hacking remained level 1. It looked up `commitCrime`, then repeated deployment variants without resolving the RAM failure. |

The latest observed blocker is a script-RAM requirement, not editor access. The
deployment helper now avoids rewriting identical file contents and action
summaries retain visible RAM/runtime errors as failures. This is not yet
validated by a new gameplay session because a read-only endpoint check found a
model already loaded on shared inference; an additional run was withheld to
avoid resource contention. The update therefore has automated test coverage
and a live disposable UI-helper check, but no new gameplay result.

## Compact-model reliability follow-up (2026-11-05)

After confirming the local inference GPUs were idle, six sequential isolated
runs used `gemma4:e4b` Q4_K_M with screenshot and tool-call capabilities on the
same fresh v3.0.1 seed. These are not comparable to the earlier Qwen3.6 model
trials because the model and harness version differ.

| Run | Steps | Inference time | Tool calls | Evidence |
|---|---:|---:|---:|---|
| 04 | 3 | 75.3s | 3; 2 failed | Repeated a missing script read after generic bridge 500 responses. |
| 05 | 5 | 163.7s | 5; 4 identical reads | Not-found feedback was returned, but the model repeated the same read; operator stopped. |
| 06 | 5 | 223.9s | 5; 2 failed, 2 no-progress | Dismissed the offline popup and ran `ls`, then issued malformed API-reference queries and guessed another absent filename. |
| 07 | 4 | 139.6s | 4; 3 no-progress | Repeated an absent-file read; the repeated-failure guard stopped the session. |
| 08 | 9 | 378.5s | 9; 5 no-progress | Authored and revised code after “no main function,” but the same run was blocked until a diagnostic Terminal command; never verified income. |
| 09 | 10 | 414.3s | 10; 1 failed, 3 no-progress | Authored and deployed code, but a visible runtime-error modal still said the script lacked a main function; no final stat verification. |

Across these runs no money increase was confirmed. Run 09 processed 47,070
prompt tokens and 2,841 output tokens. The Ollama model report showed 3.745 GB
allocated in VRAM; GPU utilization varied by sample, and the inference calls
were sequential. Details and screenshots are retained only in ignored local
trial records. This follow-up did not use an action model and does not establish
that the documentation or fixes can complete autonomous gameplay.

## Post-outage seed and completion-gate follow-up (2026-11-05)

The first attempt was setup-only: the seed source pointed at a parent directory
with a nested `profile/`, so the benchmark copied the wrong Chromium user-data
root. It correctly stopped before inference when Bitburner did not show Remote
API Online. A new disposable seed was configured and saved through the visible
game Options UI, then verified Online after browser-session recreation.

| Run | Result | Tool and game evidence | Inference |
|---|---|---|---|
| 10 | Exhausted after 6 Browser Use history steps | Empty filename read; unsupported API calls; malformed structured response. It reported that its deployed script had not been run. No income verified. | 7 requests; 258.6s summed time; 41,678 prompt / 1,683 completion tokens; first load 5.02s. |
| 11 | Exhausted after 11 history entries (10 action steps) | Repeated speculative deployments; Bitburner displayed a `main function` runtime error. No verified script run or balance increase. | 11 requests; 418.2s summed time; 49,501 prompt / 2,927 completion tokens; first load 0.54s (warm model). |
| 12 | Exhausted after 10 history steps | Qwen queried `ns.hack`, authored and deployed `hack-n00dles.js`, and visibly started it (PID 1). Bitburner v3.0.1 then reported `formatNumber` was removed in 3.0.0 and named `ns.format.number()` as the replacement. The HUD at run confirmation remained $1.262k / Hack 1; the model reported incomplete and no income was verified. | 10 requests; 508.3s summed request duration; 77,964 prompt / 1,314 completion tokens reported; cold load 49.2s; 11m46s from first to last node sample. |
| 13 | Failed after 3 history steps | Remote API was Online, but the game showed an offline-progress dialog. The model repeated `game_observe`; the no-progress guard stopped the session. No Netscript was authored or deployed. | 3 requests; 59.9s summed duration; 12,456 prompt / 187 completion tokens; model was warm. The 68-second node sample interval had no meaningful gameplay progression. |
| 14 | Failed after 5 steps | The updated startup instruction worked: Qwen dismissed the visible offline-progress dialog and resumed terminal observation. Ollama then disconnected twice (`Server disconnected without sending a response`, then connection failure). No script was authored or deployed; final visible balance remained $1.262k / Hack 1. | Five inference attempts were recorded, three with responses and two transport failures. No retry was made after the endpoint failure. The isolated session ended without gameplay progress. |
| 15 | Exhausted after 13 steps | Qwen scanned the network, authored six versions across `hack.js` and `hack_n00dles.js`, and repeatedly treated the pre-deployment `ls` output as current. The Remote API tool reported each write read-back verified and supplied RAM cost, but Qwen never called `game_run_script` or ran a Terminal command. It ended by explicitly reporting failure. Visible money remained $1.262k and hacking remained level 1. | 13 Ollama requests: 12 responses, 1 read timeout. Responses reported 101,469 prompt and 17,456 completion tokens; summed server request duration 702.5s; first model-load duration 16.1s. Trial telemetry spanned 14m57s. `/api/ps` reported about 23.0 GB VRAM allocation. Per-GPU SSH telemetry was unavailable. |
| 16 | Incomplete after 16 steps; operator-stopped during the supervisor's single-session delay | Starting money was visibly reported as $1.262k and hacking level 1. Qwen authored and deployed `hack-n00dles.js`, then visibly ran it. Bitburner showed `hack: Cannot hack n00dles server because you do not have root access`. Qwen repeated dialog-dismiss actions six times, had two 180s inference timeouts, then authored a revised script using `ns.nuke` but did not run it. No post-run money comparison or income was verified. The final visible dialog still showed the root error. | 14 Ollama responses: 98,276 prompt and 21,825 completion tokens; 815.8s summed response time; 17.6s first load; 19m45s from objective start to final response. Two 180s request timeouts were not included in Ollama response metrics. Model allocation peaked at about 23.0 GB across four GPUs; CPU offload was not measured. |

Runs 10 and 11 used `gemma4:e4b` (8B, Q4_K_M), 16,384 context, temperature 0.2, seed 7,
and the same bounded objective. The second trial sampled GPU peaks of 3.3 GB
and 2.1 GB, with utilization up to 100%. CPU offload was not measured. A
tested completion guard now rejects successful `done` claims for money tasks
unless the model has a visible positive script-run confirmation and a visible
balance increase after the run. The guard's positive and negative cases pass;
this model still did not meet the gameplay objective. The local inference
endpoint later returned and enabled the isolated Qwen follow-up in Run 12. No UI action model was tested;
that experiment remains deferred until a primary local model meets the income
gate. Sixteen documented isolated runs had not met that gate before Run 17. Run 16 exposed
an ineffective dismissal loop; the visible runtime dialog included a semantic
Close button, but the helper fell back to Escape when several modal buttons were
present. The updated helper selects a unique visible Close button from the
fresh DOM snapshot and refuses a repeated close attempt when the same dialog
remains. The always-loaded guide and per-session prompt now call for exact
runtime-error lookup, live API verification, and a single evidence-based retry.

### Guided Run 17 — first verified isolated income cycle

One fresh, disposable profile was tested with `qwen3.6:35b` (Q4_K_M), 16,384
context, temperature 0.2, seed 7, an 18-step limit, a 20-minute session limit,
the compact game guide, Browser Use, and the restricted Remote API. The model
received no code, target, or gameplay correction. It dismissed the initial
offline-progress dialog, inspected the visible network, obtained root on
`n00dles`, independently authored and deployed `hack-n00dles.js`, and visibly
launched it. It first tried an invalid compound Terminal command, read the
game's usage error, and recovered with valid separate commands. It then copied
the script to the rooted server and launched it there. The visible balance
changed from $1.262k to $1.583k (about $321); hacking remained level 1. The
terminal confirmed both launches, and `ps` showed the first process, but the
model did not produce a script `print`/income report. The positive balance
change is the income evidence; no hacking progression is claimed. No runtime
script error was visible at the final observation. This is one success, not a
repeatability result.

The session used all 18 model/tool steps and finished in 19m34s. All 18
inference requests returned without timeout: 189,988 prompt tokens, 24,761
completion tokens, 1,154.8 seconds summed request duration (64.2s mean, 52.8s
median), and 17.6s cold load. Aggregate Ollama evaluation throughput was 36.9
output tokens/s and prompt processing throughput was 411 tokens/s. Ollama
reported approximately 23.0 GB allocated to the model across four GPUs;
sampled GPU utilization reached 100% on each card. CPU offload was not
measured. The detailed run artifacts are retained locally and ignored by Git;
no internal node names, network details, saves, or model responses are
published.

This run meets the narrow gate of independently authored, visibly executed
Netscript with a positive visible money delta. It does not prove reliable
debugging of Netscript errors, repeated success, autonomous continuation across
sessions, hacking-level progression, or BitNode completion.

### Guided Run 18 — failed replication after the pending-run guard

Run 18 used a fresh copy of the same v3.0.1 seed, model, objective, tools,
16,384 context, temperature 0.2, seed 7, 18-step limit, and 20-minute ceiling.
The only harness change from Run 17 was the optional visible `expected_host`
check and a short instruction to use it when choosing a host. The initial
visible balance was $1.262k, Hack 1, and Remote API Online. The model dismissed
the offline popup, inspected files, scanned, selected `n00dles`, and visibly
used `run NUKE.exe` to gain root. It authored and deployed `hack-n00dles.js`
once through the restricted Remote API. It then made four redeployment calls
while the one-write guard returned the same `NO_PROGRESS` instruction to run
the already verified file. No further write was made. After repeated identical
failures, the supervisor stopped the session at 13 steps. The visible final
balance remained $1.262k and Hack remained 1. No Netscript execution or income
was verified; the run did not reach the new expected-host check.

The 13 inference requests returned without transport failure: 116,682 prompt
tokens, 14,054 completion tokens, and 659.6 seconds summed response time (50.7s
mean, 49.0s median). Cold load was 17.6s; aggregate prompt/output throughput was
421 / 38.8 tokens per second. Wall time from objective start to supervisor
failure was 11m08s. Ollama reported about 23.0 GB in VRAM at 16,384 context.
Across four 8 GiB cards, sampled utilization averaged 17–27% by card and peaked
at 100% on each; sampled memory use peaked at 7.6, 5.1, 6.2, and 5.7 GiB.
CPU offload was not measured. Trial artifacts remain in ignored local storage.

This replication failed the gameplay gate. It confirms that the write guard
prevented repeated writes but did not prevent repeated inference: the failure
signature included the model-authored source text, so small code changes reset
the repeated-failure counter. The source now normalizes this specific pending
run refusal, while preserving a recovery opportunity and allowing other
diagnostic actions to reset the streak. Its signature ignores changing source
and visible HUD text; a successful model-chosen action in the same response
clears this refusal streak, while passive observation alone does not. Ordinary
error signatures retain their previous behavior. Focused regression tests cover
these cases. Run 19 exercised this fix and is recorded below. Overall, Runs
17–19 contain two verified income cycles and one failed replication; reliable
completion and reporting are not established.

### Guided Run 19 — income after pending-run recovery

Run 19 used a fresh copy of the same v3.0.1 seed and the current source at
`3360ec9`, with `qwen3.6:35b` Q4_K_M, Browser Use, the restricted Remote API,
16,384 context, temperature 0.2, seed 7, an 18-step limit, and a 20-minute
session limit. The model received no code, target, or gameplay correction. It
scanned, gained root on `n00dles`, authored and deployed `hack_n00dles.js`, and
then received the pending-run refusal when it tried to redeploy before a
visible run. It returned to `home`, listed files, and ran that exact script;
the visible terminal confirmed PID 1. A later screenshot showed the running
process, a successful `n00dles` hack output of `$320.651`, and HUD money of
$1.583k versus the initial $1.262k (about +$321). Hacking stayed at level 1.
The first retained screenshot confirming income was 7m19s after the visible
script-run confirmation; the game may have earned money earlier.
This is an independently authored, deployed, and visibly executed
money-generating program. No Netscript runtime error occurred, so code repair
was not needed. The model received the success evidence in its browser
observation, but did not return a final written report.

The supervisor ended the session as `failed` at 17/18 steps after the
1,200-second session limit. The model recovered from one invalid structured
response, inspected the script and process list, and a repeated `tail` command
was blocked. The final response timed out at 180 seconds before it could
complete. Across 16 completed Ollama responses, the run used 148,113 prompt
tokens and 23,468 completion tokens, with 1,002.24 seconds summed response
time (62.64s mean, 60.66s median). One response consumed 179 seconds and 6,199
completion tokens before returning invalid JSON after consuming 16,384 combined
prompt and completion tokens, consistent with context exhaustion.
The model used about 23.0 GB VRAM across four GPUs; 232 GPU samples averaged
21.2% utilization and peaked at 100%, while sampled memory averaged 5.7 GiB
per card and peaked at 7.2 GiB. The screenshot evidence and detailed traces
remain in ignored local artifacts. Production was not used or changed.

Run 19 validates that the revised guard let Qwen recover from the pending-run
refusal and that its script earned money. It does not establish that the agent
can consistently finish a session, provide a concise result, recover from
Netscript runtime errors, or continue autonomously across sessions.

### Guided Run 20 — explicit `think:false`

Run 20 used a fresh copy of the same v3.0.1 seed and objective, with the same
Qwen3.6:35b Q4_K_M model, Browser Use and restricted Remote API tools, 16,384
context, temperature 0.2, seed 7, and an 18-step / 20-minute ceiling. The only
intended inference change from the model default was explicit `think:false`.
The model independently authored, deployed, and visibly ran
`hack-n00dles.js`. The initial HUD showed $1.262k and Hacking 1; a retained
screenshot 3m59s after task start showed the active script and $1.551k, and a
later screenshot showed $1.838k and Hacking 1. The visible Active Scripts panel
reported $576.303 production at $0.022/sec. This verifies about $576 of
observable income from a model-authored program; no hacking-level increase was
observed.

The supervisor marked the run `failed` after 13 steps / 7m15s because the model
repeated passive observations until the no-progress guard stopped it. Its
checkpoint had already recorded the objective as complete, and the screenshots
showed income, but it did not return a final report. No runtime error occurred,
so no code-debug cycle was needed. Fifteen completed responses used 143,053
prompt and 3,047 completion tokens; summed Ollama response time was 419.91s
(27.99s mean, 31.21s median). No timeout or malformed response was recorded.
Historical per-GPU samples for this run were empty because the sampler's SSH
command did not force the documented identity and strict host-key options;
GPU allocation and utilization for this trial are therefore unavailable. The
sampler was corrected and a later read-only smoke sample recorded four GPU
rows, but that does not reconstruct Run 20 hardware use.

Run 20 demonstrates income generation under `think:false`, while also exposing
a completion/reporting failure after success. It is one sample, not evidence
that `think:false` is a better setting: Run 19 and Run 20 both earned money,
but neither completed with a final report, and the benchmark has not repeated
either condition enough to rank them.

### Guided Run 21b — runtime-error recovery and progress-guidance repeat

The first Run 21 launch stopped before containers or inference because Compose
rejected a relative state-volume path; it is retained as a setup failure and is
not a gameplay trial. Run 21b used a fresh copy of the same v3.0.1 seed,
`qwen3.6:35b` Q4_K_M, explicit `think:false`, 16,384 context, temperature 0.2,
seed 7, an 18-step / 20-minute ceiling, and source commit `51dc457`. It tested
the post-run `game_progress` prompt and documentation after Run 20's repeated
observation loop.

Qwen dismissed the offline dialog, used visible `scan-analyze`, independently
authored and deployed `hack.js`, and ran it. Bitburner displayed a runtime error:
the script attempted to hack `n00dles` without root access. Qwen queried the
live `ns.nuke` reference, inspected its own script, and redeployed a revision.
It then copied the script to `n00dles`, connected there, and attempted to run it
while that server remained unrooted. It did not consult `game_troubleshoot` or
use `game_progress`; the model repeated blocked `run hack.js` calls until the
guard stopped the session as `failed` at 17/18 steps after 7m17s. The final
screenshot showed $1.262k and Hacking 1, unchanged from the initial HUD, with no
verified income.

The run produced 17 completed Ollama responses, 132,747 prompt and 3,894
completion tokens, and 420.95 seconds summed response time (24.76 seconds mean,
25.24 seconds median). No request timed out or returned malformed output. The
visible runtime error was saved in the checkpoint, but the metrics initially
reported zero `game_errors` because the dialog appeared after the run tool had
already returned its positive startup result. That telemetry defect and the
same-host `connect` loop are covered by follow-up harness fixes. The existing
guard still stopped consecutive identical blocked commands. Across 86 hardware
samples, the model occupied about 23.0 GB VRAM. Per-device peak memory was
7.5/5.0/6.1/5.5 GiB; mean utilization was 30.6/15.6/21.2/17.3%, with 100%
peaks on all four GPUs. CPU offload was not separately measured. Evidence stays
in ignored local artifacts.

Run 21b confirms that updated progress instructions alone did not prevent the
model's root/host confusion. It is a genuine Netscript debug failure, not an
income success; the model was not given a correction. The next controlled step
is a fresh isolated trial after making the visible root-access mechanics and
same-host `connect` guard clearer. Production was not used or changed.

### Guided Run 22 — isolated income repeat

Run 22 used a fresh copy of the same v3.0.1 seed, `qwen3.6:35b` Q4_K_M,
explicit `think:false`, 16,384 context, temperature 0.2, seed 7, and an
18-step / 20-minute ceiling. The model independently observed the game,
scanned, authored and deployed `hack_n00dles.js`, visibly ran PID 1, observed
the script output, and stopped it. A retained screenshot showed the HUD rise
from $1.262k to $1.551k and Terminal output attributing $288.750 and 3.300
experience to the successful hack. Hacking stayed at level 1. The code was
model-authored; no script or correction was supplied by the operator.

The session ended `failed` after 11 steps / about 5m59s: after the observed
success, the model made two identical passive `game_observe` calls. The
no-progress guard refused the repeats and stopped the session while the
checkpoint said it intended to verify final money. Thus gameplay income is
verified, but final reporting and recovery from guard termination remain
unreliable. The two counted `game_errors` were guard refusals, not in-game
runtime errors; this run did not exercise a Netscript debug cycle.

Thirteen Ollama responses used 124,477 prompt and 2,787 completion tokens.
Summed request time was 338.67 seconds (26.05s mean; 30.03s median), with a
17.57s initial model load and about 37.46 completion tokens/s. There were no
timeouts or malformed responses. Across 69 hardware samples, mean utilization
per GPU was 27.6/15.4/21.7/19.0%, with 100% peaks on each; peak VRAM was
7.39/4.94/6.06/5.53 GiB. CPU offload was not measured. Screenshot and raw
traces remain in ignored local artifacts. Production was not used or changed.

Run 22 repeats the Run 19/20 pattern: useful income can occur, but the model
may fail to conclude after seeing it. This is one successful isolated sample,
not proof of sustained autonomous play or BitNode progression.

### Guided Run 23 — isolated income and error-recovery repeat

Run 23 used a newly prepared v3.0.1 seed saved through the visible game UI and
confirmed Remote API Online after browser-session recreation. The trial used
`qwen3.6:35b` Q4_K_M, 16,384 context, temperature 0.2, seed 7, explicit
`think:false`, and a 16-step / 20-minute ceiling. The model received no script,
target, or code correction. It inspected the game, authored and deployed
`hack_n00dles.js`, then independently switched approaches after a visible RAM
failure (`crime.js` required 81.65 GB on home). It authored and deployed
`hack_n00dles_simple.js`, ran it through the visible Terminal, and its tail
window showed successful `n00dles` hacks credited with $288.750, $287.553,
$286.361, and $285.174, each with 3.300 experience. The initial HUD showed
$1.262k / Hack 1. A screenshot at 00:09:44 UTC showed $2.125k / Hack 1 and the
successful script output; a final visible observation at 00:10:46 UTC showed
$2.410k / Hack 1 while the script was still active. No hacking-level increase
was observed.

The first script was attempted about 4m55s after objective start; the first
visible successful hack output was captured at 7m37s. The model called
`done(success=true)` on step 16 and reported money at $1.838k,
but the supervisor ended the bounded run as `exhausted` at its step limit. The
final HUD evidence verifies positive income independently of that inconsistent
reported balance. The run included five game/tool errors, two duplicate
deployment refusals before running verified files, one 81.65 GB RAM rejection,
and repeated `game_progress` observations. It nevertheless recovered from the
RAM error by authoring and running a lower-RAM hacking script. There were no
inference timeouts or malformed responses.

Seventeen Ollama requests used 143,832 prompt and 4,010 completion tokens;
summed request time was 437.32 seconds (25.72 seconds mean, 26.48 seconds
median), including a 15.84-second initial load. Total objective time to the
final visible observation was 8m38s. Across 100 hardware samples, mean GPU
utilization was 27.7/13.6/18.3/15.0%, with 100% peaks; peak VRAM was
7.16/4.94/6.06/5.09 GiB. CPU offload was not measured. After cleanup all GPUs
returned to 0% utilization, no inference requests remained active, and the
model stayed resident at 16,384 context. Trial artifacts remain in ignored
local files; production was not used or changed.

Run 23 demonstrates independent recovery from a RAM-limited script attempt and
verified money generation, while also confirming that repeated ineffective
observations and end-state reporting remain weaknesses. It does not establish
reliable extended autonomy or BitNode progression.

After Run 23, the harness was updated so a guarded successful `done` marks a
bounded objective `completed`; long-term BitNode objectives still require the
separate visible BitNode completion proof. The regression suite passes 120/120
in a network-disabled candidate image. The fix was not deployed to the retained
shared test profile while existing game scripts remained active.

## Reproducing a trial

The isolated Compose deployment, objective, fresh-profile trial runner, and
hardware sampler are in `deployment/benchmark.compose.yaml`,
`benchmarks/gameplay-objective.md`, and `scripts/`. Configure the private
endpoints, exact installed tag, an unchanged clean seed profile, and a unique
state directory in ignored `local/` records. Run three trials per eligible
model sequentially. Never reuse trial state, modify the shared persistent test
profile, or expose private endpoint mappings in committed records. See
`scripts/run-benchmark-trial.sh`.
The runner checks that its agent and VNC loopback ports are distinct and unused
before contacting Ollama or starting containers; choose fresh port values when
another isolated trial still owns the defaults.

For a controlled Qwen thinking-mode comparison, leave `OLLAMA_THINK` unset for
the model default or set it to `false` (or `true`) for an explicit Ollama chat
parameter. The runner validates and records this setting. This option is
benchmark-only unless deliberately configured elsewhere; results must confirm
that the selected model honors it before treating it as a distinct condition.

## Run 24 — Qwen3.6 client-options recovery retest (isolated)

Run 24 replayed the clean Run 23 profile and objective with `qwen3.6:35b`
Q4_K_M (35.5B), explicit 16,384 context, thinking disabled, temperature 0.2,
and seed 7. It ran 11 of 16 available actions over about 4m56s and made 11
inference requests: 82,576 prompt tokens and 3,025 completion tokens. Request
latency ranged 18.4–32.6s; there were no inference timeouts or malformed
responses. The Ollama process endpoint reported the requested 16,384 context
after model load (two early samples still showed the pre-existing 65,536
runner); model VRAM allocation peaked at about 20.5 GiB. GPU utilization
sampling was unavailable in this run, and CPU offload was not measured.

The model inspected the visible server scan, independently authored and
deployed `hack-n00dles.js`, and ran it. Bitburner visibly rejected the first
run because `n00dles` lacked root access. The model then authored a revision
using the live game's root-access API and deployed it. Its next `run` result
was the same previous `hack-n00dles.js:L10` runtime error, despite the new
contents. The final visible DOM confirmed a runtime-error modal whose heading
was split across `RUNTIME` and `ERROR`. The modal matcher had checked for the
contiguous phrase, failed to classify the stale modal, and allowed its contents
to be read as the new command result. A whitespace-normalization fix and a
regression test now cover this exact UI rendering. The model did not establish
root, verified execution of the revision, income, or measurable progression;
this run is a gameplay failure, not an income result.

Trial logs, seed profile, and deployment configuration remain private and
ignored under `local/benchmark-runs/qwen36-prod-options-02/`. The trial used a
disposable browser/game profile and did not touch production or change any
Ollama server settings.

## Run 25 — Qwen split-line modal recovery (isolated)

Run 25 repeated the clean Run 23 starting profile and bounded income objective
with `qwen3.6:35b` Q4_K_M, context 16,384, thinking disabled, temperature 0.2,
and seed 7. The trial used the modal whitespace-normalization fix validated by
123 automated tests. It completed 16 actions in 6m51s, making 16 model requests
with 132,239 prompt tokens, 3,091 completion tokens, and 399.5 seconds summed
inference time (25.0s mean; 24.2s median). No request timed out or returned a
malformed response. Ollama reported 16,384 context across the sampled run and
peak model VRAM allocation of 21.46 GiB. All 81 remote GPU samples were
available; utilization was 0% during the samples recorded, though other
resident models occupied VRAM. CPU offload was not measured.

Qwen inspected visible files, authored and deployed `hack.js`, and ran it. The
visible runtime dialog reported that the first hack lacked root access. With
the split-line detector fixed, it dismissed the dialog and received the old
error as a diagnostic instead of mistaking it for a new run result. It first
tried an invalid Terminal `nuke` command, then independently revised and
redeployed the script to call `ns.nuke`. The visible Tail window confirmed
`NUKE.exe` granted root and subsequently showed successful n00dles hacks for
$288.750 and $287.553, each with 3.300 experience. The visible overview showed
money increasing from $1.262k to $1.838k (+$576). PID 2 remained active at
completion; no hacking-level increase was recorded (level 1 at start and end).
The bounded objective completed successfully.

The agent used five calls that were classified as game errors, including
repeated dialog dismissal, the invalid Terminal command, and a repeated `tail`
command that the no-progress guard correctly blocked. It recovered within the
same session without operator guidance or supplied code. The first successful
hack output was visible by 5m13s after session start. Trial configuration,
conversation traces, screenshots/DOM observations, and hardware samples remain
private and ignored under `local/benchmark-runs/qwen36-modal-fix-01/`. This
trial did not use or modify the shared persistent test profile or Ollama server settings.

## Run 26 — same-seed repeat (isolated; no income)

Run 26 repeated the Run 23 seed and objective with Qwen3.6:35b Q4_K_M, 16,384
context, `think=false`, temperature 0.2, seed 7, a 16-step cap, and a 20-minute
session limit. The initial and final visible balance remained $1.262k; no active
script or income was visible. Qwen independently authored and ran
`nuke_n00dles.js`; `scan-analyze 2` then visibly showed root access on n00dles.
It authored and deployed a money script but spent the remaining actions on two
repeat reads and `ps`, then ended without running that script. This is a
workflow failure, not a deployment or inference failure.

The run made 18 Ollama requests: 174,570 prompt and 4,556 completion tokens,
502.28 seconds summed inference time, no timeouts, and five visible game
errors. The longest request took 144.5 seconds. Across 127 GPU samples, each
card reached 100% utilization and model VRAM peaked at about 23.05 GB; CPU
offload was not measured. Trial artifacts and game progress remain in the
ignored, isolated `local/benchmark-runs/qwen36-repeat-02/` directory. The
retained shared test profile was not used.

Run 26 exposed that the agent could abandon a successfully deployed script
before execution. The follow-up source change now blocks script reads, API
lookups, unrelated Terminal commands, and task completion until that exact
deployment receives a visible run attempt from the visible `home` prompt.
The guard is covered by the automated suite; Run 27 will test it in a fresh
isolated profile. The guard does not author code or choose a gameplay strategy.

## Run 27 — pending-run guard trial (isolated; no income)

Run 27 used the same Qwen3.6:35b Q4_K_M tag and Run 26 conditions, verified
vision/tool capabilities, and the same clean seed and objective. It began at
$1.262k / Hacking 1. Qwen deployed and visibly ran `hack.js`; the game's
rendered Terminal result said the target needed root. Qwen then issued the
invalid Terminal command `nuke n00dles` and attempted the same script with a
target argument; visible output again reported no root access. After it
deployed a revised `hack.js`, the new pending-run gate correctly blocked
unrelated actions, but the existing no-repeat-PID guard also blocked running
the newly deployed changed file because its filename had a previous PID. The
session repeated that blocked result and failed after 14 actions. Final
read-only screenshot showed $1.262k / Hacking 1 and no attributable income.
Terminal showed the Remote API Online and visible run errors; the final game
observation listed two active-script PIDs, but neither yielded verified
earnings.

There were 14 successful Ollama responses (86,044 prompt and 2,051 completion
tokens), 261.75 seconds summed inference time (18.70 seconds mean, 33.84
seconds maximum), one 180-second request timeout, and three later Ollama
connection failures. The session lasted about 10m28s. Across 63 hardware
samples, GPU utilization peaked at 100%, 100%, 100%, and 88%; per-card VRAM
peaks were 7,329, 5,059, 6,201, and 5,207 MiB, and Ollama reported 23.05 GB
for the model. CPU offload was not measured. Evidence remains private under
`local/benchmark-runs/qwen36-pending-run-guard-01/`.

The source now permits a new visible run of a file when that exact filename is
the pending read-back-verified deployment, even if an earlier version already
received a PID. It still rejects an immediate repeat after that deployment's
visible run. The follow-up is covered by the network-disabled suite (128/128).
Run 27 exposed this collision; Run 28 below tests the correction in a fresh
isolated gameplay trial.

## Run 28 — pending-run recovery and verified income (isolated)

Run 28 used the candidate at commit `a6ae3c3`, Qwen3.6:35b Q4_K_M, a clean
copy of the same seed and objective, 16,384 context, `think=false`, temperature
0.2, seed 7, and the same 16-action / 20-minute bounds. The model had verified
vision and tool capabilities. It completed the bounded objective in 14 actions
and about 6m38s (03:40:55–03:47:33 UTC).

Qwen authored and deployed `hack_n00dles.js` and visibly ran it. Bitburner
returned an actual runtime error because n00dles lacked root access. Qwen
dismissed the dialog, first tried `NUKE.exe` with an argument, and received the
game's visible explanation that the Terminal program does not accept target
arguments. It then authored and deployed a revised script, visibly ran it on
home, and received `Gaining root access to n00dles...`, `Hacking n00dles...`,
and `Hack complete. Check your money.` The HUD showed $1.262k before the first
run and $1.551k after the successful run, a visible increase of $289. The
hacking level remained 1. This is observable model-authored progress; the run
does not establish a long-running income rate or sustained BitNode progression.

The new pending-deployment guard rejected a premature `tail` attempt and the
model immediately ran the exact deployed file. Later, the changed-file retry
passed the prior-PID gate; this is the first isolated run exercising both
guards end to end. Completion was accepted only after the model reported and
the visible UI confirmed the balance increase. There were two game errors,
zero tool failures, zero inference timeouts, and zero Ollama connection
failures.

The run made 15 Ollama responses (137,229 prompt and 2,963 completion tokens),
381.45 seconds summed inference time (25.43 seconds mean, 27.26 median, 34.61
maximum). Across 79 GPU samples, every card reached 100% utilization. Per-card
VRAM peaks were 7,329, 5,059, 6,201, and 5,207 MiB; Ollama reported 23.05 GB
for the model. CPU offload was not measured. Detailed trial data, screenshots,
and the isolated game remain private under
`local/benchmark-runs/qwen36-pending-run-guard-02/`. The shared persistent
test profile and Ollama service settings were not modified.

## Run 29 — root-access recovery without income (isolated)

Run 29b repeated the clean-seed objective with Qwen3.6:35b Q4_K_M, 16,384
context, `think=false`, temperature 0.2, seed 7, and a 16-action / 20-minute
bound. The isolated game began at $1.262k and Hacking 1. Qwen authored and
deployed `hack.js`, but its first execution failed because n00dles had no root
access. After four repeated dialog-dismissal calls and an invalid `nuke
n00dles` Terminal command, it authored and ran `nuke.js`. Visible output
confirmed `NUKE.exe executed on n00dles`; the final visible Terminal scan
reported root access. The model then redeployed equivalent `hack.js` instead of
running it, and exhausted its action budget. No money-making script execution
or income was confirmed: the visible balance remained $1.262k and hacking
remained level 1. The model's completion response was not accepted.

The run took 7m36s and used 16 Ollama responses: 141,922 prompt tokens,
3,318 completion tokens, and 442.4 seconds summed response time (27.65s mean,
28.11s median). It had zero tool transport failures and four game/tool errors.
Across 101 hardware samples, all four GPUs reached 100% utilization; VRAM
peaked at 7,575, 5,059, 6,211, and 5,675 MiB. Ollama reported 23.05 GB of
model VRAM allocation and 16,384 context. CPU offload was not measured. Private
artifacts remain under `local/benchmark-runs/qwen36-run29b/`. This failure
shows that root-access recovery is possible, but the model did not carry the
recovery through to executing its income script.

## Run 30 — visible income, unaccepted completion (isolated)

Run 30 tested the deployed no-dialog-repeat guard with Qwen3.6:35b Q4_K_M,
16,384 context, `think=false`, temperature 0.2, seed 7, and the same 16-action /
20-minute cap. The game began at $1.262k and Hacking 1. After visible scans,
Qwen authored and ran `nuke.js`; Terminal output confirmed root access was
granted on n00dles. It then authored `hack.js` with an infinite
`await ns.hack('n00dles')` loop and ran it with visible PID 2. The HUD later
showed $1.551k, an increase of $289 while that was the only newly running
income script; the initial offline-progress dialog reported $0.000 in script
earnings. Hacking remained level 1. This is observable income evidence from a
model-authored and executed script, but Qwen itself treated the increase as
possibly passive and did not verify or report attribution. It rewrote the
script repeatedly instead; two pending-deployment rejections and a repeated
`scan` consumed the remaining actions. The supervisor ended `failed` at step
14, so the bounded task was not accepted as complete. The no-dialog-repeat
path was not exercised by the model in this run; its behavior is covered by
tool tests.

The session lasted 6m08s and made 14 Ollama requests: 116,951 prompt and 3,231
completion tokens, 357.2 seconds summed response latency (25.52s mean, 27.82s
median, 31.57s maximum). There were four game/tool errors, no transport
failures, and no inference timeouts. Across 73 hardware samples, each GPU
reached 100% utilization; VRAM peaks were 7,329, 5,059, 6,211, and 5,207 MiB.
Ollama reported 23.05 GB allocated and 16,384 context; CPU offload was not
measured. Private evidence is under
`local/benchmark-runs/qwen36-dialogguard-01/`. The replay surfaced a second
harness defect: `game_progress` failed to parse the live HUD because Bitburner
renders its money label and value on separate DOM lines. The parser and
automatic session-baseline comparison have since been corrected and covered
by regression tests.

## Run 31 — prerequisite and execution-order failure (isolated)

Run 31 used the corrected progress-parser source, the same disposable starting
state and Qwen3.6:35b Q4_K_M configuration, 16,384 context, `think=false`,
temperature 0.2, seed 7, and a 16-action / 20-minute cap. It ended `failed`
after six actions and 2m22s. The visible scan showed n00dles had no root
access, but Qwen authored `hack.js` with an un-awaited `ns.hack(target)`, then
attempted two rewrites instead of running the already deployed file. The
pending-run guard stopped those unrelated actions. No script execution, income,
or hacking progression was confirmed.

Six Ollama responses used 46,567 prompt and 963 completion tokens, with 137.0
seconds summed inference latency (22.83 seconds mean, 24.20 median, 28.55
maximum). There were two game/tool errors, no transport failures or timeouts.
Across 29 hardware samples, GPU utilization peaked at 100%, 58%, 100%, and
100%; VRAM peaked at 7,329 / 5,059 / 6,201 / 5,207 MiB. The resident model
allocation was 23.05 GB; CPU offload was not measured. Private artifacts remain
under `local/benchmark-runs/qwen36-progress-01/`.

The compact system instructions now explicitly require visible root access
before hacking, awaiting asynchronous hack/grow/weaken calls, and visibly
running the verified deployment before editing it again. These are workflow
constraints, not a supplied gameplay strategy or script. They still require a
new isolated trial; Run 31 did not validate the progress parser because the
model never executed a script.

## Run 32 — partial income, unresolved runtime error (isolated)

Run 32 tested the updated compact workflow instructions with Qwen3.6:35b
Q4_K_M, 16,384 context, `think=false`, temperature 0.2, seed 7, and a 16-step /
20-minute cap, using a fresh copy of the same seed and objective. The model
observed $1.262k and hacking level 1. It scanned and saw n00dles had no root,
but still deployed and ran an un-awaited hack call. The visible error confirmed
the missing root. Qwen then tried two invalid Terminal invocations, before
authoring a revised Netscript that called `ns.nuke`, awaited `ns.hack`, and
attempted an unsupported `ns.getMoney` call. It visibly ran the revised file
with PID 2; an isolated profile clone later showed the actual runtime error
`TypeError: ns.getMoney is not a function`.

The model did not resolve that final error or verify its balance itself. In a
separate no-inference observation of a copy of the run profile, Bitburner
reported `$0.197` in script earnings for 53 seconds offline, and the visible
HUD showed $1.551k, $289 above the model-observed start. This is evidence of
partial, model-authored gameplay progress, not an accepted autonomous cycle:
the model did not diagnose the last error or report the money change, and no
hacking-level increase was confirmed.

The agent log said “Completed 10 steps,” while the last persisted callback
checkpoint was at step 11 and remained `active` with no outcome. The benchmark
controller lost its API while polling final status and exited before writing
final-status or final-observation files. A copy of the profile enabled visual
follow-up. The local runner has since been changed to retry status polling,
record an explicit `api_unavailable` result, and save Compose logs and
container status before cleanup. Bash syntax checks and a local API-loss fault
injection passed, including assertions for status and observation sentinels,
Compose logs, and container-state records. A second live inference run has not
yet exercised this recovery path.

The run made 11 Ollama responses with 95,625 prompt and 2,286 completion
tokens. Summed response latency was 285.9 seconds (26.0 seconds mean, 35.0
maximum); elapsed time was about five minutes. There were three recorded
game/tool errors, no transport failures, and no inference timeouts. Across 57
hardware samples, all four GPUs reached 100%; VRAM peaks were 7,329, 5,059,
6,201, and 5,207 MiB. Ollama reported 23.05 GB model allocation; CPU offload
was not measured. The isolated run and its visual follow-up remain private
under `local/benchmark-runs/qwen36-root-prereq-01/`.

### Reproducible checkpoint continuation

The isolated benchmark runner now supports continuing an interrupted run from
`BENCH_CONTINUE_FROM=<prior-run-directory>` instead of `BENCH_SEED_PROFILE`.
The source must have an active runtime and latest checkpoint, and must match the
current objective, exact model digest, thinking mode, context, temperature, and
seed. The runner copies only the browser profile and checkpoint files into a
new trial state; it excludes Chromium singleton process markers and refuses to
overwrite an existing trial. This mode is intended for recovery experiments,
not clean-seed comparisons. It has been tested against Run 32's private
artifacts without inference. A follow-up gameplay run still requires a separate
inference reservation and has not started.

## Run 33 — Type Error recovery regression (isolated)

Run 33 continued the interrupted Run 32 profile with Qwen3.6:35b Q4_K_M at
16,384 context, `think=false`, temperature 0.2, seed 7, with limits of 16
actions or 20 minutes. It ended `failed` after four steps and four model/tool
calls in about 92 seconds. The four responses used 23,570 prompt and 624
completion tokens, with 88.65 seconds summed latency (22.16 seconds mean,
30.19 maximum). Two game/tool errors occurred; there were no inference
transport failures or timeouts. No script correction, income, or hacking
progression was verified.

The model dismissed the offline-progress notice, ran `ls`, and saw `hack.js`.
It then encountered `TypeError: ns.getMoney is not a function`. The saved
Bitburner v3.0.1 snapshot showed the error panel as bare divs, with no dialog
role, `aria-modal`, or MUI dialog root, while exposing a visible `Close`
control. The old detector therefore reported no dialog. Qwen repeated the same
dismissal after `NO_PROGRESS`, and the stagnation guard stopped the run. The
detector now recognizes rendered `TYPE ERROR`/`RUNTIME ERROR` text only when
script and PID fields are present, then accepts a unique visible `Close`
control from a fresh Browser Use accessibility snapshot. The copied profile
did not reproduce the error panel immediately after reload. Run 34 later
reproduced the error by running the saved failing script and verified the
model recovered. Focused and full offline tests cover this behavior; the
Run 33 candidate passed 149 tests at that point; deployed candidate `60480e5`
passed 152/152, and session-number fix `e3a1a62` passed 154/154 in the pinned
runtime image. Private evidence is under
`local/benchmark-runs/qwen36-runtime-recovery-01/`.

## Run 34 — independent runtime-error recovery and income (isolated)

Run 34 used Qwen3.6:35b Q4_K_M with Browser Use, the restricted Remote API,
the same compact game instructions, 16,384 context, `think=false`, temperature
0.2, seed 7, and a 16-step / 20-minute bound. It began from a disposable copy
of the saved test profile containing the previously model-authored but broken
`hack.js`; it was a recovery trial, not a clean-seed comparison. No script,
target, or corrected API was supplied to the model.

The visible HUD began at $1.262k and hacking level 1. Qwen used visible
`ls`, read the listed `hack.js` through the restricted script tool, then ran it
through the in-game Terminal. Bitburner showed `TypeError: ns.getMoney is not a
function`. Qwen identified the invalid call, authored a replacement using
`ns.getServer`, deployed it through the Remote API, and ran that file through
the Terminal. It opened the built-in Active Scripts page and called `done`
after reporting a balance of $1.838k. The visible game showed $1.551k after the
first run and $1.838k after the corrected run, a rounded +$287 after
correction and +$576 from the session baseline. The Active Scripts UI showed
$576.303 total production since the last augmentation and $0.009/sec; hacking
remained level 1. The script was no longer active at the final observation.
This is the first measured Qwen trial in this series to recover from the
`ns.getMoney` runtime error and verify income from the corrected script.

The agent completed 11 action steps in 5m13s (from objective start to its
verified completion); the corrected script was visibly run at 3m38s and the
final observation was captured at 5m13s. Twelve Ollama responses completed
without transport errors or timeouts: 105,704 prompt tokens, 2,286 completion
tokens, and 303.1 seconds summed request latency (25.3 seconds mean). Cold
model load took 15.9 seconds. Aggregate throughput was 469 prompt and 38.1
output tokens/sec. Ollama `/api/ps` recorded 23.05 GB of VRAM allocation at
16,384 context. Per-GPU utilization/memory and CPU offload could not be
measured because SSH telemetry authentication was unavailable in the test
workspace. One later `game_progress` call contained a malformed baseline
argument; the model then verified progress in the rendered Active Scripts UI.
The follow-up harness change now rejects incomplete currency strings and
non-integer hacking baselines while preserving the current rendered stats in
an actionable error response.

The Run 34 image passed 149/149 offline tests. The separate disposable
browser-helper test verified one tutorial-page transition, deliberate tutorial
exit, fresh semantic tab navigation, and visible Terminal `ls`; neither used
model inference. After the baseline-validation correction, the current
candidate passes 152/152 tests. All Run 34 artifacts, including its exact model digest,
visible observations, action log, and request metrics, remain in ignored local
storage. The shared persistent test-game profile was not used or changed.

## Run 35 — Terminal observation lag (persistent test game)

Run 35 continued the shared persistent **test** profile with Qwen3.6:35b
Q4_K_M, 16,384 context, `think=false`, temperature 0.2, seed 7, and a 16-step
bound. It stopped at the step limit after 7m51s. This was not a clean-seed
comparison. The model dismissed an offline-progress dialog, encountered a
1.70 GB RAM rejection when attempting to run its script on `home`, and used
visible `scan-analyze 1` output to discover that rooted `n00dles` had 4 GB RAM.
It authored/deployed `simple_hack.js` and visibly copied it to `n00dles`, but
did not connect there or execute it. No income or hacking-level change is
attributed: the final rendered state showed $71.733k and hacking 154, but the
starting state was behind the dialog and was not captured.

The run made 17 successful Ollama responses (149,838 prompt and 3,661
completion tokens), with 453.5 seconds summed request time (26.7 seconds
mean), and no inference transport errors. It made 16 game-tool calls, with
eight visible game errors and no failed tool calls. Several Terminal calls
returned short selector fragments before later observations showed the actual
command echo and result. The deployed helper was therefore changed to wait up
to 2.5 seconds for fresh visible confirmation and to block blind duplicate
commands after an uncertain timeout. Regression coverage exercises delayed
output and the timeout guard. Run 35 used the old helper. The fix was deployed
as `c2379de` after passing 156 offline tests; Run 36 exercised a live Terminal
command but did not reproduce the delayed-snapshot condition. Private traces
and metrics remain in ignored local records.

## Run 36 — repeated RAM-guard rejection (persistent test game)

Run 36 continued the same persistent **test** profile after deploying commit
`c2379de`; it was bounded to 16 steps and manually stopped at stagnation. The
session used Qwen3.6:35b Q4_K_M at 16,384 context, `think=false`, temperature
0.2, seed 7. It ended after eight steps in 3m24s (08:31:16–08:34:40 UTC), with
eight Ollama responses, 61,353 prompt and 2,112 completion tokens, 197.4
seconds summed request time (24.7 seconds mean), and about 0.04 seconds model
load time. There were no inference transport errors. Tool metrics were eight
calls, six visible game errors, and zero framework failures.

The model dismissed an offline-progress dialog, attempted to dismiss it again
and received `NO_PROGRESS`, then successfully used visible `scan-analyze 2`.
It next made five variants of a `game_deploy_script` call for
`hack_n00dles.js`; each was blocked because the prior visible run had failed
the 1.70 GB RAM check on `home` and the harness required process/host diagnosis
before another write. Repeated failure detection ended the loop, and the
operator stop awaited the underlying run task. No script executed in Run 36.
The latest rendered HUD showed $71.749k and hacking 154, but no start HUD
baseline was captured; no income or level change is attributed.

Run 36 exposed a conflicting instruction in the system prompt: it required
every deployed script to run on `home`, even when visible RAM evidence said
that host could not run it. The prior checkpoint also carried a stale model
subobjective into the next session. The prompt was corrected to select the
execution host from visible root/RAM evidence and allow the documented
in-game copy/connect flow; failed saved subobjectives are marked historical.
The change passed 157 offline tests and was deployed as `667e4ab`; Run 37
showed that this instruction alone did not stop the model's repeated writes.
Run 36 did exercise one successful live Terminal action through the updated
fresh-observation helper (`scan-analyze 2`); it did not reproduce the delayed
snapshot condition. The exclusive inference slot was released after the run;
private request traces remain under ignored local artifacts.

## Run 37 — host prompt did not change RAM-retry behavior

Run 37 continued the same persistent test game after `667e4ab` deployed the
host-selection prompt and failed-checkpoint handling. Qwen3.6:35b Q4_K_M at
16,384 context, `think=false`, temperature 0.2, seed 7 ran for about 2m42s
(08:53:41–08:56:23 UTC) and stopped at six agent steps. Seven Ollama responses
used 48,403 prompt and 1,215 completion tokens; summed request time was 137.7
seconds (19.7 seconds mean), with about 0.03 seconds model-load time and no
reported transport errors. Tool metrics: six calls, four visible game errors,
zero framework failures.

The model again dismissed a dialog, repeated the dismissal despite `NO_PROGRESS`,
used visible `scan-analyze 2`, and attempted three code variants for the same
blocked `hack_n00dles.js` deployment on `home`. The RAM diagnostic guard
returned the same file/host failure each time. I stopped the session to avoid
further inference; no script ran. Post-run rendered stats were $71.763k and
hacking 155, but no session-start HUD baseline was captured, so neither a
money delta nor hacking gain is attributed. The game remains stopped at
session 4 / 6 steps. The prompt change did not correct this model behavior.

Run 37 also exposed that the supervisor's repeated-failure signature included
the complete proposed script content. As a result, harmless code variations
reset the stagnation counter even though the tool rejected each deployment for
the same file/host RAM condition. Commit `6e8f68a` normalizes these failures by
filename and host, so a second identical RAM-guard outcome stops the loop.
The 158-test suite passes and an in-container check confirmed different source
variants produce the same signature. Live validation is pending.

## Run 38 — deployment succeeded, Terminal guard deadlocked

Run 38 continued the shared persistent test game after `6e8f68a`, using
Qwen3.6:35b Q4_K_M at 16,384 context, `think=false`, temperature 0.2, seed 7.
It ended in terminal failure after about 4m13s including one bounded supervisor
retry. The model produced 10 responses (61,722 prompt / 1,944 completion
tokens; 185.6 seconds summed request latency, 18.6 seconds mean; about 0.03
seconds model load time), with no transport errors. The two sessions used six
agent steps total and three visible game-tool calls in the terminal retry.

The model dismissed the dialog, received the expected RAM rejection while
trying to redeploy `hack_n00dles.js`, then independently authored and deployed
`hack.js`. The tool failed to run it because the Terminal prompt was not
visible; the follow-up `game_terminal` path also checked for a prompt before
opening Terminal, so repeated calls could not recover. The supervisor stopped
after the configured bounded retry. The final rendered UI showed $71.779k and
hacking 155, equal to the captured post-dialog baseline; no script ran and no
Run 38 income or progression is attributed. The deployed `hack.js` remains
unexecuted in the persistent test game.

The local correction opens Terminal with the documented visible shortcut
before validating `expected_host` or a pending deployment, and retains precise
pending-run instructions across a failed checkpoint. All 160 pinned tests
pass. Deployment and a new bounded gameplay attempt are pending; do not count
this as a successful autonomous gameplay cycle.

## Run 39 attempt — actual prompt rendering not recognized

The bounded continuation used Qwen3.6:35b with the shared persistent test game
and the deployed `d8bb369` hidden-Terminal opening fix. After one visible dialog
dismissal, the rendered HUD showed $71.789k and hacking 155. The model then
attempted `run hack.js` twice. Both actions were rejected because the live
accessibility snapshot represents the Terminal prompt as `home` followed by
`]>`, while the code recognized only `[home /]>`. The operator stopped after
three agent steps; no script was executed and the balance/hacking baseline is
not attributed to this run. A parser update for both visible forms passes 162
pinned tests and awaits deployment and a repeat bounded trial.

### Run 39 continued — prompt fixed, RAM recovery still missing

After deploying `c268e46`, Qwen3.6:35b successfully passed the live Terminal
host check and reached visible Bitburner execution. The post-dialog HUD
baseline was $71.796k / hacking 155. `hack.js` was rejected on `home` at 1.70
GB required RAM; model-authored `simple_hack.js` was rejected at 1.85 GB. The
model then deployed `tiny_hack.js` without inspecting running processes or
Active Scripts, and repeated that deployment after the guard's rejection. The
operator stopped at nine steps. No script executed; no income or progression
is attributable to this attempt.

This isolated the next harness defect: an unresolved RAM rejection gated only
redeployment of the same filename, allowing the model to evade the diagnostic
step by renaming its script. The new cross-filename gate requires visible `ps`
or Active Scripts inspection before any new deployment. All 164 pinned tests
pass. This fix has not yet been deployed or live-validated.

### Run 39 continuation — stale generic file-listing instruction

After the cross-filename RAM gate was deployed, the next Qwen continuation
cleared the offline dialog, then called Terminal `ls` twice. The tool correctly
rejected both calls because `tiny_hack.js` was already deployed and awaiting
visible execution. The model did not execute the pending script and made no
game progress. The operator stopped at three steps. A dynamic session-priority
instruction now makes pending execution override the generic objective's file
listing request, and gives unresolved RAM errors a visible process-inspection
priority. All 166 pinned tests pass; this prompt change is not yet deployed.

### Pending-run priority prompt deployed

Commit `5552257` was deployed after the session-9 listing loop. The state-aware
session task now explicitly makes execution of a verified pending file the
first game action, ahead of generic file-listing directions; when no file is
pending, it prioritizes visible process diagnostics after a RAM rejection. The
rollout preserved the same test profile and terminal `operator_stopped` state.
No gameplay or inference has yet validated this instruction change.

### Run 39 session 10 — script started, income unverified

With the split-prompt parser, cross-file RAM gate, and pending-run priority
deployed, Qwen ran its authored `tiny_hack.js` on `n00dles` after `home`
rejected it for insufficient free RAM. The visible Terminal confirmed PID 5.
The model then inspected Active Scripts and saw an aggregate `$0.471/s` on
`home`, which it incorrectly attributed to `tiny_hack.js`; the completion
guard rejected its success report. The visible HUD at the end was $71.821k /
hacking 156. No immediate pre-run money value was persisted, so this trial does
not establish attributable income. The agent was operator-stopped at the
16-action cap. A follow-up harness change records the visible balance before a
run, ignores old PIDs when confirming a new command, and uses the pre-run value
for progress comparison. All 170 pinned tests pass. This change was deployed
and live-validated in the continuation below.

### Run 39 session 11 — model-authored loop executed; income remains too small to verify on HUD

The `d3c3691` build was confirmed running on the shared persistent test game
before this bounded Qwen3.6:35b continuation (16,384 context, temperature 0.2,
seed 7). The agent cleared the offline dialog, read `simple_hack.js`, authored
`hack_n00dles.js`, and deployed it through the restricted Remote API. Bitburner
rejected its first run on `home` because it required 2.05 GB RAM; the agent
copied its own file to rooted `n00dles`, connected visibly, and started it with
PID 5. Terminal output showed the script's weaken/grow/hack cycle. Visible logs
confirmed successful hacks of `$0.005` and `$0.010` (3.300 hacking experience
each); a later read-only view showed further `$0.014` and `$0.019` successes.
Other attempts failed or stole `$0`. The visible HUD was `$71.840k` at agent
stop and later `$71.842k` while the script remained active. This is a `$2`
displayed increase after the test began, but it cannot all be attributed to
this script: its visible successful transactions total only cents, and the
Active Scripts summary showed `$0.467/s` aggregate production. The script
itself is confirmed to have earned money; the full HUD increase is not
attributed. Hacking remained level 156.

The agent stopped after 14 tool calls (about eight minutes) when it repeated
`tail hack_n00dles.js` despite the `NO_PROGRESS` rejection. Tool metrics were
zero framework failures and seven game/tool errors, including transient DOM
fragments and the repeat guard. The agent is `operator_stopped`; the legitimate
Netscript process remains active in the preserved test game. No token/latency
telemetry was persisted for this deployed session. The run demonstrates
independent authoring, deployment, visible execution, RAM-error recovery, and
successful hacks. It does not establish how much of the displayed `$2` HUD
increase came from this script. The next check should observe the existing
script and HUD without changing the game state.

The run exposed a repetition-detection gap: identical rejected `NO_PROGRESS`
actions kept receiving a new failure signature while the background script
changed visible log text. The harness now ignores changing DOM text for an
explicit `NO_PROGRESS` result while still keying on the attempted tool action
and rejection; a different action resets the streak. A regression test covers
the live pattern. The 171-test suite passes in a no-network test container.
The fix was deployed in commit `6018a62` after archiving the test profile and
retaining a rollback image. Postflight preserved `operator_stopped`, browser
readiness, and Remote API Online. Restart reopened the saved script-log UI
alongside an offline-progress modal; its amount is not treated as current
balance or attributable income. A short visible verification continuation is
pending coordination for the shared inference slot.

A later read-only Remote API `getFile` call confirmed that the model-authored
`hack_n00dles.js` still exists on `home` after the restart. Its custom `tprint`
uses `toFixed(0)`, so its own `$0` line rounds away fractional-dollar results;
Bitburner's visible operation log is the evidence for the `$0.005`–`$0.019`
successes. The file was read only; no game state or script content was changed.

### Run 40 — bounded visible-state check; RAM error revealed

On 2026-11-06 at 11:10 UTC, the local inference queue showed no active
requests, `/api/ps` was empty, all four GPUs were idle, and the VM was
`operator_stopped`. Qwen3.6:35b then received a three-action, five-minute
observation-only objective. It made three `game_dismiss_dialog` calls; each
returned a dialog-remains error. The session was explicitly stopped at 11:11:58
UTC; status persisted `operator_stopped` at session 12, two completed steps.
The third tool result raced with the stop, so the action log has three calls
while the step counter has two. All three calls failed; two were counted as
game errors. Ollama recorded four responses: 20,430 prompt tokens, 1,324
completion tokens, and 86.829 seconds summed request time (21.707 seconds
mean). Model-load time summed to 15.851 seconds; mean prompt-evaluation and
output-evaluation times were 10.280 and 7.351 seconds per response. The agent
session occupied about 92 seconds wall clock.

The fresh rendered UI revealed that the offline-progress popup had transitioned
to a Bitburner runtime-error dialog for `hack_n00dles.js@home (PID -4)`. It
reported `weaken` dynamic RAM of 1.80 GB against 1.70 GB allocated, with
`hasRootAccess` and `weaken` listed as in-use functions and a stack at line 17.
This is evidence of a failed home-server attempt. The current balance was not
visible, so this run establishes no income or balance change. The model did
not modify, deploy, start, or stop a script. Qwen remained resident under
Ollama keep-alive after the request; a post-run `/api/ps` sample reported
23.05 GB VRAM allocated at 16,384 context (not a peak measurement). The
inference slot was released with no active request. The next gameplay trial should show
the model this visible error and let it diagnose and correct its own script
without supplied code.

### Run 41 — bounded recovery attempt; Terminal confirmation failure

On 2026-11-06, the isolated test game was given to local `qwen3.6:35b` at
16,384 context for up to 20 minutes. The run started at 11:45:42 UTC and ended
at 11:52:27 UTC in terminal `failed` state after two consecutive failed
sessions. The supervisor did not revive that terminal state. It recorded 13
action steps. Ollama recorded 13 responses: 84,230 prompt tokens, 3,872
completion tokens, 309.661 seconds summed request latency (23.820 seconds
mean), and 15.905 seconds summed model-load time. VRAM allocation was about
23.05 GB at 16,384 context; this is not a peak sample. GPU utilization was
0% at preflight and one later idle sample; no generation-time peak was
collected.

The model dismissed the offline-progress dialog, then tried to diagnose the
existing script through Terminal. It reported a visible balance of `$71.893k`
and hacking level 157, but did not capture a fresh before/after balance
comparison. The visible Terminal log showed repeated `Stole $0` output. The
model guessed that its hacking level was insufficient; visible
`scan-analyze 2` output instead showed `n00dles` required level 1 and had root
access. The displayed script source was unchanged and formats the stolen value
with `toFixed(0)`, so its own output rounds fractional dollars to `$0`. The
model did not author, deploy, or verify a repair, and this run proves no
attributable income.

The run exposed a harness defect: several Terminal commands were visible in
the final rendered UI after `game_terminal` had reported no new result within
2.5 seconds. The timeout did not include that latest UI text; repeated attempts
were then blocked by the duplicate-command guard, but the agent did not switch
to a useful inspection path and the supervisor stopped after two failed
sessions. The helper now waits up to 6 seconds and returns an `UNCONFIRMED`
result with the latest visible excerpt; the duplicate guard remains in force
and the prompt/tool guide direct inspection with `game_observe` or
`game_read_script`. Delayed-output, timeout, duplicate, and lifecycle summary
tests pass. The full 180-test suite passes with network disabled. The fix is
deployed in commits `f02ded9` and `738d751`; postflight preserved terminal
`failed` at session 14 with AUTO_RESUME enabled, so the agent did not restart.
The updated Terminal behavior still needs validation in a new bounded live
agent session. This run remains a failure and proves no attributable income.

### Run 42 — bounded script attempt; ReferenceError recovery failed

On 2026-11-06 from 12:25:31 to 12:30:14 UTC, the isolated test game was
continued with local `qwen3.6:35b` at 16,384 context, capped at eight action
steps. Preflight showed no queued/in-flight inference requests, no model loaded
on the inference host, and all four GPUs idle. The run used eight model
responses,
processing 72,435 prompt and 2,066 completion tokens. Summed Ollama request
duration was 238.785 seconds (29.854 seconds mean elapsed per response); mean
model-load duration was 1.987 seconds. A post-run idle sample showed 0%
utilization and 7.329/5.059/6.201/5.207 GiB allocated across the four GPUs;
this is a post-run allocation sample, not a generation-time peak.

Qwen dismissed the visible offline-progress popup, inspected the existing
script's RAM and available memory, stopped `hack_n00dles.js`, authored and
deployed `hack_n00dles_fast.js`, and attempted to run it. The new script
produced a visible Bitburner `REFERENCE ERROR`: `ReferenceError: ns is not
defined` at line 16. The run tool correctly returned `UNCONFIRMED` because no
fresh Terminal result arrived within six seconds; the subsequent rendered UI
showed the actual error modal. Qwen called `game_dismiss_dialog` twice, but
both calls incorrectly reported that no dialog was visible. The agent was
explicitly stopped at eight actions. The final screen showed the error modal;
no current balance or hacking-level delta was visible, and no attributable
income was verified. The new script failed and was not independently debugged
or corrected.

The observation exposed a second harness defect: the modal detector handled
`RUNTIME ERROR` and `TYPE ERROR`, but not Bitburner's rendered `REFERENCE
ERROR` heading. A regression now recognizes that heading and uses only a fresh,
unique visible Close button. The focused tests pass, and the network-disabled
full suite passes 181/181. The fix was deployed from commit `9b8d82d` after the
agent was explicitly stopped, persistent test data was archived and validated,
and the previous image was retained for rollback. Postflight verified the
deployed source hash, browser readiness, Remote API Online, and noVNC HTTP 200;
the agent remains `operator_stopped` at session 15. The restored browser shows
an offline-progress modal with an aggregate amount; this is not a current
balance or income measurement. All Bitburner instances are test games.

### Run 43 — live dialog recovery and second Netscript error

On 2026-11-06 from 12:44:59 to 12:48:49 UTC, the deployed build was tested on
the same isolated game with local `qwen3.6:35b` at 16,384 context. The run
recorded nine action steps before the emergency stop (the requested eight-step
bound was exceeded by one action while the stop raced a tool response). Ten
Ollama responses processed 76,863 prompt and 2,212 completion tokens; summed
request duration was 218.516 seconds (21.857 seconds mean elapsed per
response). The model was already resident; summed model-load time was 0.039
seconds. Preflight sampled 0% GPU utilization and 7.329/5.059/6.201/5.207 GiB
allocated across the inference host's four GPUs; this was before generation, and no
generation-time peak or CPU offload measurement was collected.

The model reran its own earlier file and the deployed modal helper detected
and dismissed the resulting `REFERENCE ERROR`. It then read the script,
identified that Netscript code outside `main(ns)` caused `ns is not defined`,
authored and redeployed a correction, and ran it again. The visible runtime
error then changed to a `TYPE ERROR`: `spawn` rejected an array-valued script
argument at line 20. This shows the model recovered from the first error and
exposed a second bug, but did not finish debugging it within the bounded run.
The UI showed positive Terminal PIDs for two run attempts. At the final
read-only observation the rendered HUD showed `$71.947k` and hacking level
157; no before/after baseline was recorded, so no money delta or income is
attributed to the new script. A prior script's `$1` log line was visible, but
it cannot be attributed to this run. Explicit stop persisted
`operator_stopped` at session 16; no continuation was started.

A read-only observation at 12:55:31 UTC showed `$71.949k` versus `$71.947k`
at 12:48:50. The terminal also displayed `$0`/`$1` result lines from
`hack_n00dles.js` and positive PIDs for the new script. This $2 displayed
change is not attributed: the observation interval had no clean baseline,
multiple scripts may be involved, and the new script's second runtime error
was not verified as resolved.
