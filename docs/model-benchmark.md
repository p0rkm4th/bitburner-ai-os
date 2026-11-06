# Local model gameplay benchmark

## Scope and controls

All inference used existing local Ollama servers. The x1 laptop hosted only the
isolated browser and agent containers; no model was loaded there. Production
gameplay, profile, save, and model settings were left untouched. Each run got a
new copy of the same disposable Bitburner profile with the Remote API visibly
Online. No trial shared game progress with another trial.

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
| Primary challenger | `qwen3.8:27b` | Official 27B tag; 18 GB Q4_K_M catalog build | Vision and tool support; Apache-2.0 | Not scored. The original Ollama 0.31.1 pull returned HTTP 412. A later read-only check found Ollama 0.40.14 on the current local endpoint, but the exact tag is still absent from its catalog. No download or generation has been performed; local resource and scheduling checks remain pending. |
| Coding challenger | `devstral-small-2:24b-instruct-2512-q4_K_M` | 24B, Q4_K_M; 15.2 GB model, 18.2 GB reported GPU allocation | Vision and tool support; Apache-2.0 | Deep inference pool; installed and benchmarked |
| VRAM-sized candidate | `gemma4:12b` | 11.9B, Q4_K_M; 8.7 GB model, 8.7 GB reported GPU allocation | Vision and tool support; Apache-2.0 | Compact inference pool; installed and benchmarked |

Catalog tags and requirements were checked before pulling Devstral. Its exact
tag requires Ollama 0.13.3 or later; the serving endpoint was 0.31.1 during
that benchmark. The official Ollama catalog lists Qwen3.8's 27B, 18 GB tag.
Later read-only checks found Ollama 0.40.14 on the current local endpoint, but
did not find the tag installed; no pull or generation has been performed.
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

Keep `qwen3.6:35b` as the production model for now. It was the most reliable of
these tested candidates at generating tool actions and Netscript attempts, read
official definitions in one run, and was the fastest tested model. It still
failed the gameplay goal in all three trials, so this benchmark does **not**
validate autonomous gameplay. Devstral's code focus did not offset its lower
throughput and inability to recover from a blocked dialog. Gemma 4 should not
be selected for this harness given repeated long timeouts and zero script
authoring.

Do not switch production to a challenger based on these runs. At the time of
this initial benchmark, Qwen3.8 could not be pulled because the serving Ollama
version was too old. The owner later reported that the Ollama servers had been
updated; exact installed tags, current compatibility, and gameplay quality have
not yet been reverified. Revisit model selection through a controlled isolated
comparison. No production model setting was changed.

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
in a network-disabled candidate image. This fix is not deployed to the
production browser while existing game scripts remain active.

## Reproducing a trial

The isolated Compose deployment, objective, fresh-profile trial runner, and
hardware sampler are in `deployment/benchmark.compose.yaml`,
`benchmarks/gameplay-objective.md`, and `scripts/`. Configure the private
endpoints, exact installed tag, an unchanged clean seed profile, and a unique
state directory in ignored `local/` records. Run three trials per eligible
model sequentially. Never reuse trial state, use production profiles, or expose
private endpoint mappings in committed records. See `scripts/run-benchmark-trial.sh`.

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
trial did not use or modify the production profile or Ollama server settings.
