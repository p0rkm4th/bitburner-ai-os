"""Integration-style tests for registered actions over a fake visible Browser Use page."""
import unittest
from types import SimpleNamespace

from app.game_tools import _visible_content_matches, find_visible_tab_node, register_game_tools, visible_progress


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
        if self.kind == "modal_close":
            self.page.close_clicks += 1
            if self.page.modal_button_count == 1:
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
        self.close_clicks = 0
        self.command = ""
        self.editor_text = ""
        self.saved_text = ""
        self.focused = None
        self.terminal_visible = True
        self.run_output = None
        self.executed_commands = []
        self.visible = "Bitburner Terminal"
        self.files = {"home.js": "export async function main(ns) {}"}
        self.nav_label = "Create Program"
        self.nav_nodes = []

    async def get_url(self):
        return self.url

    async def get_element(self, backend_node_id):
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
            self.visible = "Bitburner Terminal\nterminal-input"
            return
        if key != "Enter" or self.focused != "terminal":
            return
        command = self.command
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
        elif command == "ps":
            self.visible = "Bitburner Terminal\nps\nPID Filename\n4 home.js"
        elif command.startswith("scp "):
            self.visible = f"Bitburner Terminal\n{command}\nFile copied to {command.split()[-1]}"
        elif command.startswith("scan-analyze ") and command != "scan-analyze 2":
            self.visible = f"Bitburner Terminal\n{command}\nIncorrect usage of scan-analyze command. depth argument must be positive numeric"
        else:
            self.visible = f"Bitburner Terminal\n{command}\nCommand accepted"


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
        return FakeSnapshot(self.page)


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

    async def test_identical_observation_is_reported_as_no_progress(self):
        first = await self.actions["game_observe"](self.browser)
        repeated = await self.actions["game_observe"](self.browser)
        self.assertIn("Visible dialog: none", first)
        self.assertTrue(repeated.startswith("NO_PROGRESS:"))
        self.page.visible = "Bitburner Terminal\nA different visible screen"
        changed = await self.actions["game_observe"](self.browser)
        self.assertIn("A different visible screen", changed)

    async def test_open_tab_reacquires_visible_label_and_verifies_transition(self):
        self.page.nav_nodes = [FakeNavNode("Create Program")]
        result = await self.actions["game_open_tab"]("Create Program", self.browser)
        self.assertIn("Opened visible game tab 'Create Program'", result)
        self.assertEqual(self.page.visible, "Create Program page opened")

    async def test_open_tab_rejects_unknown_or_ambiguous_navigation_targets(self):
        unknown = await self.actions["game_open_tab"]("Arbitrary URL", self.browser)
        self.assertIn("allowlisted", unknown)
        self.page.nav_nodes = [FakeNavNode("Stats", 1), FakeNavNode("Stats", 2)]
        ambiguous = await self.actions["game_open_tab"]("Stats", self.browser)
        self.assertIn("exactly one fresh visible navigation button", ambiguous)

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
        self.page.visible = "RUNTIME ERROR\nscript crashed\nScript: home.js\nPID: 1"
        result = await self.actions["game_terminal"]("ps", self.browser)
        self.assertTrue(result.startswith("NO_PROGRESS:"))
        self.assertIn("RUNTIME ERROR", result)
        self.assertIn("requested action was not performed", result)
        self.assertFalse(self.page.modal)
        self.assertEqual(self.page.executed_commands, [])

    async def test_terminal_rejects_same_command_repeat_without_sending_it(self):
        first = await self.actions["game_terminal"]("help", self.browser)
        second = await self.actions["game_terminal"]("help", self.browser)
        self.assertIn("Command accepted", first)
        self.assertTrue(second.startswith("NO_PROGRESS:"))
        self.assertIn("repeat was not sent", second)
        self.assertEqual(self.page.executed_commands, ["help"])

    async def test_terminal_preserves_and_marks_visible_ram_error(self):
        self.page.run_output = (
            "Bitburner Terminal\n[home /]> run home.js\n"
            "Cannot run home.js (t=1) on home. This script requires 81.60GB of RAM."
        )
        result = await self.actions["game_terminal"]("run home.js", self.browser)
        self.assertTrue(result.startswith("VISIBLE GAME ERROR (verbatim):"))
        self.assertIn("requires 81.60GB of RAM", result)

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
        self.assertFalse(self.page.modal)

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

    async def test_visible_run_clears_verified_deployment_streak(self):
        self.action_state.update(deployments_without_run=2, last_deployed_filename="home.js")
        result = await self.actions["game_run_script"]("home.js", self.browser, [])
        self.assertIn("Running script home.js with PID 4", result)
        self.assertEqual(self.action_state["deployments_without_run"], 0)
        self.assertNotIn("last_deployed_filename", self.action_state)

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


if __name__ == "__main__":
    unittest.main()
