# Agent Zero isolated evaluation

## Setup check

The current open-source Agent Zero image was launched in a disposable project
with an internal-only Docker network and a sidecar built from the same
restricted Bitburner bridge source used by the Browser Use harness. No game,
production profile, Ollama endpoint, or inference request was connected.

Agent Zero's own MCP client initialized the bridge and listed exactly five
tools: `health_check`, `pushFile`, `getFile`, `calculateRam`, and
`getDefinitionFile`. A `health_check` returned the expected no-game-connected
diagnostic. The bridge rejected save-file access as an unknown tool and blocked
a traversal-style write request. Agent Zero's app returned HTTP 200 when
checked from inside its container.

The app UI was not reachable from the host while attached only to the
internal-only network with the rootless Docker daemon. The test did not weaken
network isolation to publish it. The three disposable experiment containers
and their network were removed after the checks; ignored result and smoke-test
artifacts remain under `local/agent-zero-exp-b32/` for reproducibility.

## Comparison status

This is setup and MCP discovery evidence, not a gameplay result. Although both
harnesses reach the same bridge allowlist, raw MCP currently exposes lower-level
operations. It does not enforce Browser Use's read-back verification, RAM
calculation, visible-run gate, or progress checks. It also does not provide the
same Browser Use session and spectator view. Do not treat the present tool
surfaces as equivalent for an A/B gameplay comparison.

Before a comparable local-model trial, provide Agent Zero only equivalent
high-level wrappers and a constrained browser session, without expanding its
game or host permissions. Use the same model, clean isolated game seed,
instructions, inference parameters, and time/action budget. Measure actual
visible income and error recovery. No Agent Zero gameplay trial has been run.
