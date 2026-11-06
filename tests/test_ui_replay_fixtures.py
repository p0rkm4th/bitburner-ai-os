"""Deterministic offline replays grounded in saved Bitburner UI observations.

No browser, game profile, model inference, or network access is used here.
"""
import json
from pathlib import Path
import unittest
from types import SimpleNamespace

from app.game_tools import find_visible_tab_node, register_game_tools
from tests.test_game_tools import FakeBrowserSession, FakeNavNode, FakePage, FakeTools


FIXTURES = json.loads((Path(__file__).parent / "fixtures/ui_action_replays.json").read_text())


class RecordedClickPage(FakePage):
    """Fake page that records which fresh backend node the helper clicked."""
    def __init__(self):
        super().__init__()
        self.clicked_backend_ids = []

    async def get_element(self, backend_node_id):
        self.clicked_backend_ids.append(backend_node_id)
        self.nav_label = next(
            node.label for node in self.nav_nodes if node.backend_node_id == backend_node_id
        )
        return await super().get_element(backend_node_id)


class UIActionReplayTests(unittest.IsolatedAsyncioTestCase):
    def setUp(self):
        self.cases = {item["id"]: item for item in FIXTURES["cases"]}

    def nav_nodes(self, replay_case):
        # Rebuild current observation with backend IDs unrelated to the stale index.
        return [FakeNavNode(label, backend_node_id=700 + i)
                for i, label in enumerate(replay_case["observation"]["visible_navigation_labels"])]

    async def test_stale_index_replay_reacquires_semantic_target_once(self):
        case = self.cases["stale-script-editor-index"]
        page = RecordedClickPage()
        page.nav_nodes = self.nav_nodes(case)
        browser = FakeBrowserSession(page)
        actions = register_game_tools(FakeTools())

        fresh_state = await browser.get_browser_state_summary()
        target = find_visible_tab_node(fresh_state.dom_state, case["observation"]["requested_label"])
        result = await actions["game_open_tab"](case["observation"]["requested_label"], browser)

        self.assertIn("Opened visible game tab 'Script Editor'", result)
        self.assertEqual(page.clicked_backend_ids, [target.backend_node_id])
        self.assertNotEqual(page.clicked_backend_ids[0], case["observation"]["prior_stale_index"])
        self.assertEqual(page.visible, "Script Editor page opened")
        self.assertEqual(case["observation"]["repeated_stale_index_errors_in_trace"], 5)

    async def test_wrong_target_replay_uses_requested_visible_label(self):
        case = self.cases["wrong-achievements-target"]
        page = RecordedClickPage()
        page.nav_nodes = self.nav_nodes(case)
        browser = FakeBrowserSession(page)
        actions = register_game_tools(FakeTools())

        result = await actions["game_open_tab"](case["observation"]["requested_label"], browser)

        self.assertIn("Opened visible game tab 'Script Editor'", result)
        self.assertEqual(len(page.clicked_backend_ids), 1)
        self.assertEqual(page.visible, "Script Editor page opened")
        self.assertEqual(case["observation"]["observed_wrong_target_repetitions"], 2)

    async def test_runtime_dialog_replay_preserves_error_and_closes_once(self):
        case = self.cases["runtime-error-dialog-blocks-terminal"]
        page = FakePage()
        page.modal = True
        page.mui_modal = True
        page.presentation_only = True
        page.visible = case["observation"]["visible_dialog_text"]
        browser = FakeBrowserSession(page)
        actions = register_game_tools(FakeTools())

        blocked = await actions["game_terminal"]("ps", browser)

        self.assertIn("RUNTIME ERROR", blocked)
        self.assertIn("Cannot hack foodnstuff", blocked)
        self.assertIn("requested action was not performed", blocked)
        self.assertEqual(page.close_clicks, 1)
        self.assertEqual(page.executed_commands, [])
        self.assertFalse(page.modal)

        # A fresh, deliberate call after the dialog is gone succeeds once; helper
        # does not loop or replay the blocked command itself.
        result = await actions["game_terminal"]("ps", browser)
        self.assertIn("PID Filename", result)
        self.assertEqual(page.executed_commands, ["ps"])


if __name__ == "__main__":
    unittest.main()
