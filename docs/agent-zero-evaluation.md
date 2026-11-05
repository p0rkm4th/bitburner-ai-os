# Agent Zero integration experiment

This is an isolated compatibility experiment. It does not replace the Browser
Use harness and has not been used to control the production game.

## Architecture under test

The existing FastAPI service owns one persistent Chromium session. In the
Agent Zero benchmark profile, `AGENT_ZERO_MCP_ENABLED=1` disables the
Browser Use supervisor and exposes a bearer-authenticated adapter for the
existing allowlisted `game_*` tools. The Node MCP sidecar advertises those
tools only, forwards requests to the adapter, and disables raw Remote API
operations. Save access, arbitrary code execution, host shell access, browser
evaluation, and unrestricted file operations are not part of this interface.

The adapter rejects calls while the Browser Use controller owns the session,
validates tool arguments against the existing action schemas, and serializes
calls through one lock. The sidecar shares the browser container's network
namespace. Its MCP listener is not published on the host and is reachable only
over an internal experiment network. The distinct Agent Zero token is stored
in ignored local configuration.

## Current evidence

- The app and sidecar images build; the existing MCP Node dependencies pass
  `npm audit --omit=dev` with zero reported vulnerabilities.
- The application test suite passed: 99 tests. The Agent Zero adapter tests
  passed: 6 tests.
- Agent Zero's own MCP client connected to the sidecar and discovered 12
  allowlisted `game_*` tools. Calls to `game_observe` and
  `game_terminal(command="help")` through Agent Zero's `MCPConfig.call_tool`
  returned visible UI text and terminal help with no tool errors. The
  observation contained 2,821 characters. An attempted raw save API operation
  was denied by the server.
- The sidecar reached the isolated browser app. An unauthenticated request was
  rejected with HTTP 401. Authenticated MCP calls to observe the game, retrieve
  guide/reference text, open the Stats tab, and run harmless visible `ls` and
  `help` terminal commands succeeded.
- These checks used the cloned benchmark seed. The visible `$1.262k` and
  hacking level 100 were inherited seed values, not progress made by Agent
  Zero or a gameplay model. No gameplay inference trial has run.
- Agent Zero's MCP settings API was attempted using its authenticated WebUI
  API. It failed before saving configuration because `chpasswd` returned a
  nonzero exit status. The isolated test was configured through Agent Zero's
  persistent settings file and restarted; its own MCP client then connected
  and executed a read-only observation. This is specific to the disposable
  Agent Zero experiment and does not change the production deployment.
- A read-only request to the configured Ollama `/api/tags` endpoint from
  Agent Zero failed to connect because its Docker network is internal-only.
  No Ollama endpoint is configured in Agent Zero and no inference request was
  made. Keep this network boundary until a least-privilege path to local Ollama
  is established.

## Current conclusion

Tool parity looks feasible without another game-control framework: Agent Zero
can be given the same existing `game_*` tool surface, while mutual exclusion
prevents concurrent controllers. Setup and MCP discovery/read-only execution
are verified; Agent Zero's authenticated settings API has a `chpasswd`
blocker, while the persistent settings configuration works. Ollama
connectivity, error recovery, context handling, autonomous continuation,
and gameplay progress are not yet demonstrated. Do not treat the inherited money visible
in the viewer as an Agent Zero result.

The next comparison should use an isolated disposable profile and matching
local model, seed, step/time limits, and tool permissions. Record tool calls,
tokens, elapsed time, failure recovery, and verified game-state deltas. Keep
inference sequential with other workloads that use the same Ollama slot.
