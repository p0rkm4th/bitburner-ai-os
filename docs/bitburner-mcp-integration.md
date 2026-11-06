# Bitburner Remote API / MCP integration

## Version-aware learning reference

The game version must come from the visible game UI when a session starts. Do not
assume the deployed game follows the repository's `dev` branch. The current
official release notes list Bitburner 3.0.1; the Remote API's
`getDefinitionFile` returns definitions from the running game, so queried
signatures should be treated as authoritative for that session. `game_netscript_reference`
returns only a small excerpt for one requested symbol instead of loading all
type definitions into the agent's context.

The intended learning loop is: inspect the UI and existing script, consult the
relevant in-game documentation or one type-definition symbol, author code from
the observed problem, deploy and verify the exact text, run it through the
visible terminal, then inspect its visible result and debug from that evidence.
This guide does not prescribe a gameplay strategy or supply a ready-made script.

Official references:

- [In-game documentation and current definitions](https://github.com/bitburner-official/bitburner-src)
- [Remote API protocol](https://github.com/bitburner-official/bitburner-src/blob/dev/src/Documentation/doc/en/programming/remote_api.md)
- [Official release notes](https://github.com/bitburner-official/bitburner-src/releases)

## Supported integration surface

The optional Browser Use tools call the existing MCP server's authenticated
REST facade. Their fixed game-facing surface is:

- `game_read_script`: read one simple `.js` filename from `home`.
- `game_deploy_script`: write model-authored code to one simple `.js` filename
  on `home`, read it back, and ask the game to calculate its RAM cost.
- `game_netscript_reference`: accept a bare symbol such as `grow` or a
  namespaced symbol such as `ns.grow`, then return its exact signature and
  nearby official documentation from the running game's type definitions.

The Browser Use session remains responsible for gameplay, observations,
visible script execution, and spectator output. These tools do not call save
APIs, enumerate servers, delete files, read arbitrary game-state values, or
execute code. The bridge is opt-in via `BITBURNER_REMOTE_API_URL` and
`BITBURNER_REMOTE_API_TOKEN`; do not publish its token.
When the bridge is configured, the browser editor helpers are omitted from the
model's tool list so script authoring uses this verified API path. Visible
terminal execution, browser observations, and spectator access remain enabled.

Bitburner's official Remote API documents `pushFile`, `getFile`,
`calculateRam`, and `getDefinitionFile`. It also documents `getSaveFile`,
`getAllServers`, `deleteFile`, and bulk file reads. Those broader calls must not
be exposed to the gameplay agent.

## Upstream MCP server audit

Audited upstream commit: `0229e9b93ea1ffc2a1e570561fc5102c6d19e29b`
(2026-02-16). It builds with Node 20+ and TypeScript; the implementation is a
WebSocket Remote API listener, Express REST facade, MCP stdio/Streamable HTTP
servers, and a dashboard. It contains no automated tests.

Security and compatibility findings:

- Its initial lockfile audit reported 14 production dependency advisories (10
  high, 3 moderate, 1 critical). `npm audit fix` in the isolated checkout
  updated compatible dependencies; build then passed and the production audit
  reported zero advisories. This is not an upstream release.
- Defaults bind the Bitburner WebSocket listener to `0.0.0.0`; the REST facade
  also listens on all interfaces, has wildcard CORS, and makes bearer auth
  optional. Streamable HTTP has no authentication. Keep these listeners inside
  a private container network, require a token, and do not publish ports.
- The unfiltered MCP tool list includes save-file reads, bulk file access,
  deletion, and server enumeration. REST adds broad file upload/append/delete
  operations. Do not pass the full upstream tool catalog to the player.
- A new Bitburner WebSocket client replaces the prior client, so an exposed
  listener allows connection hijacking/denial. Dashboard events include
  request data, and the bridge logs calls. Treat it as trusted local plumbing,
  not a hardened public service.
- The repository's Remote API method catalog is stale versus the current
  official specification (which also documents file metadata methods). The
  adapter therefore allowlists exact calls and does not mirror every upstream
  method.

## Test boundaries and current evidence

Initial Remote API testing must use a separate Chromium profile and separate
test save. The shared persistent profile is also test-game state, but its
progress must be preserved during isolated experiments. A
successful `pushFile`/`getFile`/`calculateRam` result only validates file
transport and syntax/RAM calculation; the agent must still run the program in
the visible in-game terminal and verify actual behavior before calling a
gameplay cycle successful.

The hardened bridge image also passed a disposable no-network security smoke
test: unauthenticated REST health and MCP requests returned 401; authenticated
REST health returned 200 and reported no game connected; traversal and
non-home script targets were rejected; save/delete methods were absent; and
convenience file routes were disabled. Authenticated MCP initialization and
tool discovery exposed only `health_check`, `pushFile`, `getFile`,
`calculateRam`, and `getDefinitionFile`; a forbidden save-read tool call was
rejected. A permitted write request correctly reported that no game was
connected. This confirms the bridge boundary and MCP catalog, but does not
replace an isolated live-game Remote API round trip.

The REST-facing Browser Use adapter additionally enforces a one-deployment
visible-run gate and exact read-back/RAM checks. The raw upstream MCP tools do
not enforce that workflow sequence. Do not expose raw MCP tools directly to a
gameplay model; an MCP consumer must use an equivalent constrained wrapper.

Agent Zero comparison: its current docs describe native MCP server setup,
project-scoped instructions/files/memory/secrets, and loadable skills. Those
could organize a Bitburner guide and project instructions, but they do not
resolve the current Browser Use interaction failures or add a safer Remote API
surface by themselves. Do not migrate for this task. If a separate comparison
is useful later, run an isolated A/B with the same model, profile snapshot,
short task, tool allowlist, and success criteria; compare completed actions,
timeouts, script correctness, and visible game confirmation.
