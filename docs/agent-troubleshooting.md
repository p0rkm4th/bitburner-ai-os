# Gameplay troubleshooting

The patterns below were observed in isolated runs. They are diagnostic
procedures, not a prescribed gameplay strategy.

## Deployment and Netscript errors

- **`game_progress` rejects a baseline:** Copy the whole money value from a
  recent visible observation (for example, `$1.262k`). If it is uncertain,
  omit `baseline_money`; the tool will report current visible stats without a
  comparison. Do not invent or abbreviate a baseline.

- **Remote API offline / `getFile` HTTP 500:** Check `game_observe` for the
  visible Remote API status. Do not repeat reads or deploys while it is Offline.
  Treat a still-offline bridge as an environment blocker; retain the current
  file and ask for operator repair rather than changing network settings.
- **File not found / invalid filename:** Remote API filenames are simple
  `.js` names on `home`; remove path prefixes and inspect `ls` or `game_read_script`.
- **An old `ls` does not show a newly deployed file:** `ls` output predating a
  write is stale. When `game_deploy_script` says it read back the exact content
  and calculated RAM, run that exact filename through `game_run_script` and
  inspect the live result. Do not repeatedly rewrite or change filenames to
  refresh an old listing; after one verified write without a run, the adapter
  blocks another deployment until visible execution is attempted. A later
  revision is allowed after the run's actual output provides evidence to debug.
  The pending filename and run requirement survive a checkpoint and the next
  session; do not restart the write loop after a session boundary.
- **Need to inspect a text report:** `game_read_script` reads Netscript `.js`
  files only. Use the visible Terminal command `cat report.txt` for a simple
  in-game text filename, then base the next action on the returned output.
- **RAM calculation HTTP error:** Preserve the exact error from
  `game_deploy_script`. Query `game_netscript_reference` for each uncertain API,
  fix the model-authored code, then deploy once and verify exact read-back.
  Repeating identical content cannot fix an unknown or unavailable API.
- **`main` missing / entry point rejected:** Check the live script documentation
  and current game's expected export syntax. A deployment/read-back alone does
  not validate compilation or execution.
- **Function removed / undefined / “is not a function”:** Query the live definition for the current
  game version. Do not restore old names such as `nFormat` from memory. Debug
  using the actual runtime message, then update and redeploy the script.
- **Bitburner v3.0.x reports `formatNumber` removed:** In the observed v3.0.1
  game, the runtime dialog said: `formatNumber: Function removed in 3.0.0.
  Please use ns.format.number() instead.` Treat the running game's message as
  authoritative, query `game_netscript_reference` for `ns.format.number`, and
  revise only the affected model-authored call. A visible `run` PID confirms
  startup, not successful completion; observe for runtime errors and verify
  money/output after the repair.
- **`Cannot hack this server yet`:** Recheck the server hostname, root status,
  required hacking skill, open-port requirement, and money/security state using
  visible Terminal output and official API docs. `home` is the player's own
  computer, not an ordinary hacking target. Do not assume a replacement target.
- **`scan-analyze` usage error:** This terminal command takes a positive numeric
  network depth (for example, `scan-analyze 2`), not a server hostname. `scan`
  takes no arguments. Use the exact usage/error text to correct the command.
- **Unknown Terminal command:** Read the visible `Command … not found` result.
  Do not repeat the command with a different guessed spelling. Retrieve
  `game_troubleshoot` with the exact error, then use documented Terminal help,
  the official Documentation page, or a relevant allowlisted page via
  `game_open_tab`.
- **Target has no root access:** Stop script execution attempts against that
  host. Read the exact runtime error, inspect that host's visible root, hacking
  level, and port requirements, then query this guide and the live API reference
  before correcting your own script. `ns.nuke(host)` is a documented Netscript
  API; verify its current signature with `game_netscript_reference`. `NUKE.exe`
  is also available as a visible Terminal program. Do not infer root access from
  a deployment, a PID, or a successful network scan; verify the target's visible
  root status before retrying `hack`. A script running on `home` may call
  `ns.nuke(target)` directly; copying a script to an unrooted server or
  connecting to it does not grant root and cannot make that script run there.
  Check the `ns.nuke` boolean result and visible target permissions first.
- **No matching in-game help topic:** Terminal `help` topics are not a complete
  Netscript/API reference. Use the visible Documentation page or
  `game_netscript_reference` for an API symbol. Do not try a series of guessed
  help-topic spellings.
- **Terminal command confused with Netscript API:** `game_netscript_reference`
  is for Netscript function definitions. A terminal command or built-in `.exe`
  program is used through the visible in-game Terminal; do not search for it as
  an `ns` function.

## RAM and active process errors

- **Dynamic RAM runtime error:** A script can fail at runtime even after a
  static RAM calculation. Compare the visible dynamic usage with its allocation,
  inspect the functions named in the error, and consult their live API docs
  before revising. Recalculate the authored file, then verify a visible run.
- **No RAM / process does not start:** Read the exact `mem` or run error and
  verify available RAM on the execution host. A RAM calculation is not proof
  that the host currently has that RAM free. Scripts have a 1.6 GB minimum;
  API calls add RAM cost, so shortening or reformatting code that still uses the
  same APIs may leave the required RAM unchanged. Use `ps` or the visible Active
  Scripts page to identify processes already occupying RAM. Do not relaunch a
  script with a confirmed positive PID; inspect `tail` and actual money change.
  If a failed or duplicate process is consuming RAM, use documented Terminal
  controls only after confirming its PID and that stopping it will not discard
  useful progress. If another rooted server has enough free RAM, deploy or
  copy the authored file there and execute it on that server; connecting alone
  does not copy files. Use the documented in-game `scp filename.js server`
  command while on `home`, then connect before running it. See the [official
  scripts guide](https://github.com/bitburner-official/bitburner-src/blob/dev/src/Documentation/doc/en/basic/scripts.md)
  and [getting-started guide](https://github.com/bitburner-official/bitburner-src/blob/dev/src/Documentation/doc/en/help/getting_started.md).

## Browser and modal errors

- **“Message received” dialog:** Read its visible body before closing. Record any
  new program, reward, or `.msg` filename; after dismissing once, inspect the
  named in-game file with `game_terminal` and `cat filename.msg`. If the same
  message reappears, verify whether it is a new message or an unchanged modal
  before dismissing again.
- **A dialog is visible:** Read its visible contents, then call
  `game_dismiss_dialog` once. If the tool returns `NO_PROGRESS` because there
  is no dialog, do not call it again; use the visible error with
  `game_troubleshoot` or choose another useful action. If a dialog remains or
  the close attempt errors, report the blocker instead of retrying. Do not keep
  clicking old indexes, reload the page, or run a terminal command through a
  covered dialog.
- **Dismissal reveals a different dialog:** The first dialog closed and another
  is now covering the game. Read the returned new dialog text and use
  `game_troubleshoot` or the relevant live documentation before choosing the
  next action. Do not retry dismissal as though the original dialog were still
  open; dismiss the newly visible dialog only after inspecting it.
- **A `TYPE ERROR` dialog appears:** Treat it as a Netscript runtime error.
  Read the rendered error and stack, then dismiss it once with
  `game_dismiss_dialog` or let one `game_terminal` call dismiss it and return
  the dialog text. If either tool says `NO_PROGRESS`, do not repeat that same
  dismissal; inspect the current rendered UI and retrieve relevant
  `game_troubleshoot` notes.
- **Terminal says “Please follow the tutorial”:** The submitted command did not
  run. Inspect the visible tutorial and choose one `game_tutorial` action: use
  `next` to learn a page or deliberately choose `exit` if appropriate. Verify
  the transition before using Terminal again; do not repeat the blocked command.
- **Fresh profile shows an offline-progress dialog:** Read its visible game
  earnings and milestones, then dismiss it once with `game_dismiss_dialog`.
  Remote API Online does not mean the dialog is absent. Do not repeat
  `game_observe` while the same dialog remains; act on its visible contents.
- **Terminal not visible:** `game_terminal` uses the documented Terminal
  shortcut, refreshes the page, and verifies the current input before typing.
  If the input still is not visible, inspect and report; do not guess an index.
- **No visible change after command:** Read the tool's explicit error and
  inspect the new UI. Avoid repeating the same command without a new reason.
  A Terminal snapshot can briefly contain only a selector fragment while
  Bitburner renders the command echo and result. The helper waits up to 6
  seconds for a fresh echo, editor transition, tutorial block, run confirmation,
  or runtime error. If it returns `UNCONFIRMED`, Enter was sent and may have
  executed; inspect the included UI excerpt or call `game_observe`, and do not
  repeat the same command. Use `game_read_script` to inspect listed `.js` source.
- **`game_progress` says a stat is unavailable:** The current rendered view may
  not expose it. Open the visible `Stats` tab for hacking level or `Active
  Scripts` for running scripts, then observe the rendered result. Do not
  estimate the value or infer it from a PID.
- **`game_run_script` rejects `expected_host`:** No run command was sent. Read
  the host shown in the visible Terminal prompt, connect through the normal
  in-game interface if needed, and retry with the host you chose. The guard
  verifies the current prompt; it does not copy the script or change servers.
- **A script raises a runtime error:** `game_run_script` checks the rendered UI
  briefly after a positive PID and can return an immediate runtime-error modal.
  Read the exact error and stack location, retrieve the matching
  `game_troubleshoot` note and current Netscript definition, then make one
  model-authored correction. Redeploy and run again; a PID alone is not
  success. If the error appears later, inspect the visible modal or
  `tail <file.js>`. Stop a failed process only after confirming its PID.

## Observation, progress, and inference limits

- Use `game_observe` once when beginning an objective and after meaningful UI
  transitions. After script execution, use `game_progress` to read current
  money, hacking level, and visible income. If an unchanged `game_observe`
  returns `NO_PROGRESS`, do not repeat it; use `game_progress` or take a
  different useful action.
- Treat game-visible changes and completed, verified actions as progress. A
  successful tool call, code generation, or repeated `done` response is not.
- If two consecutive actions produce the same error or unchanged page, request
  the relevant `game_troubleshoot` note and select a different diagnostic step.
  Never replay identical code or clicks without new evidence.
- Keep each decision concise: state the current subgoal, evidence, unresolved
  issue, and next action. Do not restate the full game guide or conversation.
- A tool call timeout is not proof the game action failed; inspect the browser
  and file through the supported tools before retrying. The harness bounds
  model retries. If the response format is malformed or calls repeatedly time
  out, record the blocker and preserve the checkpoint.
- Verify money, hacking level, running process, and relevant output before
  reporting success. If the values are unchanged, state that no progress was
  demonstrated.
