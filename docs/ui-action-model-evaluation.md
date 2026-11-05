# Optional UI action model evaluation

## Decision

Do not add a learned UI action model to the running agent. The observed failures
are repeated Terminal commands, RAM/process diagnosis, queued game dialogs, and
long or malformed inference responses. The current gameplay tool set no longer
offers generic element-index clicks: it uses fresh semantic controls, visible
modal checks, and verified transitions. A second target selector would overlap
those safeguards, while the major failures (game strategy, RAM diagnosis, and
slow or unavailable primary inference) are outside a UI-action model's scope.
Neither candidate has been tested against the live Bitburner DOM; the optional
adapter remains unimplemented.

The current low-complexity path is the deterministic visible-UI helper set in
`app/game_tools.py`. It resolves fresh visible labels, rejects ambiguous or
missing targets, checks modal state, executes through the shared Browser Use
session, and verifies the rendered transition. Unit tests cover stale/ambiguous
targets, blocked dialogs, terminal results, and navigation. A live integration
check on a fresh disposable profile also passed: it observed the game and
opened the Create Program tab by its fresh semantic label. This check confirms
the existing helper path works; it is not a comparative model benchmark.

## Candidate review

| Candidate | License and scope | Runtime and compatibility | Assessment |
|---|---|---|---|
| Laya Browser Mind2Web, 421M | Apache-2.0 model; the training dataset is CC-BY-4.0. It predicts a typed action and target from DOM candidates; it does not generate text or use screenshots. Serving expects the Laya typed-question format plus its formatter and lexical shortlist. | F16, 0.4B parameters (about 0.8 GB raw weights before framework overhead). Not an Ollama model. No inference hardware minimum is published. It has not been installed or run here. | Small enough to be plausible for local inference, but not a drop-in Browser Use action head. The model card reports Mind2Web task success of 4.0% cross-task, 2.3% cross-website, and 2.6% cross-domain; it explicitly says live-page behavior is untested and calls this a research/hobby checkpoint. |
| Fast Browser Use | MIT-licensed standalone local browser-use engine, not a tiny action model or adapter for the current shared Browser Use session. | Requires Python 3.12+ and Playwright >=1.58. Its PyTorch path uses Qwen3.5-9B or Qwen3.5-35B-A3B; it documents 24 GB GPU memory for 9B BF16 and 80 GB for 35B-A3B BF16. The current browser image pins Playwright 1.56. Its README launches its own Playwright browser session. | Incompatible with the current runtime without dependency changes, and substantially larger than Laya. It adds another browser runtime instead of a small shared-session action head. |

Sources: [Laya Browser model card](https://huggingface.co/Quantum08/laya-browser-mind2web),
[Fast Browser Use repository](https://github.com/APUS-AI-Lab/fast-browser-use), and
[Fast Browser Use dependency manifest](https://github.com/APUS-AI-Lab/fast-browser-use/blob/main/pyproject.toml).
These are upstream claims and requirements, not local performance measurements.

## Comparison status

| Workflow | Evidence | Outcome |
|---|---|---|
| Primary model only | An earlier production trace showed a script and $3.764 of offline earnings, but the uncontrolled trace does not attribute that amount to a model-authored program. Controlled benchmark trials have not verified income. | No reproducible, isolated money-making cycle is established. Repeated run attempts exhausted RAM; calls timed out or failed to reach local inference. |
| Deterministic UI helpers | 73 automated tests pass, including fresh semantic target resolution, modal handling, terminal results, RAM recovery gating, and repeat-run protection. An earlier disposable-profile check opened a game tab by its semantic label. | Functional and low-cost; no controlled A/B replay and no measured end-to-end latency reduction. |
| Tiny model assisted | Laya weights were not loaded; Fast Browser Use was not installed. | No task-success, latency, resource, or income measurements. No evidence supports integration. |

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

## Isolated tiny-action-model follow-up (2026-11-05)

The current gameplay tool set already removes generic indexed clicks. Its
remaining browser actions resolve allowlisted visible labels, check for
blocking dialogs, and verify UI transitions. Historical logs do contain stale
index clicks and blocked-dialog loops, but current deterministic helper tests
cover fresh target resolution and one-shot dialog recovery. A controlled A/B
replay was not run: the configured local inference endpoint did not respond to
a read-only availability check. No weights were downloaded and no inference
was started.

Laya is a DOM-candidate action policy (`CLICK`, `TYPE`, or `SELECT`), not a
screenshot/vision model. It relies on a matching candidate formatter and
lexical shortlister; its model card reports that the shortlist misses the
correct element on about 21–27% of steps. Its reported Mind2Web task success is
low, and live-page behavior is explicitly untested. [Model card](https://huggingface.co/Quantum08/laya-browser-mind2web)
and [reference formatter](https://github.com/HiteshS08/laya-system-use/blob/main/jev_ultrafast/formatter.py).

Fast Browser Use does not fit the tiny-model/shared-browser proposal. It is MIT
licensed but launches its own browser and uses Qwen3.5-9B or 35B-A3B through
PyTorch/MLX. The documented Playwright minimum is newer than this deployment's
pin, and its hardware requirements are much higher than Laya's. [README](https://github.com/APUS-AI-Lab/fast-browser-use)
and [dependency manifest](https://github.com/APUS-AI-Lab/fast-browser-use/blob/main/pyproject.toml).

**Recommendation:** Keep deterministic UI helpers and do not integrate either
candidate. No measured A/B task-success or latency improvement exists, and the
primary-model acceptance gate remains open. Reconsider Laya only after an
isolated money-making Netscript cycle succeeds and a local inference window is
available for sequential replay on equivalent disposable profiles. Fast
Browser Use is not recommended for this architecture.
