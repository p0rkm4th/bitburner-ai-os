"""Integration-style tests for registered actions over a fake visible Browser Use page."""
import unittest
from types import SimpleNamespace
from unittest.mock import patch

from app.game_tools import (_visible_content_matches, find_visible_button_node, find_visible_tab_node, register_game_tools,
                            visible_money_value, visible_progress, visible_runtime_error, visible_terminal_hosts)


class FakeElement:
    def __init__(self, page, kind):
        self.page = page
        self.kind = kind

    async def get_bounding_box(self):
        if self.kind == "modal" and not self.page.modal:
            return None
        if self.kind == "modal_close" and not self.page.modal and not self.page.mui_modal:
            return None
        if self.kind == "presentation" and not self.page.presentation_only:
            return None
        if self.kind in {"editor", "editor_input", "save"} and not self.page.editor:
            return None
        if self.kind == "terminal" and self.page.editor:
            return None
        return SimpleNamespace(x=1, y=1, width=200, height=24)

    async def get_basic_info(self):
        role = "presentation" if self.kind in {"presentation", "mui_root"} else "dialog"
        return SimpleNamespace(attributes={"role": role})

    async def focus(self):
        self.page.focused = self.kind

    async def fill(self, value):
        if self.kind == "terminal":
            self.page.command = value
        elif self.kind == "editor_input":
            self.page.editor_text = value
            tokens = "\n".join(f"[{900 + i}] {token}" for i, token in enumerate(value.split()))
            self.page.visible = f"Script Editor home.js\n{tokens}"

    async def get_attribute(self, name):
        if name == "value" and self.kind == "editor_input":
            return self.page.editor_text
        return None

    async def click(self):
        if self.kind.startswith("tutorial:"):
            label = self.kind.split(":", 1)[1]
            self.page.tutorial_clicks += 1
            if not self.page.tutorial_click_noop:
                if label == "Next":
                    self.page.visible = "This tutorial will show you the basics. Page 2 Next Exit Tutorial"
                    self.page.nav_nodes = [FakeNavNode("Next", 1001), FakeNavNode("Exit Tutorial", 1002)]
                else:
                    self.page.visible = "Bitburner Terminal\n[home /]>"
                    self.page.nav_nodes = []
            return
        if self.kind == "modal_close":
            self.page.close_clicks += 1
            if self.page.dialog_after_close is not None:
                self.page.visible = self.page.dialog_after_close
                self.page.dialog_after_close = None
            elif self.page.close_attempt_succeeds:
                self.page.modal = False
                self.page.mui_modal = False
                self.page.presentation_only = False
                self.page.visible = "Bitburner Terminal\nDialog dismissed"
        if self.kind == "save":
            self.page.saved_text = self.page.editor_text
        if self.kind == "nav":
            self.page.visible = f"{self.page.nav_label} page opened"


class FakePage:
    def __init__(self):
        self.url = "https://bitburner-official.github.io/"
        self.editor = False
        self.modal = False
        self.presentation_only = False
        self.mui_modal = False
        self.modal_button_count = 1
        self.close_attempt_succeeds = True
        self.dialog_after_close = None
        self.close_clicks = 0
        self.command = ""
        self.editor_text = ""
        self.saved_text = ""
        self.focused = None
        self.terminal_visible = True
        self.run_output = None
        self.tail_output = None
        self.tail_output = None
        self.post_run_observations = []
        self.executed_commands = []
        self.delay_output_snapshots = 0
        self.stale_output_snapshots = 0
        self.delayed_visible = ""
        self.visible = "Bitburner Terminal"
        self.files = {"home.js": "export async function main(ns) {}"}
        self.nav_label = "Create Program"
        self.nav_nodes = []
        self.tutorial_clicks = 0
        self.tutorial_click_noop = False
        self.tutorial_block_terminal = False

    async def get_url(self):
        return self.url

    async def get_element(self, backend_node_id):
        if backend_node_id == 999:
            return FakeElement(self, "modal_close")
        for node in self.nav_nodes:
            if node.backend_node_id == backend_node_id and node.label in {"Next", "Exit Tutorial"}:
                return FakeElement(self, f"tutorial:{node.label}")
        return FakeElement(self, "nav")

    async def get_elements_by_css_selector(self, selector):
        if selector == '[role="dialog"]' or selector == '.MuiDialog-root':
            return [FakeElement(self, "modal")] if self.modal and not self.mui_modal else []
        if selector == '.MuiModal-root':
            if self.mui_modal:
                return [FakeElement(self, "mui_root")]
            return [FakeElement(self, "modal")] if self.modal else []
        if selector == '[aria-modal="true"]':
            if self.modal and not self.mui_modal:
                return [FakeElement(self, "modal")]
            return [FakeElement(self, "presentation")] if self.presentation_only else []
        if selector in ('[aria-modal="true"] button, [aria-modal="true"] [role="button"]',
                        '[aria-modal="true"] button, [aria-modal="true"] [role="button"], .MuiModal-root button, .MuiModal-root [role="button"]',
                        '[aria-modal="true"] button', '[aria-modal="true"] [role="button"]',
                        '[role="dialog"] button', '[role="dialog"] [role="button"]',
                        '.MuiModal-root button', '.MuiModal-root [role="button"]'):
            if self.mui_modal and selector in ('[aria-modal="true"] button, [aria-modal="true"] [role="button"]',
                                                '[aria-modal="true"] button, [aria-modal="true"] [role="button"], .MuiModal-root button, .MuiModal-root [role="button"]',
                                                '.MuiModal-root button', '.MuiModal-root [role="button"]'):
                return [FakeElement(self, "modal_close")]
            if self.modal:
                return [FakeElement(self, "modal_close") for _ in range(self.modal_button_count)]
            return []
        if selector in ('.MuiModal-root button', '.MuiModal-root [role="button"]') and self.mui_modal:
            return [FakeElement(self, "modal_close")]
        if selector in (".monaco-editor", '[role="textbox"][aria-label*="editor" i]'):
            return [FakeElement(self, "editor")] if self.editor else []
        if selector in (".monaco-editor textarea.inputarea", ".monaco-editor textarea", 'textarea[aria-label*="editor" i]'):
            return [FakeElement(self, "editor_input")] if self.editor else []
        if selector in ('button[aria-label*="Ctrl + S" i]', 'button[aria-label*="save" i]', 'button[title*="save" i]', 'button[data-testid*="save" i]'):
            return [FakeElement(self, "save")] if self.editor else []
        if selector in ("#terminal-input", 'input[aria-label*="terminal" i]', 'input[placeholder*="command" i]', 'textarea[aria-label*="terminal" i]'):
            return [FakeElement(self, "terminal")] if self.terminal_visible and not self.editor else []
        return []

    async def press(self, key):
        if key.casefold() in ("control+s", "ctrl+s") and self.editor:
            self.saved_text = self.editor_text
            return
        if key.casefold() == "escape" and self.modal:
            self.modal = False
            self.visible = "Bitburner Terminal\nDialog dismissed"
            return
        if key.casefold() == "alt+t":
            self.terminal_visible = True
            self.visible = "Bitburner Terminal\n[home /]>"
            return
        if key != "Enter" or self.focused != "terminal":
            return
        command = self.command
        if self.tutorial_block_terminal:
            self.visible = ("Bitburner Terminal\n[home /]> " + command +
                            "\nPlease follow the tutorial or click 'Exit Tutorial' if you'd like to skip it")
            return
        self.executed_commands.append(command)
        if command == "ls":
            self.visible = "Bitburner Terminal\n" + " ".join(self.files)
        elif command.startswith("cat "):
            filename = command[4:]
            self.visible = (f"Bitburner Terminal\n{self.files[filename]}" if filename in self.files
                            else f"ERROR: no file named {filename}")
        elif command.startswith("nano "):
            filename = command[5:]
            if filename in self.files:
                self.editor = True
                self.editor_text = self.files[filename]
                self.visible = f"Script Editor {filename}\n{self.editor_text}"
            else:
                self.visible = f"ERROR: no script named {filename}"
        elif command.startswith("run "):
            self.visible = self.run_output or f"Bitburner Terminal\n{command}\nRunning script home.js with PID 4; $1.25/s"
        elif command.startswith("tail "):
            self.visible = self.tail_output or f"Bitburner Terminal\n{command}\nNo script named home.js with args [] is running on the server"
        elif command.startswith("tail "):
            self.visible = self.tail_output or f"Bitburner Terminal\n{command}\nNo script named home.js with args [] is running on the server"
        elif command == "ps":
            self.visible = "Bitburner Terminal\nps\nPID Filename\n4 home.js"
        elif command.startswith("scp "):
            self.visible = f"Bitburner Terminal\n{command}\nFile copied to {command.split()[-1]}"
        elif command.startswith("scan-analyze ") and command != "scan-analyze 2":
            self.visible = f"Bitburner Terminal\n{command}\nIncorrect usage of scan-analyze command. depth argument must be positive numeric"
        else:
            self.visible = f"Bitburner Terminal\n{command}\nCommand accepted"
        if not self.editor and f"]> {command}" not in self.visible:
            terminal_prefix = "Bitburner Terminal\n"
            body = self.visible[len(terminal_prefix):] if self.visible.startswith(terminal_prefix) else self.visible
            self.visible = f"{terminal_prefix}[home /]> {command}\n{body}"
        if self.delay_output_snapshots:
            self.delayed_visible = self.visible
            self.visible = "[14]<div id=root />"
            self.stale_output_snapshots = self.delay_output_snapshots


class FakeSnapshot:
    def __init__(self, text):
        self.dom_state = self
        self.text = text
        self.selector_map = {i + 1: node for i, node in enumerate(getattr(text, "nav_nodes", []))}
        self.text = text.visible if hasattr(text, "visible") else text

    def llm_representation(self):
        return self.text


class FakeBrowserSession:
    def __init__(self, page):
        self.page = page

    async def get_current_page(self):
        return self.page

    async def get_browser_state_summary(self, include_screenshot=False):
        if (self.page.post_run_observations and self.page.executed_commands
                and self.page.executed_commands[-1].startswith("run ")):
            self.page.visible = self.page.post_run_observations.pop(0)
            if "RUNTIME ERROR" in self.page.visible:
                self.page.modal = True
                self.page.mui_modal = True
                self.page.presentation_only = True
        snapshot = FakeSnapshot(self.page)
        if self.page.stale_output_snapshots:
            self.page.stale_output_snapshots -= 1
            if self.page.stale_output_snapshots == 0:
                self.page.visible = self.page.delayed_visible
        return snapshot


class FakeNavNode:
    def __init__(self, label, backend_node_id=1, visible=True, role="button"):
        self.label = label
        self.backend_node_id = backend_node_id
        self.is_visible = visible
        self.attributes = {"role": role}

    def get_all_children_text(self):
        return self.label


class FakeTools:
    def action(self, description=""):
        def decorate(fn):
            return fn
        return decorate


class GameToolIntegrationTests(unittest.IsolatedAsyncioTestCase):
    async def asyncSetUp(self):
        self.page = FakePage()
        self.browser = FakeBrowserSession(self.page)
        self.action_state = {}
        self.actions = register_game_tools(FakeTools(), action_state=self.action_state)

    async def test_observe_and_terminal_round_trip(self):
        state = await self.actions["game_observe"](self.browser)
        self.assertIn("Visible dialog: none", state)
        result = await self.actions["game_terminal"]("ls", self.browser)
        self.assertIn("home.js", result)

    async def test_terminal_waits_for_fresh_command_echo_before_reporting_visible_error(self):
        self.page.delay_output_snapshots = 2
        self.page.run_output = (
            "Bitburner Terminal\n[home /]> run hack_n00dles.js\n"
            "Cannot run hack_n00dles.js (t=1) on home. This script requires 1.70GB of RAM.\n[home /]>"
        )
        result = await self.actions["game_terminal"]("run hack_n00dles.js", self.browser)
        self.assertIn("Cannot run hack_n00dles.js (t=1) on home", result)
        self.assertEqual(self.page.executed_commands, ["run hack_n00dles.js"])

    async def test_terminal_waits_for_delayed_visible_command_result(self):
        # Live Run 41 showed rendered Terminal output arriving after the old
        # 2.5 second confirmation window. This models that delayed DOM update.
        self.page.delay_output_snapshots = 12
        result = await self.actions["game_terminal"]("cat home.js", self.browser)
        self.assertIn("cat home.js", result)
        self.assertIn("export async function main(ns)", result)
        self.assertEqual(self.page.executed_commands, ["cat home.js"])

    async def test_terminal_timeout_blocks_blind_retry_when_output_never_arrives(self):
        self.page.delay_output_snapshots = 30
        with patch("app.game_tools.TERMINAL_RESULT_CONFIRM_TIMEOUT_SECONDS", 0.25):
            first = await self.actions["game_terminal"]("ls", self.browser)
            second = await self.actions["game_terminal"]("ls", self.browser)
        self.assertTrue(first.startswith("UNCONFIRMED:"))
        self.assertIn("Latest visible UI:", first)
        self.assertIn("do not repeat it", first)
        self.assertTrue(second.startswith("NO_PROGRESS:"))
        self.assertIn("game_observe", second)
        self.assertEqual(self.page.executed_commands, ["ls"])

    async def test_terminal_reports_tutorial_block_and_retries_only_after_explicit_exit(self):
        self.page.tutorial_block_terminal = True
        self.page.visible = "Bitburner Terminal"
        self.page.nav_nodes = [FakeNavNode("Next", 1001), FakeNavNode("Exit Tutorial", 1002)]
        blocked = await self.actions["game_terminal"]("ls", self.browser)
        self.assertTrue(blocked.startswith("BLOCKED:"))
        self.assertIn("the command was not executed", blocked)
        self.assertEqual(self.page.executed_commands, [])
        exited = await self.actions["game_tutorial"]("exit", self.browser)
        self.assertTrue(exited.startswith("Exited the visible tutorial;"))
        self.page.tutorial_block_terminal = False
        listing = await self.actions["game_terminal"]("ls", self.browser)
        self.assertIn("home.js", listing)
        self.assertEqual(self.page.executed_commands, ["ls"])

    async def test_identical_observation_is_reported_as_no_progress(self):
        first = await self.actions["game_observe"](self.browser)
        repeated = await self.actions["game_observe"](self.browser)
        self.assertIn("Visible dialog: none", first)
        self.assertTrue(repeated.startswith("NO_PROGRESS:"))
        self.page.visible = "Bitburner Terminal\nA different visible screen"
        changed = await self.actions["game_observe"](self.browser)
        self.assertIn("A different visible screen", changed)

    async def test_passive_money_and_script_log_updates_do_not_enable_observation_polling(self):
        self.page.visible = ("Overview\nMoney $100\nHack 1\nTerminal\n"
                             "hack.js: Stole $5 from n00dles")
        first = await self.actions["game_observe"](self.browser)
        self.page.visible = ("Overview\nMoney $200\nHack 1\nTerminal\n"
                             "hack.js: Stole $6 from n00dles")
        repeated = await self.actions["game_observe"](self.browser)
        self.assertIn("Money $100", first)
        self.assertTrue(repeated.startswith("NO_PROGRESS:"))
        self.assertIn("game_progress", repeated)

    async def test_progress_check_recovers_after_duplicate_observation_without_resetting_it(self):
        self.page.visible = "Overview\nMoney $1.838k\nHack 1\nActive Scripts\nProduction $0.022 / sec"
        first = await self.actions["game_observe"](self.browser)
        blocked = await self.actions["game_observe"](self.browser)
        self.assertIn("Money $1.838k", first)
        self.assertTrue(blocked.startswith("NO_PROGRESS:"))

        progress = await self.actions["game_progress"](self.browser, baseline_money="$1.262k",
                                                          baseline_hacking_level=1)
        self.assertIn("Money: $1.838k", progress)
        self.assertIn("Visible script income: $0.022/s", progress)
        self.assertIn("Money comparison: current $1.838k, baseline $1.262k", progress)
        self.assertIn("Hacking-level change from baseline: +0", progress)
        self.assertTrue((await self.actions["game_observe"](self.browser)).startswith("NO_PROGRESS:"))

    async def test_open_tab_reacquires_visible_label_and_verifies_transition(self):
        self.page.nav_nodes = [FakeNavNode("Create Program")]
        result = await self.actions["game_open_tab"]("Create Program", self.browser)
        self.assertIn("Opened visible game tab 'Create Program'", result)
        self.assertEqual(self.page.visible, "Create Program page opened")

    async def test_tutorial_next_uses_fresh_visible_button_and_verifies_page_change(self):
        self.page.visible = "This tutorial will show you the basics. Page 1 Next Exit Tutorial"
        self.page.nav_nodes = [FakeNavNode("Next", 1001), FakeNavNode("Exit Tutorial", 1002)]
        result = await self.actions["game_tutorial"]("next", self.browser)
        self.assertTrue(result.startswith("Advanced one tutorial page; the rendered transition was verified."))
        self.assertIn("Page 2", result)
        self.assertEqual(self.page.tutorial_clicks, 1)

    async def test_tutorial_exit_is_explicit_and_verified(self):
        self.page.visible = "This tutorial will show you the basics. Next Exit Tutorial"
        exit_button = FakeNavNode("Exit Tutorial", 1002, role="")
        exit_button.attributes = {"type": "button"}
        exit_button.tag_name = "button"
        self.page.nav_nodes = [FakeNavNode("Next", 1001), exit_button]
        result = await self.actions["game_tutorial"]("exit", self.browser)
        self.assertTrue(result.startswith("Exited the visible tutorial; the rendered transition was verified."))
        self.assertNotIn("Exit Tutorial", result.split("\n", 1)[1])
        self.assertEqual(self.page.tutorial_clicks, 1)

    async def test_tutorial_action_without_tutorial_does_not_click(self):
        result = await self.actions["game_tutorial"]("next", self.browser)
        self.assertTrue(result.startswith("NO_PROGRESS:"))
        self.assertEqual(self.page.tutorial_clicks, 0)

    async def test_unchanged_tutorial_page_blocks_repeated_click(self):
        self.page.visible = "This tutorial will show you the basics. Next Exit Tutorial"
        self.page.nav_nodes = [FakeNavNode("Next", 1001), FakeNavNode("Exit Tutorial", 1002)]
        self.page.tutorial_click_noop = True
        first = await self.actions["game_tutorial"]("next", self.browser)
        second = await self.actions["game_tutorial"]("next", self.browser)
        self.assertTrue(first.startswith("ERROR:"))
        self.assertTrue(second.startswith("NO_PROGRESS:"))
        self.assertEqual(self.page.tutorial_clicks, 1)

    def test_tutorial_button_lookup_requires_unique_fresh_visible_exact_label(self):
        state = SimpleNamespace(selector_map={
            1: FakeNavNode("Next", 1001),
            2: FakeNavNode("Next page", 1002),
            3: FakeNavNode("Next", 1003, visible=False),
        })
        node = find_visible_button_node(state, "Next")
        self.assertEqual(node.backend_node_id, 1001)
        state.selector_map[4] = FakeNavNode("Next", 1004)
        self.assertIsNone(find_visible_button_node(state, "Next"))

    def test_terminal_host_parser_accepts_visible_prompt_renderings(self):
        self.assertEqual(visible_terminal_hosts("Terminal\n[home /]>"), ["home"])
        self.assertEqual(visible_terminal_hosts("Terminal\nhome\n\t]>"), ["home"])
        self.assertEqual(visible_terminal_hosts("Terminal\nrandom home text\nWelcome"), [])

    def test_visible_money_value_parses_only_rendered_hud_balance(self):
        self.assertEqual(visible_money_value("Overview\nMoney\n$1.262k"), 1262.0)
        self.assertIsNone(visible_money_value("Terminal output\n$1.262k"))

    def test_tutorial_lookup_accepts_native_button_without_explicit_role(self):
        native = FakeNavNode("Exit Tutorial", 1005, role="")
        native.attributes = {"type": "button"}
        native.tag_name = "button"
        state = SimpleNamespace(selector_map={1: native})
        self.assertEqual(find_visible_button_node(state, "Exit Tutorial").backend_node_id, 1005)

    async def test_open_tab_rejects_unknown_or_ambiguous_navigation_targets(self):
        unknown = await self.actions["game_open_tab"]("Arbitrary URL", self.browser)
        self.assertIn("Allowed exact labels:", unknown)
        self.assertIn("Terminal", unknown)
        self.assertIn("No browser action was sent", unknown)
        self.page.nav_nodes = [FakeNavNode("Stats", 1), FakeNavNode("Stats", 2)]
        ambiguous = await self.actions["game_open_tab"]("Stats", self.browser)
        self.assertIn("exactly one fresh visible navigation button", ambiguous)

    def test_open_tab_schema_restricts_targets_to_visible_labels(self):
        from browser_use import Tools

        browser_tools = Tools()
        register_game_tools(browser_tools)
        schema = browser_tools.registry.registry.actions["game_open_tab"].param_model.model_json_schema()
        self.assertEqual(schema["properties"]["tab"]["enum"], [
            "Terminal", "Script Editor", "Active Scripts", "Create Program", "Stats",
            "Hacknet", "City", "Travel", "Milestones", "Documentation",
        ])

    async def test_tab_label_matching_ignores_hidden_and_non_button_nodes(self):
        nodes = [FakeNavNode("Create Program", 1, visible=False), FakeNavNode("Create Program", 2, role="link"),
                 FakeNavNode("Stats", 3)]
        state = SimpleNamespace(selector_map={i: node for i, node in enumerate(nodes)})
        self.assertEqual(find_visible_tab_node(state, "Stats").backend_node_id, 3)
        self.assertIsNone(find_visible_tab_node(state, "Create Program"))

    async def test_terminal_reopens_by_shortcut_and_refreshes_the_visible_input(self):
        self.page.terminal_visible = False
        result = await self.actions["game_terminal"]("ls", self.browser)
        self.assertIn("home.js", result)
        self.assertTrue(self.page.terminal_visible)
        self.assertEqual(self.page.command, "ls")

    async def test_terminal_dismisses_known_game_dialog_before_action_and_reports_body(self):
        self.page.modal = True
        self.page.mui_modal = True
        self.page.presentation_only = True
        self.page.visible = "Offline for 1 hour. Your scripts generated $0.000"
        result = await self.actions["game_terminal"]("help", self.browser)
        self.assertTrue(result.startswith("NO_PROGRESS:"))
        self.assertIn("Offline for 1 hour", result)
        self.assertIn("requested action was not performed", result)
        self.assertEqual(self.page.close_clicks, 1)
        self.assertEqual(self.page.executed_commands, [])

    async def test_terminal_dismisses_visible_runtime_error_once_before_next_command(self):
        self.page.modal = True
        # The live game's accessible DOM presents the heading across two lines.
        self.page.visible = "RUNTIME\nERROR\nscript crashed\nScript: home.js\nPID: 1"
        result = await self.actions["game_terminal"]("ps", self.browser)
        self.assertTrue(result.startswith("NO_PROGRESS:"))
        self.assertIn("RUNTIME\nERROR", result)
        self.assertIn("requested action was not performed", result)
        self.assertFalse(self.page.modal)
        self.assertEqual(self.page.executed_commands, [])

    async def test_terminal_dismisses_bitburner_type_error_before_sending_command(self):
        self.page.modal = True
        self.page.mui_modal = True
        self.page.presentation_only = True
        self.page.visible = (
            "TYPE ERROR\nTypeError: ns.getMoney is not a function\n"
            "Stack: TypeError: ns.getMoney is not a function\n"
            "at main (home/hack.js:11:22)\nScript: hack.js\nPID: 1\n"
            "Suppress error modals (5 min) Close View Script Logs Errors Page"
        )
        result = await self.actions["game_terminal"]("ls", self.browser)
        self.assertTrue(result.startswith("NO_PROGRESS:"))
        self.assertIn("TYPE ERROR", result)
        self.assertIn("ns.getMoney is not a function", result)
        self.assertIn("requested action was not performed", result)
        self.assertEqual(self.page.close_clicks, 1)
        self.assertEqual(self.page.executed_commands, [])

    async def test_terminal_rejects_same_command_repeat_without_sending_it(self):
        first = await self.actions["game_terminal"]("help", self.browser)
        second = await self.actions["game_terminal"]("help", self.browser)
        self.assertIn("Command accepted", first)
        self.assertTrue(second.startswith("NO_PROGRESS:"))
        self.assertIn("repeat was not sent", second)
        self.assertEqual(self.page.executed_commands, ["help"])

    async def test_terminal_blocks_known_unsupported_serverinfo_command(self):
        result = await self.actions["game_terminal"]("serverinfo n00dles", self.browser)
        self.assertTrue(result.startswith("BLOCKED:"))
        self.assertIn("no Terminal `serverinfo` command", result)
        self.assertIn("game_troubleshoot", result)
        self.assertEqual(self.page.executed_commands, [])

    async def test_terminal_rejects_connect_to_current_host(self):
        self.page.visible = "Bitburner Terminal\n[n00dles /]> run hack.js"
        result = await self.actions["game_terminal"]("connect n00dles", self.browser)
        self.assertTrue(result.startswith("NO_PROGRESS:"))
        self.assertIn("Already connected to n00dles", result)
        self.assertIn("does not change the server or grant root access", result)
        self.assertEqual(self.page.executed_commands, [])

    async def test_terminal_allows_connect_to_a_different_visible_host(self):
        self.page.visible = "Bitburner Terminal\n[home /]> scan"
        result = await self.actions["game_terminal"]("connect n00dles", self.browser)
        self.assertIn("Command accepted", result)
        self.assertEqual(self.page.executed_commands, ["connect n00dles"])

    async def test_terminal_preserves_and_marks_visible_ram_error(self):
        self.page.run_output = (
            "Bitburner Terminal\n[home /]> run home.js\n"
            "Cannot run home.js (t=1) on home. This script requires 81.60GB of RAM."
        )
        result = await self.actions["game_terminal"]("run home.js", self.browser)
        self.assertTrue(result.startswith("VISIBLE GAME ERROR (verbatim):"))
        self.assertIn("requires 81.60GB of RAM", result)

    async def test_terminal_tail_no_running_script_gives_actionable_diagnostics(self):
        self.page.tail_output = (
            "Bitburner Terminal\n[home /]> tail hack_n00dles_fast.js\n"
            "No script named hack_n00dles_fast.js with args [] is running on the server"
        )
        result = await self.actions["game_terminal"]("tail hack_n00dles_fast.js", self.browser)
        self.assertIn("SCRIPT STATUS (not an execution error)", result)
        self.assertIn("No script named hack_n00dles_fast.js", result)
        self.assertIn("absence now does not prove that launch failed", result)
        self.assertIn("Do not repeat `tail`", result)
        self.assertIn("Active Scripts", result)
        self.assertIn("game_read_script", result)
        repeat = await self.actions["game_terminal"]("tail hack_n00dles_fast.js", self.browser)
        self.assertTrue(repeat.startswith("NO_PROGRESS:"))
        self.assertEqual(self.page.executed_commands, ["tail hack_n00dles_fast.js"])

    async def test_terminal_tail_no_running_script_gives_actionable_diagnostics(self):
        self.page.tail_output = (
            "Bitburner Terminal\n[home /]> tail hack_n00dles_fast.js\n"
            "No script named hack_n00dles_fast.js with args [] is running on the server"
        )
        result = await self.actions["game_terminal"]("tail hack_n00dles_fast.js", self.browser)
        self.assertIn("SCRIPT STATUS (not an execution error)", result)
        self.assertIn("No script named hack_n00dles_fast.js", result)
        self.assertIn("absence now does not prove that launch failed", result)
        self.assertIn("Do not repeat `tail`", result)
        self.assertIn("Active Scripts", result)
        self.assertIn("game_read_script", result)
        repeat = await self.actions["game_terminal"]("tail hack_n00dles_fast.js", self.browser)
        self.assertTrue(repeat.startswith("NO_PROGRESS:"))
        self.assertEqual(self.page.executed_commands, ["tail hack_n00dles_fast.js"])

    async def test_run_script_catches_runtime_error_that_follows_pid_confirmation(self):
        self.page.post_run_observations = [
            "Bitburner Terminal\nrun home.js\nRunning script with 1 thread, PID 4",
            "RUNTIME ERROR\nREMOVED FUNCTION ERROR\nhome.js@home (PID - 1)\nformatNumber: Function removed in 3.0.0.",
        ]
        result = await self.actions["game_run_script"]("home.js", self.browser)
        self.assertIn("RUNTIME ERROR", result)
        self.assertIn("formatNumber: Function removed in 3.0.0", result)
        self.assertEqual(self.page.executed_commands, ["run home.js"])

    async def test_runtime_error_excerpt_comes_only_from_rendered_ui(self):
        visible = "Terminal output\nRUNTIME ERROR\nScript: home.js\nPID: 4\nns.hack is not a function\nStack: home.js:L3"
        excerpt = visible_runtime_error(visible)
        self.assertIn("ns.hack is not a function", excerpt)
        type_error = visible_runtime_error(
            "TYPE ERROR\nTypeError: ns.getMoney is not a function\nScript: hack.js\nPID: 1")
        self.assertIn("TYPE ERROR", type_error)
        self.assertIn("ns.getMoney is not a function", type_error)
        reference_error = visible_runtime_error(
            "REFERENCE ERROR\nReferenceError: ns is not defined\nScript:\nhack.js\nPID:\n4\nClose")
        self.assertIn("ReferenceError: ns is not defined", reference_error)
        concurrency_error = visible_runtime_error(
            "CONCURRENCY ERROR\nweaken: Concurrent calls to Netscript functions are not allowed!\n"
            "Script:\nhack.js\nPID:\n4\nClose")
        self.assertIn("Concurrent calls to Netscript functions are not allowed", concurrency_error)
        self.assertEqual(visible_runtime_error("ordinary visible game page"), "")

    async def test_terminal_records_ram_rejection_and_process_inspection_satisfies_diagnostic_gate(self):
        self.page.run_output = (
            "Bitburner Terminal\n[home /]> run simple_hack.js n00dles\n"
            "Cannot run simple_hack.js (t=1) on home. This script requires 1.70GB of RAM."
        )
        result = await self.actions["game_terminal"]("run simple_hack.js n00dles", self.browser)
        self.assertIn("requires 1.70GB of RAM", result)
        self.assertEqual(self.action_state["ram_rejection"], {
            "filename": "simple_hack.js", "host": "home", "required_ram": "1.70", "diagnosed": False,
        })
        await self.actions["game_terminal"]("ps", self.browser)
        self.assertTrue(self.action_state["ram_rejection"]["diagnosed"])

    async def test_terminal_reads_model_authored_text_report_visibly(self):
        self.page.files["discovery_result.txt"] = "home\nfoodnstuff\n"
        result = await self.actions["game_terminal"]("cat discovery_result.txt", self.browser)
        self.assertIn("foodnstuff", result)
        self.assertEqual(self.page.command, "cat discovery_result.txt")

    async def test_visible_editor_verification_accepts_tokenized_monaco_text(self):
        source = "export async function main(ns) {\n  await ns.sleep(10);\n}"
        tokenized = "[10] export\n[11] async\n[12] function\n[13] main\n[14] (ns)\n[15] {\n[16] await\n[17] ns.sleep(10);\n[18] }"
        self.assertTrue(_visible_content_matches(source, tokenized))
        self.assertFalse(_visible_content_matches(source, tokenized.replace("sleep(10)", "hack(\"food\")")))

    async def test_modal_stops_terminal_operation_with_actionable_error(self):
        self.page.modal = True
        result = await self.actions["game_terminal"]("ls", self.browser)
        self.assertIn("visible dialog", result)
        self.assertIn("dismiss it with its visible UI control", result)

    async def test_presentation_shell_is_not_mistaken_for_an_open_dialog(self):
        self.page.presentation_only = True
        state = await self.actions["game_observe"](self.browser)
        self.assertIn("Visible dialog: none", state)
        result = await self.actions["game_terminal"]("ls", self.browser)
        self.assertIn("home.js", result)

    async def test_empty_mui_presentation_shell_with_visible_button_is_not_a_dialog(self):
        self.page.mui_modal = True
        self.page.presentation_only = True
        self.page.visible = "Bitburner Terminal\n[home /]>"
        state = await self.actions["game_observe"](self.browser)
        self.assertIn("Visible dialog: none", state)
        result = await self.actions["game_terminal"]("ls", self.browser)
        self.assertIn("home.js", result)

    async def test_dialog_dismissal_uses_escape_once_and_verifies_transition(self):
        self.page.modal = True
        result = await self.actions["game_dismiss_dialog"](self.browser)
        self.assertIn("dismissed and verified absent", result)
        self.assertEqual(self.page.close_clicks, 1)
        self.assertFalse(self.page.modal)

    async def test_dialog_dismissal_without_visible_modal_is_no_progress(self):
        self.page.visible = "Bitburner Terminal\nRUNTIME ERROR hack: no root access"
        result = await self.actions["game_dismiss_dialog"](self.browser)
        self.assertIn("NO_PROGRESS", result)
        self.assertIn("no input was sent", result)
        self.assertIn("Use game_troubleshoot", result)
        self.assertIn("no root access", result)
        self.assertEqual(self.page.close_clicks, 0)

    async def test_repeated_dialog_dismissal_after_success_is_rejected(self):
        self.page.modal = True
        first = await self.actions["game_dismiss_dialog"](self.browser)
        self.assertIn("dismissed and verified absent", first)
        second = await self.actions["game_dismiss_dialog"](self.browser)
        self.assertIn("NO_PROGRESS", second)
        self.assertIn("Do not call game_dismiss_dialog again", second)
        self.assertEqual(self.page.close_clicks, 1)

    async def test_new_visible_dialog_can_be_dismissed_after_prior_dialog(self):
        self.page.modal = True
        await self.actions["game_dismiss_dialog"](self.browser)
        self.page.modal = True
        second = await self.actions["game_dismiss_dialog"](self.browser)
        self.assertIn("dismissed and verified absent", second)
        self.assertEqual(self.page.close_clicks, 2)

    async def test_bitburner_mui_presentation_dialog_uses_its_unique_close_button(self):
        self.page.modal = True
        self.page.mui_modal = True
        self.page.presentation_only = True
        self.page.visible = "Offline for 1 hour. Your scripts generated $0.000"
        result = await self.actions["game_dismiss_dialog"](self.browser)
        self.assertIn("dismissed and verified absent", result)
        self.assertEqual(self.page.close_clicks, 1)
        self.assertFalse(self.page.modal)

    async def test_bitburner_message_modal_uses_unique_visible_button_in_presentation_shell(self):
        self.page.modal = True
        self.page.mui_modal = True
        self.page.presentation_only = True
        self.page.visible = (
            "Message received from unknown sender: Use this program to track your progress. "
            "This message was saved as j0.msg onto your home computer."
        )
        result = await self.actions["game_dismiss_dialog"](self.browser)
        self.assertIn("dismissed and verified absent", result)
        self.assertEqual(self.page.close_clicks, 1)

    async def test_runtime_error_modal_selects_visible_close_with_other_buttons_present(self):
        self.page.modal = True
        self.page.mui_modal = True
        self.page.presentation_only = True
        self.page.modal_button_count = 3
        self.page.nav_nodes = [FakeNavNode("Close", backend_node_id=999)]
        self.page.visible = (
            "RUNTIME ERROR hack: no root access Script: home.js PID: 2 "
            "Suppress error modals (5 min) Close View Script Logs Errors Page"
        )
        result = await self.actions["game_dismiss_dialog"](self.browser)
        self.assertIn("dismissed and verified absent", result)
        self.assertEqual(self.page.close_clicks, 1)
        self.assertFalse(self.page.modal)

    async def test_reference_error_modal_uses_fresh_visible_close_button(self):
        self.page.visible = (
            "REFERENCE ERROR\nReferenceError: ns is not defined\n"
            "Stack: home/hack_n00dles_fast.js:16\n"
            "Script:\nhack_n00dles_fast.js\nPID:\n4\nClose\nView Script Logs\nErrors Page"
        )
        self.page.nav_nodes = [FakeNavNode("Close", 999)]
        result = await self.actions["game_dismiss_dialog"](self.browser)
        self.assertIn("dismissed and verified absent", result)
        self.assertEqual(self.page.close_clicks, 1)
        self.assertEqual(self.page.visible, "Bitburner Terminal\nDialog dismissed")

    async def test_concurrency_error_modal_uses_fresh_visible_close_button(self):
        self.page.visible = (
            "CONCURRENCY ERROR\nweaken: Concurrent calls to Netscript functions are not allowed!\n"
            "Stack: hack_n00dles_fast.js:L6@main\n"
            "Script:\nhack_n00dles_fast.js\nPID:\n4\nClose\nView Script Logs\nErrors Page"
        )
        self.page.nav_nodes = [FakeNavNode("Close", 999)]
        result = await self.actions["game_dismiss_dialog"](self.browser)
        self.assertIn("dismissed and verified absent", result)
        self.assertEqual(self.page.close_clicks, 1)
        self.assertEqual(self.page.visible, "Bitburner Terminal\nDialog dismissed")

    async def test_type_error_modal_selects_visible_close_with_other_buttons_present(self):
        self.page.modal = True
        self.page.mui_modal = True
        self.page.presentation_only = True
        self.page.modal_button_count = 3
        self.page.nav_nodes = [FakeNavNode("Close", backend_node_id=999)]
        self.page.visible = (
            "TYPE ERROR\nTypeError: ns.getMoney is not a function\n"
            "Stack: home/hack.js:11\nScript: hack.js PID: 1\n"
            "Suppress error modals (5 min) Close View Script Logs Errors Page"
        )
        result = await self.actions["game_dismiss_dialog"](self.browser)
        self.assertIn("dismissed and verified absent", result)
        self.assertEqual(self.page.close_clicks, 1)
        self.assertFalse(self.page.modal)

    async def test_type_error_on_bare_div_surface_uses_only_fresh_accessible_close(self):
        # The live Bitburner Type Error had no dialog role or MUI modal root;
        # only the rendered error text and its visible Close button were exposed.
        self.page.modal = False
        self.page.mui_modal = False
        self.page.presentation_only = False
        self.page.nav_nodes = [FakeNavNode("Close", backend_node_id=999)]
        self.page.visible = (
            "TYPE\nERROR\nTypeError: ns.getMoney is not a function\n"
            "Stack: TypeError: ns.getMoney is not a function\n"
            "Script: hack.js\nPID: 1\nClose\nView Script Logs\nErrors Page"
        )
        result = await self.actions["game_dismiss_dialog"](self.browser)
        self.assertIn("dismissed and verified absent", result)
        self.assertEqual(self.page.close_clicks, 1)
        self.assertEqual(self.page.visible, "Bitburner Terminal\nDialog dismissed")

    async def test_failed_dialog_close_is_never_repeated_for_same_visible_modal(self):
        self.page.modal = True
        self.page.mui_modal = True
        self.page.presentation_only = True
        self.page.modal_button_count = 3
        self.page.nav_nodes = [FakeNavNode("Close", backend_node_id=999)]
        self.page.close_attempt_succeeds = False
        self.page.visible = (
            "RUNTIME ERROR hack: no root access Script: home.js PID: 2 "
            "Suppress error modals (5 min) Close View Script Logs Errors Page"
        )
        first = await self.actions["game_dismiss_dialog"](self.browser)
        self.assertIn("ERROR: Dialog", first)
        self.assertEqual(self.page.close_clicks, 1)
        second = await self.actions["game_dismiss_dialog"](self.browser)
        self.assertIn("NO_PROGRESS", second)
        self.assertIn("No input was sent", second)
        self.assertEqual(self.page.close_clicks, 1)
        self.assertTrue(self.page.modal)

    async def test_dialog_still_visible_is_reported_without_repeat(self):
        self.page.modal = True
        self.page.modal_button_count = 2
        original_press = self.page.press
        async def ignore_escape(key):
            if key != "Escape":
                await original_press(key)
        self.page.press = ignore_escape
        result = await self.actions["game_dismiss_dialog"](self.browser)
        self.assertIn("remains after one close attempt", result)
        self.assertTrue(self.page.modal)

    async def test_dismissal_reports_newly_revealed_dialog_as_transition(self):
        self.page.modal = True
        self.page.mui_modal = True
        self.page.presentation_only = True
        self.page.visible = "Offline for 57 seconds. Your scripts generated $20.199 Close"
        self.page.dialog_after_close = (
            "RUNTIME ERROR RAM USAGE ERROR Script: hack_n00dles.js PID: -4 "
            "weaken Dynamic RAM Usage: 1.80GB RAM Allocation: 1.70GB Close"
        )

        result = await self.actions["game_dismiss_dialog"](self.browser)

        self.assertTrue(result.startswith("Dialog transition verified:"))
        self.assertIn("RUNTIME ERROR RAM USAGE ERROR", result)
        self.assertIn("Dynamic RAM Usage: 1.80GB", result)
        self.assertEqual(self.page.close_clicks, 1)
        self.assertTrue(self.page.modal)

        # The newly visible error is an independent dialog and can be handled
        # once on a later model action after inspecting its contents.
        next_result = await self.actions["game_dismiss_dialog"](self.browser)
        self.assertIn("Dialog dismissed and verified absent", next_result)
        self.assertEqual(self.page.close_clicks, 2)

    async def test_existing_editor_edit_save_and_run_cycle(self):
        opened = await self.actions["game_open_editor"]("home.js", self.browser)
        self.assertIn("Opened existing home.js", opened)
        authored = "export async function main(ns) {\n  await ns.sleep(10);\n}"
        saved = await self.actions["game_edit_script"]("home.js", authored, self.browser)
        self.assertIn("Saved home.js", saved)
        self.assertIn("contents still match", saved)
        self.assertEqual(self.page.saved_text, authored)
        self.assertTrue(self.page.editor)
        # The model uses the visible Terminal tab to return from the editor.
        self.page.editor = False
        ran = await self.actions["game_run_script"]("home.js", self.browser, [])
        self.assertIn("Running script home.js", ran)
        self.assertIn("$1.25/s", ran)

    async def test_editor_refuses_unverified_content_and_run_reports_missing_terminal(self):
        opened = await self.actions["game_open_editor"]("home.js", self.browser)
        self.assertIn("Opened existing", opened)
        self.page.editor = False
        result = await self.actions["game_run_script"]("unsafe.txt", self.browser, [])
        self.assertIn("simple in-game .js", result)

    async def test_run_returns_visible_game_error_for_model_debugging(self):
        self.page.run_output = "Bitburner Terminal\nrun home.js\nRUNTIME ERROR\nhacknumthreads is not a function"
        result = await self.actions["game_run_script"]("home.js", self.browser, [])
        self.assertIn("RUNTIME ERROR", result)
        self.assertIn("hacknumthreads is not a function", result)

    async def test_run_script_expected_host_guard_prevents_wrong_server_execution(self):
        self.page.visible = "Bitburner Terminal\n[home /]>"
        result = await self.actions["game_run_script"](
            "home.js", self.browser, [], expected_host="n00dles")
        self.assertIn("Not running home.js", result)
        self.assertIn("current prompt shows home", result)
        self.assertEqual(self.page.executed_commands, [])

    async def test_run_script_expected_host_requires_visible_prompt_and_valid_host(self):
        self.page.visible = "Bitburner Terminal without a prompt"
        result = await self.actions["game_run_script"](
            "home.js", self.browser, [], expected_host="n00dles")
        self.assertIn("Could not verify a current server", result)
        self.assertEqual(self.page.executed_commands, [])
        invalid = await self.actions["game_run_script"](
            "home.js", self.browser, [], expected_host="n00dles;run other.js")
        self.assertIn("simple visible Bitburner server name", invalid)
        self.assertEqual(self.page.executed_commands, [])

    async def test_run_script_executes_when_expected_host_matches_visible_prompt(self):
        self.page.visible = "Bitburner Terminal\n[n00dles /]>"
        self.page.run_output = "Bitburner Terminal\n[n00dles /]> run home.js\nRunning script home.js with PID 4"
        result = await self.actions["game_run_script"](
            "home.js", self.browser, [], expected_host="n00dles")
        self.assertIn("Running script home.js", result)
        self.assertEqual(self.page.executed_commands, ["run home.js"])

    async def test_confirmed_run_records_visible_money_before_terminal_execution(self):
        self.page.visible = "Overview\nMoney\n$1.262k\nHack\n1\n[home /]>"
        self.page.run_output = "Bitburner Terminal\n[home /]> run home.js\nRunning script home.js with PID 4"
        result = await self.actions["game_run_script"]("home.js", self.browser, [])
        self.assertIn("Running script home.js", result)
        self.assertEqual(self.action_state["money_at_script_run"], 1262.0)
        self.assertNotIn("money_before_run_attempt", self.action_state)

    async def test_old_visible_pid_does_not_confirm_a_new_ram_rejected_run(self):
        self.page.visible = (
            "Overview\nMoney\n$1.262k\nBitburner Terminal\n[home /]> run home.js\n"
            "Running script with 1 thread, PID 4"
        )
        self.page.run_output = (
            "Bitburner Terminal\n[home /]> run home.js\nRunning script with 1 thread, PID 4\n"
            "[home /]> run home.js\nCannot run home.js (t=1) on home. This script requires 81.60GB of RAM."
        )

        result = await self.actions["game_run_script"]("home.js", self.browser, [])

        self.assertIn("requires 81.60GB of RAM", result)
        self.assertNotIn("confirmed_script_run", self.action_state)
        self.assertNotIn("money_at_script_run", self.action_state)

    async def test_visible_run_clears_verified_deployment_streak(self):
        self.action_state.update(deployments_without_run=2, last_deployed_filename="home.js")
        self.page.visible = "Bitburner Terminal\n[home /]>"
        result = await self.actions["game_run_script"]("home.js", self.browser, [])
        self.assertIn("Running script home.js with PID 4", result)
        self.assertEqual(self.action_state["deployments_without_run"], 0)
        self.assertNotIn("last_deployed_filename", self.action_state)

    async def test_pending_deployment_blocks_unrelated_terminal_commands_until_visible_run(self):
        self.action_state.update(deployments_without_run=1, last_deployed_filename="home.js")
        blocked = await self.actions["game_terminal"]("ps", self.browser)
        self.assertTrue(blocked.startswith("NO_PROGRESS:"))
        self.assertIn("game_run_script('home.js'", blocked)
        self.assertEqual(self.page.executed_commands, [])

        self.page.visible = "Bitburner Terminal\n[home /]>"
        self.page.run_output = "Bitburner Terminal\n[home /]> run home.js\nRunning script home.js with PID 4"
        result = await self.actions["game_run_script"]("home.js", self.browser, [])
        self.assertIn("Running script home.js with PID 4", result)
        self.assertEqual(self.page.executed_commands, ["run home.js"])
        self.assertEqual(self.action_state["deployments_without_run"], 0)

    async def test_pending_deployment_opens_hidden_terminal_before_validating_and_running(self):
        self.action_state.update(deployments_without_run=1, last_deployed_filename="hack.js")
        self.page.terminal_visible = False
        self.page.visible = "Bitburner Overview with no Terminal prompt"
        self.page.run_output = "Bitburner Terminal\n[home /]> run hack.js\nRunning script hack.js with PID 7"

        result = await self.actions["game_run_script"]("hack.js", self.browser, [], expected_host="home")

        self.assertIn("Running script hack.js with PID 7", result)
        self.assertTrue(self.page.terminal_visible)
        self.assertEqual(self.page.executed_commands, ["run hack.js"])
        self.assertEqual(self.action_state["deployments_without_run"], 0)

    async def test_pending_run_accepts_host_split_across_visible_dom_lines(self):
        self.action_state.update(deployments_without_run=1, last_deployed_filename="hack.js")
        self.page.visible = "Overview\nhome\n\t]>"
        self.page.run_output = "Bitburner Terminal\n[home /]> run hack.js\nRunning script hack.js with PID 8"

        result = await self.actions["game_run_script"]("hack.js", self.browser, [], expected_host="home")

        self.assertIn("Running script hack.js with PID 8", result)
        self.assertEqual(self.page.executed_commands, ["run hack.js"])

    async def test_pending_deployment_cannot_run_from_non_home_server(self):
        self.action_state.update(deployments_without_run=1, last_deployed_filename="home.js")
        self.page.visible = "Bitburner Terminal\n[n00dles /]>"
        result = await self.actions["game_run_script"]("home.js", self.browser, [])
        self.assertTrue(result.startswith("NO_PROGRESS:"))
        self.assertIn("Connect home", result)
        self.assertEqual(self.page.executed_commands, [])

    async def test_changed_deployment_can_run_again_after_prior_positive_pid(self):
        self.page.visible = "Bitburner Terminal\n[home /]>"
        self.page.run_output = "Bitburner Terminal\n[home /]> run hack.js\nRunning script hack.js with PID 4"
        first = await self.actions["game_run_script"]("hack.js", self.browser, [])
        self.assertIn("Running script hack.js", first)
        self.action_state.update(deployments_without_run=1, last_deployed_filename="hack.js")
        self.action_state.pop("last_terminal_command", None)  # successful changed deployment clears this marker
        self.page.run_output = (
            "Bitburner Terminal\n[home /]> run hack.js\nRunning script hack.js with PID 4\n"
            "[home /]> run hack.js\nRunning script hack.js with PID 5"
        )
        second = await self.actions["game_run_script"]("hack.js", self.browser, [])
        self.assertIn("Running script hack.js", second)
        self.assertEqual(self.page.executed_commands, ["run hack.js", "run hack.js"])
        self.assertEqual(self.action_state["deployments_without_run"], 0)

    async def test_terminal_blocks_repeated_run_until_a_diagnostic_command(self):
        first = await self.actions["game_terminal"]("run home.js", self.browser)
        self.assertIn("Running script home.js with PID 4", first)
        duplicate = await self.actions["game_terminal"]("run home.js", self.browser)
        self.assertTrue(duplicate.startswith("NO_PROGRESS:"))
        self.assertEqual(self.page.executed_commands, ["run home.js"])
        await self.actions["game_terminal"]("ps", self.browser)
        second = await self.actions["game_terminal"]("run home.js", self.browser)
        self.assertIn("Running script home.js with PID 4", second)
        self.assertEqual(self.page.executed_commands, ["run home.js", "ps", "run home.js"])

    async def test_terminal_rejects_chaining_downloads_and_deletion(self):
        for command in ("ls; run home.js", "wget https://example.invalid/x.js", "rm home.js"):
            result = await self.actions["game_terminal"](command, self.browser)
            self.assertIn("no chaining, downloads, or deletion", result)

    async def test_terminal_allows_only_documented_in_game_script_copy(self):
        copied = await self.actions["game_terminal"]("scp hack_n00dles.js n00dles", self.browser)
        self.assertIn("File copied to n00dles", copied)
        for command in ("scp home:/hack.js .", "scp ../../hack.js n00dles", "scp hack.js n00dles && run hack.js"):
            result = await self.actions["game_terminal"](command, self.browser)
            self.assertIn("documented in-game copy syntax", result)

    async def test_terminal_visible_usage_error_is_preserved_for_diagnosis(self):
        result = await self.actions["game_terminal"]("scan-analyze n00dles", self.browser)
        self.assertIn("Incorrect usage of scan-analyze", result)

    async def test_progress_is_parsed_from_visible_text_only(self):
        text = "Money: $1.262k\nHack: 1\nScript income: $2.50/s"
        result = visible_progress(text, "$1.262k", 1)
        self.assertIn("Money: $1.262k", result)
        self.assertIn("Hacking level: 1", result)
        self.assertIn("Visible script income: $2.50/s", result)
        self.assertIn("Hacking-level change from baseline: +0", result)
        missing = visible_progress("Terminal is open")
        self.assertIn("unavailable on the current visible screen", missing)

    async def test_offline_progress_amount_is_not_reported_as_player_money(self):
        modal = ("Offline for 57 seconds. While you were offline: "
                 "Your scripts generated $20.199. Hacknet nodes generated $0.000.")
        result = visible_progress(modal, "$71.840k", 156)
        self.assertIn("Money: unavailable on the current visible screen", result)
        self.assertNotIn("Money: $20.199", result)
        self.assertNotIn("Money comparison: current", result)

    async def test_progress_parses_multiline_game_hud_and_money_change(self):
        text = "Overview\nMoney\n[274]<td />\n$1.551k\n[275]<td />\nHack\n[280]<td />"
        result = visible_progress(text, "$1,262.00", 1)
        self.assertIn("Money: $1.551k", result)
        self.assertIn("Money comparison:", result)
        self.assertIn("change +289.00", result)
        self.assertIn("Hacking level is not visible in this view", result)

    async def test_progress_does_not_render_malformed_baseline_as_money_comparison(self):
        result = visible_progress("Overview\nMoney $1.838k\nHack 2", ", ", 1)
        self.assertIn("Money comparison unavailable", result)
        self.assertNotIn("Money comparison: current", result)
        self.assertIn("Hacking-level change from baseline: +1", result)

    async def test_game_progress_uses_session_money_baseline(self):
        self.action_state["initial_visible_money"] = 1262.0
        self.page.visible = "Overview\nMoney\n[274]<td />\n$1.551k\nHack\n[280]<td />"
        result = await self.actions["game_progress"](self.browser)
        self.assertIn("Money: $1.551k", result)
        self.assertIn("change +289.00", result)

    async def test_game_progress_prefers_balance_captured_before_confirmed_run(self):
        self.action_state.update(initial_visible_money=1200.0, confirmed_script_run="earn.js",
                                 money_at_script_run=1262.0)
        self.page.visible = "Overview\nMoney\n$1.551k\nHack\n1"
        result = await self.actions["game_progress"](self.browser)
        self.assertIn("change +289.00", result)
        self.assertNotIn("change +351.00", result)

    async def test_game_progress_rejects_malformed_money_baseline_but_returns_visible_stats(self):
        self.page.visible = "Overview\nMoney\n$1.838k\nHack\n1"
        result = await self.actions["game_progress"](self.browser, baseline_money=", ")
        self.assertTrue(result.startswith("ERROR: baseline_money must be copied as one complete visible currency value"))
        self.assertIn("Money: $1.838k", result)
        self.assertIn("No money comparison was made", result)
        self.assertNotIn("baseline $", result)

    async def test_game_progress_rejects_non_integer_hacking_baseline(self):
        self.page.visible = "Overview\nMoney\n$1.838k\nHack 2"
        result = await self.actions["game_progress"](self.browser, baseline_hacking_level="1")
        self.assertTrue(result.startswith("ERROR: baseline_hacking_level must be a non-negative integer"))
        self.assertIn("Hacking level: 2", result)
        self.assertIn("No hacking-level comparison was made", result)


if __name__ == "__main__":
    unittest.main()
