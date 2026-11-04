# Hardened Bitburner MCP Remote API bridge

This image reuses upstream `JoshuaGreeff/bitburner-mcp-server` at commit
`0229e9b93ea1ffc2a1e570561fc5102c6d19e29b` and applies the checked-in
`hardening.patch`. Its lockfile is refreshed to fixed compatible dependencies.
The bridge stays inside the agent container's network namespace; no ports are
published. It listens on loopback, requires a bearer token, and requires
Bitburner to connect to `localhost:12525` with WSS disabled. The HTTPS game
blocks plain `ws://` to non-loopback hosts, which is why the shared namespace is
required.

The server-side Remote API allowlist is exactly:

- `getFile` for a simple `.js` filename on `home`;
- `pushFile` for 1–30,000 characters of a `.js` file on `home`;
- `calculateRam` for a simple `.js` filename on `home`;
- `getDefinitionFile` for official read-only type definitions.

Save reads, server enumeration, file deletion, bulk file operations, and
convenience file routes are unavailable or return an error at the bridge.
Request logs do not include script contents. Do not enable the separate
Streamable HTTP server; if started manually, it now requires bearer auth too.

The upstream project has no automated tests. Image build compiles it and runs
`npm audit --omit=dev`. The integration test suite exercises the Browser Use
adapter separately, and the operator guide records live isolated-profile
results.
