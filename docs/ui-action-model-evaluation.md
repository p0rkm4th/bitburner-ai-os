# Optional UI action model evaluation

## Decision

Do not add a learned UI action model to the running agent. The production save
has previously shown script earnings, but that run was uncontrolled and does
not meet the reproducible isolated acceptance gate. The latest isolated runs
still fail on repeated/malformed tool calls and broken Netscript. No evidence
shows that a second model would fix those failures. Neither candidate has been
run against the Bitburner DOM; the optional adapter remains unimplemented.

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
| Laya Browser Mind2Web, 421M | Apache-2.0 model; the training dataset is CC-BY-4.0. It predicts a typed action and target from DOM candidates; it does not use screenshots or generate text. A separate local LLM must fill text values. Its serving path expects Laya's typed-question format and matching formatter/lexical shortlister. | F16, 0.4B parameters. The checkpoint was trained on two T4 GPUs; that is training information, not a minimum inference requirement. It is not an Ollama model. It was not installed or run because the primary gameplay gate remains unmet; a candidate-specific A/B trial would add inference/adapter work without validating income. | Small enough to be plausible, but not a drop-in Browser Use action head. Its lexical shortlister excludes the correct element on about 21–27% of benchmark steps; its Mind2Web task success is 4.0% cross-task, 2.3% cross-website, and 2.6% cross-domain. The author explicitly says live-page behavior is untested and labels the checkpoint research/hobby. Do not deploy without a Bitburner replay benchmark. |
| Fast Browser Use | MIT-licensed standalone local browser-use engine, not a tiny action model or adapter for the current shared Browser Use session. | Requires Python 3.12+, Playwright >=1.58, and uses Qwen3.5-9B or Qwen3.5-35B-A3B with PyTorch on Linux/NVIDIA. The current browser image pins Playwright 1.56. The repository recommends 24GB VRAM for 9B BF16; the available cards are 8GB each. Its own benchmarks use an RTX PRO 6000 96GB. | Not compatible with the current image and resource envelope as documented; introduces another browser runtime and a much larger model. Do not integrate for this task. |

Sources: [Laya Browser model card](https://huggingface.co/Quantum08/laya-browser-mind2web),
[Fast Browser Use repository](https://github.com/APUS-AI-Lab/fast-browser-use), and
[Fast Browser Use dependency manifest](https://github.com/APUS-AI-Lab/fast-browser-use/blob/main/pyproject.toml).
These are upstream claims and requirements, not local performance measurements.

## Comparison status

| Workflow | Evidence | Outcome |
|---|---|---|
| Primary model only | Production trace: Qwen authored and visibly ran a Netscript loop. The game reported $3.764 of offline script earnings; HUD later showed $25.516k and Hacking 17. The trace was not isolated or controlled. | Real income and progress, but repeated run attempts exhausted home RAM; the agent has not reliably diagnosed or cleaned up active processes. Calls timed out at 150 seconds. |
| Deterministic UI helpers | 86 automated tests pass. A disposable-profile integration check handled a dialog, opened a semantic tab, and returned actual `ls` output. | Functional and low-cost; no controlled A/B replay and no measured end-to-end latency reduction. |
| Tiny model assisted | Neither Laya weights nor Fast Browser Use were installed or run. | No action-model task-success, latency, resource, or income measurements. No evidence supports integration. |

The production trace is not a model benchmark: its profile and starting state
were not controlled against an identical baseline, and the tiny model was not
run. The primary-model gameplay acceptance gate remains open.

## Benchmark status

No head-to-head trial was run. Laya weights were not downloaded, and neither
candidate accessed an isolated game profile. A read-only availability check
found the configured local Ollama endpoint unreachable; no inference request
was issued. The production agent had stopped after Ollama connection failures,
and its profile and service were left untouched. Fast Browser Use was excluded
because its documented model and dependencies do not fit the current browser
runtime without changing the architecture.

The required replay comparison for repeated clicks, stale indexes, blocked
dialogs, and failed navigation remains outstanding. Existing deterministic
helper tests and the live disposable-profile check are positive functional
checks, but do not establish that a model-assisted path reduces invalid
actions, elapsed task time, or end-to-end gameplay time. No evidence currently
supports the extra model complexity.

Before reconsidering integration, first demonstrate a repeatable, isolated
primary-model cycle that independently authors, deploys, runs, debugs, and
verifies income. Then replay the same recorded UI cases against the existing
semantic helpers and an optional Laya adapter, with inference workloads
sequential and production excluded. Compare task success and actual money
progress as well as latency and invalid/repeated actions. Keep the primary LLM
as the sole owner of gameplay strategy and code authorship.

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
