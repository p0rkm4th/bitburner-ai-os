# Offline UI action replay follow-up

This follow-up replays three minimal observations transcribed from the archived
Bitburner 3.0.1 Browser Use traces: a stale Script Editor element index, two
wrong Achievements clicks while seeking Script Editor, and a runtime error
dialog that blocked a terminal action. The fixture source descriptions are in
`tests/fixtures/ui_action_replays.json`.

| Case | Archived behavior | Deterministic helper replay |
|---|---|---|
| Stale navigation target | Five failed clicks using stale element index 20 | One fresh semantic-label lookup and verified Script Editor transition; 0 invalid targets, 0 repeated actions |
| Wrong navigation target | Achievements clicked twice while Script Editor was requested | One fresh semantic-label lookup and verified Script Editor transition; 0 invalid targets, 0 repeated actions |
| Runtime error dialog | One failed dismissal; following Terminal action was blocked | One close attempt; error text retained; blocked command not sent; no blind retry |

The deterministic replays are mocked and offline. They verify the existing
helper's behavior against the saved observations; they do not measure live
browser interaction or gameplay completion. `game_open_tab` includes a 150 ms
settle delay. The earlier helper microbenchmark measured a 150.564 ms median
for its mocked full operation, including that delay. Per-case timings were not
measured in this follow-up.

The previous Laya run remains one correct stale-target selection out of one
trial (0.727 s warm CPU forward pass, 20.241 s load). No Laya inference was run
for these added cases. Model performance for wrong-target and dialog recovery
is therefore unmeasured; no head-to-head score is claimed. The deterministic
helper passed all three cases, while avoiding model load and action-selection
inference. This small replay is insufficient to estimate general accuracy or
live task performance.

Reproduce in the pinned no-network test container:

```sh
python -m unittest tests.test_ui_replay_fixtures tests.test_game_tools -v
```

Focused result: 32 tests passed in the isolated replay worktree; after
integration, the focused replay + game-tool suite passed 73/73 tests. The full
network-disabled suite passed **175/175** tests. No game, browser profile,
inference endpoint, model weights, or network was used.
