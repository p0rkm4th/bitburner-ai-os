# Optional UI action model evaluation

## Decision

Do not add a learned UI action model to the running agent yet. The candidate
models have not been tested against the Bitburner DOM, the shared inference
endpoint currently has a model loaded, and the primary model has not yet
completed a verified money-making Netscript cycle. Production gameplay and its
profile were not changed. The optional model adapter remains unimplemented.

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
| Laya Browser Mind2Web, 421M | Apache-2.0 model; the training dataset is CC-BY-4.0. It predicts a typed action and target from a goal plus DOM candidates; it does not generate text. Its documented serving path expects Laya's typed-question format and its matching formatter/shortlister. | F16, 0.4B parameters. The checkpoint was trained on two T4 GPUs; that is training information, not a minimum inference requirement. It is not an Ollama model. The project has not been installed or run here because the only eligible local inference environment was unavailable for a safe isolated test and model inference is prohibited on the x1 host. | Small enough to be plausible, but not a drop-in Browser Use action head. Its Mind2Web task success is 4.0% cross-task, 2.3% cross-website, and 2.6% cross-domain; its author explicitly says live-page behavior is untested and labels the checkpoint a research/hobby project. Do not deploy without a Bitburner replay benchmark. |
| Fast Browser Use | MIT-licensed standalone local browser-use engine, not a tiny action model or adapter for the current shared Browser Use session. | Requires Python 3.12+, Playwright >=1.58, and uses Qwen3.5-9B or Qwen3.5-35B-A3B with PyTorch on Linux/NVIDIA. The current browser image pins Playwright 1.56. The repository recommends 24GB VRAM for 9B BF16; the available cards are 8GB each. Its own benchmarks use an RTX PRO 6000 96GB. | Not compatible with the current image and resource envelope as documented; introduces another browser runtime and a much larger model. Do not integrate for this task. |

Sources: [Laya Browser model card](https://huggingface.co/Quantum08/laya-browser-mind2web),
[Fast Browser Use repository](https://github.com/APUS-AI-Lab/fast-browser-use), and
[Fast Browser Use dependency manifest](https://github.com/APUS-AI-Lab/fast-browser-use/blob/main/pyproject.toml).
These are upstream claims and requirements, not local performance measurements.

## Benchmark status

No head-to-head trial was run. Laya weights were not downloaded, and neither
candidate was allowed to access an isolated game profile. A read-only check
found an existing model loaded on the shared local Ollama endpoint, so another
inference workload was withheld to avoid contention. Access to a separate
eligible model host was not available for this isolated run. Fast Browser Use
was excluded from execution because its documented model and dependencies do
not fit the current resource/runtime profile without changing the architecture.

The required replay comparison for repeated clicks, stale indexes, blocked
dialogs, and failed navigation therefore remains outstanding. Existing
deterministic helper tests and the live disposable-profile check are positive
functional checks, but do not establish that a model-assisted path reduces
invalid actions, elapsed task time, or end-to-end gameplay time. No evidence
currently supports the extra model complexity.

Before reconsidering integration, first demonstrate a repeatable, isolated
primary-model cycle that independently authors, deploys, runs, debugs, and
verifies income. Then replay the same recorded UI cases against the existing
semantic helpers and an optional Laya adapter, with inference workloads
sequential and production excluded. Compare task success and actual money
progress as well as latency and invalid/repeated actions. Keep the primary LLM
as the sole owner of gameplay strategy and code authorship.
