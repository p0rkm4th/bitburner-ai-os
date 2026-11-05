# Parallel autonomous gameplay experiments

## Objective

Maximize **verified Bitburner gameplay progress per wall-clock hour** while
keeping production saves untouched and preserving a fair comparison. A setup
that starts a container, discovers tools, or writes a script is not gameplay
progress. Count progress only when the isolated game visibly confirms an
in-game result; for the primary acceptance test, a model-authored script must
run and produce attributable money.

This plan uses the public repository's current `main` and
`experiment/tiny-ui-action-model` evidence. The existing reports show that
script authoring and deployment sometimes succeed, but repeated isolated Qwen,
Gemma, and Devstral runs did not consistently complete an income cycle.
Observed blockers include outdated Netscript APIs, missing `main`, invalid
targets or permissions, RAM failures, unhandled runtime dialogs, repeated
deployments without execution, and intermittent inference/network failures.
Historical offline earnings on the preserved production save are not counted
as a new trial result unless a test records a starting balance, run evidence,
and the corresponding increase.

## Workstreams and ownership

| Stream | Work | Allowed while inference is reserved? | Success evidence |
|---|---|---:|---|
| A — Existing harness | Inspect error traces; repair bounded runtime-error recovery; run a bounded Qwen3.6:35b income trial against an isolated seed | Trace analysis, code, and tests: yes. Model trial: only in the inference slot | Visible successful execution plus a balance increase attributable to that run; record model steps, tool calls, elapsed time, errors, and tokens |
| B — Agent Zero | Isolated setup, security/dependency review, Ollama compatibility, MCP discovery and non-inference tool tests; later compare autonomy and recovery | Setup and non-inference tests: yes. Model trial: inference slot only | Same restricted tools, game seed, objective, model, budgets, and observable acceptance test as A |
| C — Laya / JEV | Offline replay of recorded DOM/action traces; compare target selection with existing deterministic helpers; disposable live test only if replay shows a benefit | Yes when CPU/memory allow; do not use shared GPU inference during the reserved slot | Better action correctness or total task completion with measured latency/resource cost; otherwise do not integrate |
| D — MCP parity | Audit/tests for equivalent restricted capabilities, normalized failures, and observable results across harnesses | Yes against isolated bridge/game instances | Same allowlist and denial behavior; test results available to both harnesses; no save/state/deletion access |

Each implementation experiment uses its own branch/worktree, container,
profile, and artifact directory. Agents may inspect committed material in
parallel, but no two trials may mutate the same game profile. Never test on
the production profile or production services.

## Concurrency and resource schedule

Run independent work immediately in parallel: setup and security review for B,
offline trace replay for C, and D's audit/unit tests. A can analyze existing
logs, make harness fixes, and run non-inference tests concurrently. Do not hold
the entire project behind a model-loading or inference wait.

Use one shared **heavy-inference slot** for gameplay generation. Before each
trial, check that the selected Ollama endpoint responds, the exact model is
available, and no other workload owns the serving slot. Run only one gameplay
trial at a time across the shared inference pool. Capture model loading and
inference metrics, then release the slot. If availability is uncertain, record
the blocker and continue non-inference work; do not switch to an unapproved
model/node or send overlapping requests. Laya replay may use CPU when it does
not materially compete with the browser host; any weight loading or live UI
action inference gets a separate resource check.

Do not start Agent Zero or a Laya live-game test merely because setup passed.
First validate that it uses the same isolated game capabilities and cannot
reach host shell, save files, private game state, or unallowlisted bridge
methods. For inference comparisons, serialize runs and clone the same clean
seed before each run.

## Trial controls and measurements

Record for every attempted run, including incomplete or failed runs:

- source commit, harness version, exact model tag, host class (public reports
  must not disclose private node/address details), model context and inference
  parameters;
- clean seed/profile identifier kept only in ignored local records, game
  version, objective, tool allowlist, step/session/time/token limits;
- initial and final visible money, hacking level, root/permission state where
  visible, script name, deployment read-back, visible execution output, and
  income attributable to the run;
- every tool call, invalid/failed call, repeated action, runtime error, recovery
  attempt, and terminal outcome;
- wall time to first working script and first attributable income; inference
  latency and token counts; model-load overhead; GPU allocation/use, CPU
  offload, throughput, and browser/agent RAM where available;
- setup time separately from gameplay time. Do not report setup completion as
  a gameplay win.

Primary metric is verified gameplay progress per wall-clock hour. Rank runs by
successful autonomous gameplay and recovery first, then useful progress/minute,
tool reliability, and resource cost. Report means/medians only when at least
three equivalent trials exist; retain per-trial failures and do not exclude
timeouts or setup failures caused by the candidate harness. Report
infrastructure outages separately from model failures, with evidence.

## Decision gates

1. **Capability parity gate:** D confirms both harnesses receive only the
   documented allowlist, the same official reference content, equivalent
   normalized errors, and visible results. Block comparative inference if this
   fails.
2. **Offline UI gate:** C replays representative stale-index, repeated-click,
   dialog, and navigation traces against deterministic helpers. If the action
   model does not improve correctness or end-to-end task time enough to justify
   runtime complexity, stop before a live test.
3. **Agent Zero setup gate:** B passes isolated startup, local Ollama
   configuration inspection, restricted MCP discovery/call tests, and checks
   that OS/game permissions match the baseline. Only then schedule inference.
4. **Gameplay gate:** A first repairs a reproduced error-recovery defect and
   passes relevant non-inference tests. Then run bounded Qwen3.6:35b sessions
   against a fresh isolated seed until verified attributable income, terminal
   failure, or a justified stop condition. Preserve all evidence and do not
   count a PID, deployment, offline earning, or unverified claim as success.
5. **Comparable trial gate:** Once B or C is ready and the inference slot is
   available, run the same model, seed snapshot, objective, tools, context,
   and budget for the baseline and candidate. Change only one justified
   variable between retries. Merge improvements only after regression tests.

## Current comparison record

Update this compact table after each independent milestone. Link detailed
public-safe evidence in `docs/model-benchmark.md`,
`docs/ui-action-model-evaluation.md`, and `docs/validation.md`; keep topology,
credentials, and game profiles in ignored local records.

| Approach | Setup/non-inference | Gameplay trials | Verified progress | Errors / inference / resources | Decision |
|---|---|---:|---|---|---|
| Existing Browser Use + restricted Remote API | Existing deployment and isolated benchmark runner; current inference route must be preflighted | Historical runs documented; new run pending | Historical trials include successful script starts and old/offline earnings, but no current bounded trial with attributable income | Runtime errors, stale/incomplete recovery, skipped execution, and network failures appear in committed and ignored evidence | Continue A; repair recovery and measure one clean attributable cycle |
| Agent Zero | Pending isolated setup and non-inference MCP checks | 0 | None | Not yet measured under equivalent controls | Do not choose until parity gate and comparable gameplay trial pass |
| Deterministic UI helpers + optional Laya/JEV | Existing deterministic helpers have disposable integration evidence; offline replay pending | 0 model-assisted | None | No action-model latency, memory, or accuracy data yet | Keep deterministic helpers; add action model only if replay proves measurable benefit |

### Initial parallel-work results (2026-11-05)

- **Inference preflight:** workstation checks to the configured local Ollama
  API returned HTTP 200 for `/api/version`, `/api/tags`, and `/api/ps`; the
  baseline `qwen3.6:35b` tag is present and reported loaded. No generation was
  sent, so the endpoint's ability to complete a request after the Ollama/Herd
  changes is still unverified. A loaded model is treated as a shared resource;
  gameplay inference waits for a clear slot.
- **MCP audit:** the server-side allowlist is `getFile`, `pushFile`,
  `calculateRam`, and `getDefinitionFile`, with `health_check` in the MCP
  catalog. Save/state enumeration, deletion, bulk file routes, and public bridge
  ports are excluded. The two harnesses do **not** yet have behavioral parity:
  the baseline adds read-back, RAM, and run-before-redeploy safeguards that
  raw MCP calls lack, and error envelopes differ. Agent Zero must use equivalent
  wrapper safeguards and normalized errors before a comparable gameplay trial.
  Remote API and browser-tool unit tests passed: 46 tests in the offline
  deployment image. No live isolated bridge parity test has run yet.
- **Agent Zero setup:** pending. Its environment and non-inference tests are
  delegated to an isolated experiment; no inference or production access has
  occurred.
- **Laya replay:** pending. No weights or extra inference workload have been
  started; trace inventory and CPU replay are underway separately.
