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
| Existing Browser Use + restricted Remote API | Isolated Remote API Online; harmless write/read/RAM round trip verified | Historical runs plus one new bounded Qwen run | Model-authored `hack.js` deployed and started; no balance or hacking change; $0.000/sec observed | 12 requests: 8 completions, 4 empty provider errors; 67.3k prompt / 6.4k completion tokens; 13m44s; about 23.3 GB VRAM resident; GPU utilization unavailable | Diagnose provider failures and script runtime behavior before another trial |
| Agent Zero | Isolated current upstream container starts; 5 MCP tools discovered; no inference endpoint or game attached | 0 | None | ~902 MiB idle / 5 GiB limit, 0.17% CPU; focused pytest unavailable in image; tool surface not yet behaviorally equivalent | Setup passed; prepare same-capability browser MCP adapter before inference A/B |
| Deterministic UI helpers + optional Laya/JEV | Offline trace inventory/replay completed; no model weights downloaded and no live test | 0 model-assisted | None | 265 Browser Use chunks reviewed; 78 indexed clicks across 11 sessions; 3 same-index repetitions, but no confirmed stale-index target in available snapshots; several traces had irrelevant “Add to Cart” objective | Retain deterministic helpers; Laya/JEV not justified by current traces |

### Initial parallel-work results (2026-11-05)

- **Inference:** initial checks to local Ollama returned HTTP 200 for
  `/api/version`, `/api/tags`, and `/api/ps`; `qwen3.6:35b` was present, loaded,
  and advertised vision/tool support. The subsequent bounded run did receive
  model completions, so generation worked, but 4 of 12 requests failed with
  empty `ModelProviderError`s. Do not treat a successful endpoint preflight as
  proof of reliable inference. No concurrent candidate inference was launched.
- **MCP audit:** the server-side allowlist is `getFile`, `pushFile`,
  `calculateRam`, and `getDefinitionFile`, with `health_check` in the MCP
  catalog. Save/state enumeration, deletion, bulk file routes, and public bridge
  ports are excluded. The two harnesses do **not** yet have behavioral parity:
  the baseline adds read-back, RAM, and run-before-redeploy safeguards that
  raw MCP calls lack, and error envelopes differ. Agent Zero must use equivalent
  wrapper safeguards and normalized errors before a comparable gameplay trial.
  Remote API and browser-tool unit tests passed: 46 tests in the offline
  deployment image. No live isolated bridge parity test has run yet.
- **Agent Zero setup:** current OSS commit `ba9b67df` starts in an isolated,
  login-protected container with default-block tool policy and no host mounts,
  Docker socket, model endpoint, or game profile. Its MCP client discovered
  the restricted bridge's five advertised tools, rejected an unadvertised
  save-file method, rejected an invalid token, and executed the health tool.
  The health result was `fetch failed` because no game API was attached. No
  inference was sent. The server-side Remote API allowlist is shared, but raw
  Agent Zero MCP does not yet match the baseline's visible observation/run
  tools, read-back and RAM checks, error envelopes, or run-before-redeploy
  guard. Do not compare gameplay until those capabilities are presented
  equivalently. Idle footprint was about 902 MiB; the upstream image occupies
  about 12.3 GB on disk. See the isolated report in ignored local records.
- **Laya/JEV replay:** Laya Browser 421M's model card states Apache-2.0 and
  describes browser action prediction (click/type/select), not gameplay
  planning or Netscript. The checkpoint is F16 and roughly 842 MB. The reviewed
  logs contain 265 Browser Use conversation chunks and 78 indexed clicks in 11
  sessions. Three sessions repeated an index, but available snapshots still
  contained that target, so stale-element failure was not demonstrated. Other
  failures included repeating an irrelevant “Add to Cart” goal on the game
  page, which target selection alone would not fix. No weights were downloaded
  and no inference/live test was run. A preliminary lexical shortlist loses
  the gold target in roughly 21–27% of reviewed target-selection cases, so
  adding that adapter now could reduce accuracy. Keep deterministic game UI
  helpers; reconsider only with better-labeled traces and a replay that proves
  improvement. Fast Browser Use is a separate browser framework/runtime and
  does not meet the minimal adapter goal.
- **Qwen recovery fix and trial:** the isolated branch captures visible
  runtime error text shortly after terminal script start and stores it in
  durable errors; the retry limit is configurable and defaults to two. The
  source passed all 92 tests in the offline deployment image. In a disposable
  profile, we dismissed the visible offline-earnings modal, set the Remote API
  port in the game's UI, confirmed **Online**, and completed a harmless
  `pushFile → getFile → calculateRam` round trip (`OK`, exact read-back,
  1.6 GB). A bounded Qwen3.6:35b run used 12 steps over 13m44s from session
  start to completion. It observed $1.262k and hacking 1, scanned, authored and
  deployed `hack.js`, and ran it with a PID. Its code attempted `ns.nuke(target)`
  to obtain root; the agent did not confirm a runtime error or repair the code.
  Afterward, visible balance remained $1.262k, hacking remained 1, Active
  Scripts showed $0.000/sec, and Recent Errors had no visible rows. The final
  checkpoint still called for inspecting output. Deployment and execution start
  passed; attributable income and autonomous debugging did not. No gameplay
  success is claimed.

  The run recorded 12 inference requests: 8 returned completions and 4 returned
  empty `ModelProviderError`s. Successful responses totalled 67,333 prompt and
  6,358 completion tokens, 333.3 seconds summed server duration (41.7 seconds
  average); first model load took 17.6 seconds. Ollama reported about 23.3 GB
  VRAM resident. Per-GPU utilization and CPU offload data were unavailable. The
  agent ended at step 12 of its 16-step cap after provider errors. The trial
  viewer used port 6180; port 6080 remained the preserved production spectator
  tunnel. Production was not modified.

  Follow-up inspection of the retained metrics identified all four provider
  failures as HTTP-client `ReadTimeout`s at 120 seconds. The benchmark had
  `LLM_TIMEOUT=180` while its ignored local config injected `OLLAMA_TIMEOUT=120`.
  The benchmark Compose file now explicitly sets `OLLAMA_TIMEOUT` from the
  separate `BENCH_OLLAMA_TIMEOUT` override (default 180), preventing that
  local-only value from silently truncating model requests. Compose resolution
  confirms `OLLAMA_TIMEOUT=180`, `LLM_TIMEOUT=180`, `STEP_TIMEOUT=210`; all 93
  tests pass. This is a measured harness correction, not yet a gameplay
  success. No repeat generation was launched because the shared endpoint's
  resident model had changed and its current use was unclear. The installed
  `qwen3.6:35b` tag was still available but unloaded. The timeout fix is
  published in `0b1db62` on `experiment/qwen-runtime-recovery`. Schedule the
  next isolated trial when the shared inference slot is clear, changing only
  this justified timeout variable.

- **Next Qwen trial staged without inference:** a fresh copy of the disposable
  seed now runs in its own Compose project and browser profile, with distinct
  loopback API/viewer ports so it does not displace the prior isolated viewer.
  The game reports Remote API Online; harmless write/read/RAM validation
  returned `OK`, exact read-back, and 1.6 GB. No gameplay session or model call
  has started. The benchmark runner accepts separate port and timeout settings;
  Compose resolved the staged run to 180/180/210-second request/LLM/step
  budgets. The latest runner/port change is published as `b5be825` on
  `experiment/qwen-runtime-recovery`. At the last read-only pool check,
  `qwen3:8b` was resident and `qwen3.6:35b` remained installed but unloaded, so
  the staged session is waiting for an unambiguous inference slot.
