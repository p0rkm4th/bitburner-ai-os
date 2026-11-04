"""Integration-style tests for registered actions over a fake visible Browser Use page."""
import unittest
from types import SimpleNamespace

from app.game_tools import _visible_content_matches, register_game_tools


class FakeElement:
    def __init__(self, page, kind):
        self.page = page
        self.kind = kind

    async def get_bounding_box(self):
        if self.kind == "modal" and not self.page.modal:
            return None
        if self.kind in {"editor", "editor_input", "save"} and not self.page.editor:
            return None
        if self.kind == "terminal" and self.page.editor:
            return None
        return SimpleNamespace(x=1, y=1, width=200, height=24)

    async def get_basic_info(self):
        return SimpleNamespace(attributes={"role": "dialog"})

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
        if self.kind == "save":
            self.page.saved_text = self.page.editor_text


class FakePage:
    def __init__(self):
        self.url = "https://bitburner-official.github.io/"
        self.editor = False
        self.modal = False
        self.command = ""
        self.editor_text = ""
        self.saved_text = ""
        self.focused = None
        self.run_output = None
        self.visible = "Bitburner Terminal"
        self.files = {"home.js": "export async function main(ns) {}"}

    async def get_url(self):
        return self.url

    async def get_elements_by_css_selector(self, selector):
        if selector in ('[role="dialog"]', '[aria-modal="true"]', '.MuiDialog-root', '.MuiModal-root'):
            return [FakeElement(self, "modal")] if self.modal else []
        if selector in (".monaco-editor", '[role="textbox"][aria-label*="editor" i]'):
            return [FakeElement(self, "editor")] if self.editor else []
        if selector in (".monaco-editor textarea.inputarea", ".monaco-editor textarea", 'textarea[aria-label*="editor" i]'):
            return [FakeElement(self, "editor_input")] if self.editor else []
        if selector in ('button[aria-label*="Ctrl + S" i]', 'button[aria-label*="save" i]', 'button[title*="save" i]', 'button[data-testid*="save" i]'):
            return [FakeElement(self, "save")] if self.editor else []
        if selector in ("#terminal-input", 'input[aria-label*="terminal" i]', 'input[placeholder*="command" i]', 'textarea[aria-label*="terminal" i]'):
            return [FakeElement(self, "terminal")] if not self.editor else []
        return []

    async def press(self, key):
        if key.casefold() in ("control+s", "ctrl+s") and self.editor:
            self.saved_text = self.editor_text
            return
        if key != "Enter" or self.focused != "terminal":
            return
        command = self.command
        if command == "ls":
            self.visible = "Bitburner Terminal\n" + " ".join(self.files)
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
        else:
            self.visible = f"Bitburner Terminal\n{command}\nCommand accepted"


class FakeSnapshot:
    def __init__(self, text):
        self.dom_state = self
        self.text = text

    def llm_representation(self):
        return self.text


class FakeBrowserSession:
    def __init__(self, page):
        self.page = page

    async def get_current_page(self):
        return self.page

    async def get_browser_state_summary(self, include_screenshot=False):
        return FakeSnapshot(self.page.visible)


class FakeTools:
    def action(self, description=""):
        def decorate(fn):
            return fn
        return decorate


class GameToolIntegrationTests(unittest.IsolatedAsyncioTestCase):
    async def asyncSetUp(self):
        self.page = FakePage()
        self.browser = FakeBrowserSession(self.page)
        self.actions = register_game_tools(FakeTools())

    async def test_observe_and_terminal_round_trip(self):
        state = await self.actions["game_observe"](self.browser)
        self.assertIn("Visible dialog: none", state)
        result = await self.actions["game_terminal"]("ls", self.browser)
        self.assertIn("home.js", result)

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


if __name__ == "__main__":
    unittest.main()
