# Optional UI action model evaluation

## Decision

Do not integrate Laya or Fast Browser Use. A bounded CPU replay of a recorded
Bitburner DOM trace shows Laya can rank a visible Script Editor target, but the
existing deterministic semantic helper already selects and validates that
target in about 0.15 seconds including its settle delay. Laya adds cold-load
and inference overhead, and there is only one replay row with no end-to-end
gameplay comparison. Keep the existing helper.

The current low-complexity path is the deterministic visible-UI helper set in
`app/game_tools.py`. It resolves fresh visible labels, rejects ambiguous or
missing targets, checks modal state, executes through the shared Browser Use
session, and verifies the rendered transition. The 86-test suite covers
stale/ambiguous targets, blocked dialogs, terminal results, and navigation. A
live integration check on a disposable profile dismissed the offline popup,
opened Create Program by its fresh semantic label, and returned visible
Terminal `ls` output. This is not a comparative model benchmark.

## Candidate review

| Candidate | License and scope | Runtime and compatibility | Assessment |
|---|---|---|---|
| Laya Browser Mind2Web, 421M | Apache-2.0 model; the training dataset is CC-BY-4.0. It predicts a typed action and target from DOM candidates; it does not use screenshots or generate text. A separate local LLM must fill text values. Its serving path expects Laya's typed-question format and matching formatter/lexical shortlister. | Pinned fp16 safetensors checkpoint; 843 MiB. It is not an Ollama model. Offline CPU replay loaded successfully. | In one saved Bitburner trace, it selected the visible Script Editor from 20 reconstructed candidates with p=.9741 in 0.727s after a 20.241s cold load; peak RSS was 2,835.9 MiB. This is one candidate-selection result, not general accuracy or live-game evidence. The existing deterministic helper is far faster on the same target. Do not integrate. |
| Fast Browser Use | MIT-licensed standalone local browser-use engine, not a tiny action model or adapter for the current shared Browser Use session. | Requires Python 3.12+, Playwright >=1.58, and uses Qwen3.5-9B or Qwen3.5-35B-A3B with PyTorch on Linux/NVIDIA. The current browser image pins Playwright 1.56. The repository recommends 24GB VRAM for 9B BF16; the available cards are 8GB each. Its own benchmarks use an RTX PRO 6000 96GB. | Not compatible with the current image and resource envelope as documented; introduces another browser runtime and a much larger model. Do not integrate for this task. |

Sources: [Laya Browser model card](https://huggingface.co/Quantum08/laya-browser-mind2web),
[Fast Browser Use repository](https://github.com/APUS-AI-Lab/fast-browser-use), and
[Fast Browser Use dependency manifest](https://github.com/APUS-AI-Lab/fast-browser-use/blob/main/pyproject.toml).
These are upstream claims and requirements, not local performance measurements.

## Comparison status

| Workflow | Evidence | Outcome |
|---|---|---|
| Primary model only | Isolated Run 25: Qwen diagnosed a root-access error, independently revised its Netscript, then visible Tail output showed two successful hacks and a $576 HUD increase. | Basic authored/deploy/run/debug/income cycle now demonstrated. One bounded success does not establish reliable extended autonomy. |
| Deterministic UI helpers | The relevant UI helper tests pass 29/29 on the replay branch; the main candidate's complete suite passed 123/123. A disposable-profile integration check returned actual Terminal output. | Functional and low-cost; directly matched the target in 0.151s median including the settle delay. |
| Tiny model assisted | One offline replay of the saved Devstral stale-index trace; no live game or gameplay inference. | Laya selected the semantic target correctly, but added no avoided primary-model call and was slower than the deterministic helper. Not enough evidence to integrate. |

The uncontrolled production trace is not a model benchmark. Run 25 does pass
the basic isolated income objective, but it does not establish repeatable
long-term autonomy or BitNode progression. The tiny model was not run in a
live gameplay task.

## Benchmark status

The offline replay used Laya Browser 421M, weights revision
`d590805f9972d021d8988a98a39f6395ac78f9e0`, Apache-2.0, fp16 safetensors.
The recorded v3.0.1 DOM showed a unique `Script Editor` label; the prior
Devstral workflow repeated stale index 20. Laya selected the correct
`script_editor` from 20 reconstructed candidates (p=.9741) in 0.727 seconds.
Cold load was 20.241 seconds and peak RSS 2,835.9 MiB. CUDA was disabled and
GPU use was zero. This is one reconstructed snapshot, not a multi-trial action
benchmark.

The existing deterministic `find_visible_tab_node` helper matched the same
target in 10,000 iterations at 0.003683 ms mean / 0.004028 ms p95. The mocked
whole helper had 0.151 seconds median including its built-in 150 ms settle
delay. The game-helper suite passed 29/29 tests offline in 6.75 seconds.
The replay does not demonstrate live UI action or income, and Laya cannot
reduce a primary-model call when the primary model already returns the stable
semantic label. Its extra loading/memory cost is not justified by this result.

Fast Browser Use remains excluded because its documented model and dependencies
do not fit the current browser runtime without changing the architecture.

Only the stale-index case was replayed. Repeated-click, blocked-dialog, and
failed-navigation replay rows remain outstanding. Existing deterministic
helper tests cover those behaviors, but the single Laya snapshot does not
establish that a model-assisted path reduces invalid actions or elapsed
end-to-end gameplay time. No evidence supports adding the extra model.

Reconsider integration only if a broader replay set shows repeated stale-target
or navigation failures that the current semantic helpers do not resolve.
Compare the same recorded cases and, if justified, equivalent disposable live
tasks against the helper baseline. Count successful actions, avoided primary
calls, invalid/repeated actions, elapsed time, resource use, and verified game
progress. Keep gameplay strategy and code authorship exclusively with the
primary LLM.

## Follow-up verification (2026-11-04)

The upstream model card and Fast Browser Use README/manifest were rechecked.
Laya remains an Apache-2.0, 421M-parameter F16 typed action/target selector.
It requires the Laya typed-question formatter and lexical shortlist to reproduce
its reported scores, does not generate text, and has no live-page evaluation.
Its published end-to-end task success is 2.3% to 4.0% on Mind2Web splits; the
card explicitly describes it as a research/hobby checkpoint. These results do
not establish reliable Bitburner UI behavior. [Model card](https://huggingface.co/Quantum08/laya-browser-mind2web)

Fast Browser Use is MIT licensed, requires Python 3.12+ and Playwright >=1.58,
and its documented local inference path uses Qwen3.5-9B or Qwen3.5-35B-A3B with
PyTorch/MLX. Its examples launch and control their own Playwright Chromium
session. That conflicts with this project's single shared Browser Use session
and pinned Playwright 1.56 image; it is neither a tiny action model nor a
drop-in action adapter. Its published timings use an RTX PRO 6000 96GB, so
they are not transferable to this deployment. [README](https://github.com/APUS-AI-Lab/fast-browser-use),
[dependency manifest](https://github.com/APUS-AI-Lab/fast-browser-use/blob/main/pyproject.toml)

Earlier endpoint metadata checks found existing model workloads, so candidate
inference was withheld. During this follow-up, a read-only availability request
to the configured local inference endpoint timed out; no inference request was
issued and no weights were downloaded. The existing suite covers simulated
stale/ambiguous navigation, dialog blocking/dismissal, semantic element
reacquisition, repeated observation, and terminal error reporting. These tests
validate deterministic helpers only; they are not a live replay benchmark and
do not demonstrate income.

No action-model adapter or replay harness was added: without a safe isolated
inference window, results would not justify the added dependency or measure
the proposed model. The next gate is a repeatable, isolated primary-model cycle
with recovery from a real runtime/RAM error. If an eligible local host is
available without disrupting production, then run a sequential A/B replay on
equivalent disposable profiles. Report task completion and money change as
well as action-level latency and error counts. Keep gameplay strategy and code
authorship exclusively with the primary LLM.

## Isolated primary-model follow-up (2026-11-05)

This was a primary-only tool/recovery evaluation, not a tiny-model A/B. Six
bounded runs used `gemma4:e4b` (Q4_K_M), fresh copies of the same version 3.0.1
seed, and the same money-generation objective. Inference was sequential on
local hardware. Results remained below the income acceptance gate:

| Run | Steps / inference time | Observed outcome |
|---|---|---|
| 04 | 3 / 75.3s | Repeated missing-file reads returned the bridge's opaque HTTP 500 twice; no script. |
| 05 | 5 / 163.7s | Repeated the same missing-file read four times despite clarified not-found feedback; operator stopped. |
| 06 | 5 / 223.9s | Dismissed the offline popup and ran `ls`, then made two malformed reference queries and guessed another missing filename; operator stopped. |
| 07 | 4 / 139.6s | Repeated an identical missing-file read; the unproductive-action guard stopped the session. |
| 08 | 9 / 378.5s | Authored code and corrected an entry-point error, then repeated a blocked run without checking diagnostics; no verified run. |
| 09 | 10 / 414.3s | Authored and deployed code, but Bitburner still showed `RUNTIME ERROR: ... does not have a main function`. The model did not repair it or verify money. |

Run 09 processed 47,070 prompt tokens and 2,841 output tokens. Its visible
Terminal briefly showed a PID, but the game displayed a runtime-error dialog;
the PID was not accepted as successful execution. No final HUD comparison or
positive income was recorded. The isolated model reported 3.745 GB in VRAM;
GPU utilization varied during inference. The private trial logs contain the
per-call metrics and observable evidence.

The seed's visible `ls` output had no `.js` files. Guidance now says not to
invent a filename when none is listed. Reference lookups accept
signature-shaped queries such as `ns.sleep(number)`. A verified changed script
deployment clears the consecutive-Terminal-command guard, and a visible game
runtime-error dialog is dismissed once before the next Terminal action while
its text is retained. The 86-test suite passes. These safeguards reduced
unproductive repetitions in some traces, but did not produce a working
money-making script. The primary gameplay gate remains unmet, so do not
integrate or production-test a learned action model yet.
