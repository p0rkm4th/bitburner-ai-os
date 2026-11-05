# Bitburner core guide for the agent

Use this guide for orientation. The running game and live type definitions take
precedence over remembered or outdated API details.

## Observe before acting

- Read the visible game version, money, hacking level, current screen, dialogs,
  and Remote API status with `game_observe`.
- After scripts, use `game_progress` with prior money/level to verify balance,
  hacking, and income. On `NO_PROGRESS`, don't repeat `game_observe`; use
  progress or another action.
- Make one concrete, small objective. After an action, inspect its returned
  result and the changed UI before choosing the next action.
- A successful tool call, file upload, or RAM calculation does not prove the
  in-game action worked. Confirm it in the visible game.

## Servers and hacking

- `home` is the player's computer. It stores scripts and provides RAM; it is
  not a money target to hack.
- Use the game's Terminal `scan` or `scan-analyze` output to discover reachable
  servers and see root-access, required hacking level, required open ports, and
  available RAM.
- `scan` only lists directly connected hostnames and root status. Before choosing
  a hacking target or assuming a prerequisite, use the detailed scan view with
  a numeric depth and read its visible hacking-level, port, root, and RAM fields.
  A hostname-only scan does not establish that a server is hackable or ready to
  host scripts.
- `scan` takes no arguments. `scan-analyze` takes a positive numeric depth, for
  example `scan-analyze 2`; it does not take a hostname. Read the full visible
  error before correcting a command.
- Do not invent Terminal commands such as `serverinfo <host>`. Use a command
  shown by current Terminal help/documentation or inspect a relevant page via
  `game_open_tab`. If a command is rejected, stop and use its exact visible
  error to select another supported interface.
- Root/admin access and hacking skill are separate requirements. Port-opening
  programs followed by `NUKE.exe` grant root when the server's port requirement
  is met. `NUKE.exe` is already on `home`; zero-port servers need no opener.
  In Terminal, connect to the target and `run NUKE.exe`, or use documented
  `ns.nuke(host)`. Before using an API you are unsure about, retrieve its exact
  signature with `game_netscript_reference`. Root does not waive hacking-skill
  requirements. Inspect the server's displayed requirements before acting.
- After a root-access error, consult `game_troubleshoot` and verify uncertain
  APIs such as `ns.nuke` against the connected game's live reference before
  correcting a script. Verify visible root access and the result after a run.
- Root access is required to run scripts on a server. The script must also fit
  that server's available RAM.
- Terminal `run <file.js> [args...]` starts the file on the currently connected
  server; trailing values are script arguments, not a destination server. To
  execute on another host, copy the file with `scp <file.js> <host>` while on
  `home`, connect to that host, then run the file there.
## Money, security, and progression

- `hack` attempts to steal some of a target's available money and increases its
  security. Success chance, amount, and time depend on player skill and the
  target's state.
- `grow` increases target money and also raises security. `weaken` reduces
  security toward its minimum. These operations take time and must target a
  valid server with the required access.
- Use the current API reference for signatures, return values, and options.
  Observe the target and verify visible script output, active processes, money,
  and hacking level after execution.
- Bitburner also has non-hacking progression systems, including work, crimes,
  Hacknet, factions, augmentations, and BitNodes. Learn them through the game
  and official documentation; choose independently which objective to pursue.

## Netscript basics

- Netscript is JavaScript with game APIs. A runnable script exports an async
  `main(ns)` entry point. Use `await` for time-based Netscript operations and
  waits; a tight infinite loop can stall the game.
- Each API call has a RAM cost. Added APIs can raise script RAM requirements;
  the deployment tool asks the live game to calculate RAM before execution.
  Resolve unknown-function and RAM errors before repeating a run.
- Query `game_netscript_reference` for the exact signature and surrounding
  documentation from the connected game's definitions. Do not use removed
  helpers such as `nFormat`; check the live definitions for current alternatives.
- A Netscript `main(ns)` is different from a terminal command. Use
  `game_terminal` for commands and `game_run_script` to start a saved script.

## File and execution conventions

- The Remote API tools read and write simple `.js` filenames on `home` only.
  Do not add path prefixes to their filename arguments.
- `game_read_script` reads `.js` files only. For a text report written by a
  script, use `game_terminal` with the visible Terminal command `cat report.txt`;
  inspect the returned text instead of retrying the script-only Remote API.
- In the visible Terminal, use `ls` to inspect files, `mem <file.js>` to inspect
  RAM, `run <file.js>` to start a script, `ps` to inspect running processes, and
  `tail <file.js>` to inspect script output. Confirm exact syntax with the
  in-game `help` command or official docs if a command behaves differently.
- Use `game_open_tab` for an allowlisted visible game page and `game_terminal`
  for one supported Terminal command. Terminal `help` documents commands and
  programs, not Netscript APIs. A rejected help topic is evidence to use an
  official Documentation page, not to repeat variants of the same query.
- Use the visible Terminal to run scripts. Then inspect the run confirmation,
  `tail` output, Active Scripts, and updated game stats. Stop a failed process
  before replacing it if it is still running.
