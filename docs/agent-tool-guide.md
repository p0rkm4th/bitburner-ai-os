# Bitburner agent tools

Use the game-specific tools first. They share one Browser Use session; they do
not run concurrently. Check each returned result before acting again.

| Tool | Input | Intended use and result |
|---|---|---|
| `game_observe` | none | Read a compact rendered UI snapshot and detect a visible dialog. Read-only. |
| `game_help` | `topic` | Retrieve one allowlisted section of this repository's concise gameplay/tool documentation. It cannot read arbitrary files. |
| `game_troubleshoot` | `error` | Retrieve matching recovery notes for a visible game/tool error. |
| `game_dismiss_dialog` | none | Dismiss one visible dialog using its semantic close control, a unique visible button within the modal, or Escape; then verify it is gone. Never repeats automatically. |
| `game_open_tab` | allowlisted visible `tab` label | Open Terminal, Script Editor, Active Scripts, Create Program, Stats, Hacknet, City, Travel, Milestones, or Documentation by freshly matching its visible label; it never accepts element indexes or arbitrary selectors. |
| `game_terminal` | one-line `command` | Opens the in-game Terminal with its documented shortcut if needed and returns the visible result. Recognized offline-progress, message, and runtime-error dialogs are dismissed once; that call does not send the command and returns the dialog text. Unknown dialogs block the action. An identical repeat of the last Terminal command returns `NO_PROGRESS` without sending it again. A verified changed script deployment permits a new run attempt. |
| `game_read_script` | simple `filename` | Read one `.js` file from `home` through the restricted official Remote API. No path prefixes. Only read a filename shown by visible Terminal `ls`. If no `.js` is listed or the file is absent, do not guess/repeat a read; author a new script independently. |
| `game_deploy_script` | `filename`, model-authored `content` | Write one `.js` file on `home`, read it back, compare exact contents, and ask the live game for RAM cost. After a visible RAM rejection, the same file cannot be redeployed until `ps`, `mem <file.js>`, or the Active Scripts page has been inspected. An `ERROR:` means diagnose before retrying; a successful deploy is not a successful run. |
| `game_netscript_reference` | one `symbol` | Retrieve the exact signature and nearby docs for a Netscript API from the connected game's own type definitions. Accepts `ns.grow`, `grow`, or signature-like forms such as `ns.grow(host, opts)`; supplied arguments are ignored for lookup. Terminal commands and `.exe` programs are not Netscript APIs; use visible in-game help and `game_terminal` for those. |
| `game_run_script` | `filename`, optional `args` | Run the script via the visible Terminal and return the game's confirmation or visible error. This does not prove income; inspect output and stats afterward. |

Examples (these are tool inputs, not gameplay strategy):

```text
game_observe()
game_help(topic="servers")
game_open_tab(tab="Create Program")
game_netscript_reference(symbol="ns.grow")
game_read_script(filename="home.js")
game_terminal(command="mem home.js")
game_terminal(command="cat discovery_result.txt")
game_terminal(command="scan-analyze 2")
game_terminal(command="scp hack_n00dles.js n00dles")
game_run_script(filename="home.js", args=[])
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
When a recognized offline-progress or message dialog is closed automatically,
read the returned dialog body and choose the next action; the Terminal command
in that call was not executed. If a repeated command returns `NO_PROGRESS`,
change the diagnostic or inspect the game state before acting again.

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
The connected game's own definitions and visible documentation take precedence
when the installed version differs from these stable references.
