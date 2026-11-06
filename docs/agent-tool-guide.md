# Bitburner agent tools

Use the game-specific tools first. They share one Browser Use session; they do
not run concurrently. Check each returned result before acting again.

| Tool | Input | Intended use and result |
|---|---|---|
| `game_observe` | none | Read a compact rendered UI snapshot and detect a visible dialog. Read-only. |
| `game_progress` | optional `baseline_money`, `baseline_hacking_level` | Read visible money, hacking level, and script income from rendered UI text. It compares against the balance captured immediately before the latest confirmed script run, falling back to the session's first visible balance, handles Bitburner's multiline HUD layout, and reports the balance delta. If supplying a baseline, copy the complete visible value exactly (for example, `$1.262k`); omit it if uncertain. A malformed baseline returns an actionable error alongside the current visible stats. If a stat is not rendered, use the visible `Stats` or `Active Scripts` tab and observe again. Use after running a script and after `game_observe` returns `NO_PROGRESS`; it neither changes the game nor clears the duplicate-observation guard. |
| `game_help` | `topic` | Retrieve one allowlisted section of this repository's concise gameplay/tool documentation. It cannot read arbitrary files. |
| `game_troubleshoot` | `error` | Retrieve matching recovery notes for a visible game/tool error. |
| `game_dismiss_dialog` | none | Dismiss one currently visible dialog using its semantic close control, a unique visible button within the modal, or Escape; then verify it is gone. If no dialog is visible, it returns `NO_PROGRESS` without sending input. Do not call it again unless a new dialog is visible. |
| `game_open_tab` | exact visible `tab` label | Open Terminal, Script Editor, Active Scripts, Create Program, Stats, Hacknet, City, Travel, Milestones, or Documentation by freshly matching its visible label; its tool schema enumerates those exact labels, and invalid values send no browser input. It never accepts element indexes or arbitrary selectors. |
| `game_tutorial` | `action`: `next` or `exit` | When the tutorial is visibly open, click exactly one freshly observed `Next` or `Exit Tutorial` button and verify the transition. The model chooses whether to learn another page or exit; the tool does not skip automatically. Repeated clicks on an unchanged page are blocked. |
| `game_terminal` | one-line `command` | Opens the in-game Terminal with its documented shortcut if needed and returns the visible result. Recognized offline-progress, message, and runtime-error dialogs are dismissed once; that call does not send the command and returns the dialog text. Unknown dialogs block the action. If the tutorial rejects a command, it returns `BLOCKED` and confirms the command was not executed; choose `game_tutorial` explicitly. An identical repeat of the last Terminal command and `connect` to the already visible current host return `NO_PROGRESS` without sending input. A verified changed script deployment permits a new run attempt. |
| `game_read_script` | simple `filename` | Read one `.js` file from `home` through the restricted official Remote API. No path prefixes. Only read a filename shown by visible Terminal `ls`. If no `.js` is listed or the file is absent, do not guess/repeat a read; author a new script independently. |
| `game_deploy_script` | `filename`, model-authored `content` | Write one `.js` file on `home`, read it back, compare exact contents, and ask the live game for RAM cost. After a verified deployment, run that exact filename with `game_run_script` on a host selected from visible root and free-RAM evidence. An earlier Terminal `ls` is stale and does not disprove a later write. A second verified write before any visible run triggers a `NO_PROGRESS` guard, which is preserved in checkpoints and across sessions. After a visible run result, revise based on its actual output. After a visible RAM rejection, inspect `ps`, `mem <file.js>`, or Active Scripts before redeploying; rewriting the file does not free host RAM. If another rooted host has enough RAM, use documented `scp` while on `home`, connect, and verify the file with visible `ls`. An `ERROR:` means diagnose before retrying; deployment is not a successful run. |
| `game_netscript_reference` | one `symbol` | Retrieve the exact signature and nearby docs for a Netscript API from the connected game's own type definitions. Accepts `ns.grow`, `grow`, or signature-like forms such as `ns.grow(host, opts)`; supplied arguments are ignored for lookup. Terminal commands and `.exe` programs are not Netscript APIs; use visible in-game help and `game_terminal` for those. |
| `game_run_script` | `filename`, optional `args`, optional `expected_host` | Run the script via the visible Terminal on the currently connected server and return the game's confirmation or visible error. If supplied, `expected_host` must match the current host shown in the visible Terminal prompt; a mismatch or missing prompt blocks execution. The tool does not connect or copy the file. A PID does not prove income; inspect output and stats afterward. |

Documentation tools cache successful exact queries for the current gameplay task
and across checkpoints. Repeating the same `game_help`, `game_troubleshoot`, or
`game_netscript_reference` request returns `NO_PROGRESS` with the previous
result excerpt. Use the result already returned; choose a different, evidence-led
action. A transient documentation error is not cached and can be retried.

If `tail` reports that no matching script process is running, do not repeat it.
A one-shot script can finish after receiving a PID, so absence from `tail` is
not proof that execution failed. Inspect visible output and progress, and read
the source with `game_read_script` if needed. Use a visible runtime error or
other concrete result to decide whether to revise or rerun. Do not attribute
another script's output to the file being tested.

`game_terminal` blocks the known unsupported `serverinfo` command without
sending browser input. For other `Command … not found` errors, send the exact
visible text to `game_troubleshoot` before choosing a supported interface.

After a confirmed run, first call `game_progress()` without arguments. It uses
the balance captured before the latest confirmed run, or the first visible
session balance. Only pass a manual money or hacking baseline if its complete
value was copied from the rendered UI; never synthesize one from memory.

Examples (these are tool inputs, not gameplay strategy):

```text
game_observe()
game_progress()
game_help(topic="servers")
game_open_tab(tab="Create Program")
game_tutorial(action="next")
game_netscript_reference(symbol="ns.grow")
game_read_script(filename="home.js")
game_terminal(command="mem home.js")
game_terminal(command="cat discovery_result.txt")
game_terminal(command="scan-analyze 2")
game_terminal(command="scp hack_n00dles.js n00dles")
game_run_script(filename="home.js", args=[])
game_run_script(filename="home.js", args=[], expected_host="home")
game_troubleshoot(error="Cannot hack this server yet")
```

When `game_deploy_script` is available, do not open the editor or type code in
the browser. The live Remote API provides script authoring; the visible game
Terminal still provides execution and confirmation. The tool only accepts a
simple script filename and does not expose saves, arbitrary game state,
deletion, or arbitrary Remote API method names. Bitburner's documented
in-game `scp filename.js server` command copies a simple `.js` file from `home`
to a named server; it remains an in-game Terminal action, not host-shell access.
See the [official getting-started guide](https://github.com/bitburner-official/bitburner-src/blob/dev/src/Documentation/doc/en/help/getting_started.md).

Generic index-based browser clicks, text entry, and browser evaluation are not
gameplay tools. `game_open_tab` is the sole game navigation action: it resolves
an allowlisted label from the current rendered DOM and clicks that fresh visible
button. `game_terminal` reacquires the
current page and visible terminal input for every command. If a transition
cannot be verified, inspect with `game_observe`; do not repeat the old action.
If `game_terminal` returns `UNCONFIRMED`, Enter was sent and the command may
have executed; the result includes the latest visible UI. Do not repeat that
command. Inspect the excerpt or call `game_observe`; use `game_read_script` for
a listed `.js` file instead of trying to read its source in Terminal.
Bitburner v3.0.1 can render script `TYPE ERROR` panels without dialog roles. For
a recognized script error, the helper accepts only a unique visible `Close`
control from a fresh Browser Use accessibility snapshot.
After a script starts, use `game_progress` to verify money, hacking level, and
script income. Do not attribute aggregate Active Scripts production to your
script unless its row or visible output confirms that script. If
`game_observe` returns `NO_PROGRESS`, passive balance or script-log updates
do not count as a changed page. Use `game_progress` for changing stats or take
a different useful action before observing again. Once the
objective has visible evidence, report it instead of polling the same screen.
When a recognized offline-progress or message dialog is closed automatically,
read the returned dialog body and choose the next action; the Terminal command
in that call was not executed. If a repeated command returns `NO_PROGRESS`,
change the diagnostic or inspect the game state before acting again.
Background script output can change the page without making that rejected
command useful; do not submit the same command again for that reason.

For network inspection, use `scan` without arguments. `scan-analyze` requires a
positive numeric depth, such as `scan-analyze 2`; passing a hostname is invalid.
When a terminal command returns an error, inspect that exact output and consult
`game_troubleshoot` before selecting a different diagnostic action.

`game_read_script` is deliberately limited to `.js` Netscript files. To inspect
text output a script wrote to the in-game home directory, use the visible game
Terminal with `cat filename.txt`; read the returned text and diagnose from that
evidence. Keep the filename simple and in the current in-game directory. Do not
try Remote API file reads for arbitrary game files or repeat the same request
after an unsupported-extension error.

Before reading an unknown script name, use `game_terminal(command="ls")` and
choose a `.js` filename shown in that result. If the visible list has no `.js`
files, don't guess a read target; proceed with an independently authored
script. A `NO_PROGRESS` response saying a script is absent means the read did
not help; do not retry it.

## Official references

General mechanics are summarized from the official [getting-started guide](https://github.com/bitburner-official/bitburner-src/blob/stable/src/Documentation/doc/en/help/getting_started.md),
[hacking guide](https://github.com/bitburner-official/bitburner-src/blob/stable/src/Documentation/doc/en/basic/hacking.md),
[script guide](https://github.com/bitburner-official/bitburner-src/blob/stable/src/Documentation/doc/en/basic/scripts.md),
and [Terminal guide](https://github.com/bitburner-official/bitburner-src/blob/stable/src/Documentation/doc/en/basic/terminal.md).
The [official `ns.nuke` reference](https://github.com/bitburner-official/bitburner-src/blob/dev/markdown/bitburner.ns.nuke.md)
documents its host argument, boolean result, and the home-only `NUKE.exe` file.
The connected game's own definitions and visible documentation take precedence
when the installed version differs from these stable references.
