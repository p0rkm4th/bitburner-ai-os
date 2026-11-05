# Local model gameplay benchmark

## Scope and controls

All inference used existing local Ollama servers. The x1 laptop hosted only the
isolated browser and agent containers; no model was loaded there. Production
gameplay, profile, save, and model settings were left untouched. Each run got a
new copy of the same disposable Bitburner profile with the Remote API visibly
Online. No trial shared game progress with another trial.

The scored runs used the same objective, browser and restricted Remote API
tools, 16,384-token context, temperature 0.2, seed 7, 24-step ceiling, 30-minute
session ceiling, one session, and the same retry, history, and inactivity
limits. The game objective supplied no code, target, or Netscript correction.
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
| Primary challenger | `qwen3.8:27b` | Official 27B tag; 18 GB Q4_K_M catalog build | Vision and tool support; Apache-2.0 | Deep inference pool; not scored because Ollama 0.31.1 rejected the pull with HTTP 412 requiring a newer Ollama version. Ollama was not upgraded for this benchmark. |
| Coding challenger | `devstral-small-2:24b-instruct-2512-q4_K_M` | 24B, Q4_K_M; 15.2 GB model, 18.2 GB reported GPU allocation | Vision and tool support; Apache-2.0 | Deep inference pool; installed and benchmarked |
| VRAM-sized candidate | `gemma4:12b` | 11.9B, Q4_K_M; 8.7 GB model, 8.7 GB reported GPU allocation | Vision and tool support; Apache-2.0 | Compact inference pool; installed and benchmarked |

Catalog tags and requirements were checked before pulling Devstral. Its exact
tag requires Ollama 0.13.3 or later; the serving endpoint was 0.31.1. The
official Ollama catalog lists Qwen3.8's 27B, 18 GB tag, but this endpoint
requires a newer Ollama release. All three tested models reported the entire
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

## Results

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

Do not switch production to a challenger based on these runs. Qwen3.8 remains
untested because the local Ollama server needs an upgrade; that upgrade is
outside this isolated benchmark. Revisit model selection only after correcting
the harness/gameplay failure modes and measuring a candidate that can complete
the same end-to-end objective. No production model setting was changed.

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

Both used `gemma4:e4b` (8B, Q4_K_M), 16,384 context, temperature 0.2, seed 7,
and the same bounded objective. The second trial sampled GPU peaks of 3.3 GB
and 2.1 GB, with utilization up to 100%. CPU offload was not measured. A
tested completion guard now rejects successful `done` claims for money tasks
unless the model has a visible positive script-run confirmation and a visible
balance increase after the run. The guard's positive and negative cases pass;
this model still did not meet the gameplay objective. The primary-model outage
prevents a fair follow-up with `qwen3.6:35b`. No UI action model was tested;
that experiment remains deferred until a primary local model meets the income
gate.

## Reproducing a trial

The isolated Compose deployment, objective, fresh-profile trial runner, and
hardware sampler are in `deployment/benchmark.compose.yaml`,
`benchmarks/gameplay-objective.md`, and `scripts/`. Configure the private
endpoints, exact installed tag, an unchanged clean seed profile, and a unique
state directory in ignored `local/` records. Run three trials per eligible
model sequentially. Never reuse trial state, use production profiles, or expose
private endpoint mappings in committed records. See `scripts/run-benchmark-trial.sh`.
