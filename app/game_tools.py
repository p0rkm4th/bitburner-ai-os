"""Small, visible-UI helpers for repetitive Bitburner operations.

All actions go through the existing Browser Use session and its DOM/keyboard
Actor API. They never inspect game internals, call page.evaluate, or touch saves.
"""
import asyncio
import re
import shlex
from typing import Optional

from browser_use import BrowserSession, Tools


GAME_HOST = "bitburner-official.github.io"
MAX_OBSERVATION = 5200
SCRIPT_NAME = re.compile(r"^[A-Za-z0-9_.-]+\.js$")


async def _page(browser_session: BrowserSession):
    page = await browser_session.get_current_page()
    if page is None:
        raise RuntimeError("No active game tab in the shared Browser Use session")
    url = await page.get_url()
    if GAME_HOST not in url:
        raise RuntimeError(f"Active tab is not the Bitburner game ({url[:160]})")
    return page


async def _visible(browser_session: BrowserSession) -> str:
    snapshot = await browser_session.get_browser_state_summary(include_screenshot=False)
    return snapshot.dom_state.llm_representation()


async def _modal(page) -> Optional[str]:
    """Detect visible modal surfaces and stop before clicking covered controls."""
    selectors = ('[role="dialog"]', '[aria-modal="true"]', '.MuiDialog-root', '.MuiModal-root')
    for selector in selectors:
        for element in await page.get_elements_by_css_selector(selector):
            box = await element.get_bounding_box()
            if box and _box_dimension(box, "width") > 0 and _box_dimension(box, "height") > 0:
                info = await element.get_basic_info()
                attrs = getattr(info, "attributes", None) or (info.get("attributes", {}) if isinstance(info, dict) else {})
                label = attrs.get("aria-label") or attrs.get("role") or selector
                return str(label)[:100]
    return None


async def _need_clear_surface(page) -> None:
    modal = await _modal(page)
    if modal:
        raise RuntimeError(
            f"A visible dialog ({modal}) is covering the game. Inspect and dismiss it with its visible UI control, then retry."
        )


async def _visible_element(page, selectors: tuple[str, ...]):
    for selector in selectors:
        for element in await page.get_elements_by_css_selector(selector):
            box = await element.get_bounding_box()
            if box and _box_dimension(box, "width") > 0 and _box_dimension(box, "height") > 0:
                return element
    return None


def _box_dimension(box, key: str) -> float:
    """Browser Use returns a Pydantic BoundingBox; mocks may return mappings."""
    value = getattr(box, key, None)
    if value is None and isinstance(box, dict):
        value = box.get(key)
    return float(value or 0)


def _visible_content_matches(content: str, visible: str) -> bool:
    """Match source against Monaco's tokenized, index-decorated rendered text."""
    expected = re.sub(r"\s+", "", content)
    rendered = re.sub(r"\[\d+\]", "", visible)
    rendered = re.sub(r"\s+", "", rendered)
    return bool(expected) and expected in rendered


TERMINAL_INPUTS = (
    "#terminal-input",
    'input[aria-label*="terminal" i]',
    'input[placeholder*="command" i]',
    'textarea[aria-label*="terminal" i]',
)
EDITOR_INPUTS = (
    ".monaco-editor textarea.inputarea",
    ".monaco-editor textarea",
    'textarea[aria-label*="editor" i]',
)
EDITOR_SURFACES = (".monaco-editor", '[role="textbox"][aria-label*="editor" i]')
SAVE_BUTTONS = (
    'button[aria-label*="Ctrl + S" i]',
    'button[aria-label*="save" i]',
    'button[title*="save" i]',
    'button[data-testid*="save" i]',
)


def register_game_tools(tools: Tools) -> dict[str, object]:
    """Register a small deterministic tool set on the existing Browser Use controller."""

    @tools.action(description="Return a compact observation of the visible Bitburner UI, including dialogs and visible game state. Does not change the game.")
    async def game_observe(browser_session: BrowserSession) -> str:
        try:
            page = await _page(browser_session)
            visible = await _visible(browser_session)
            modal = await _modal(page)
            prefix = f"Visible dialog: {modal}\n" if modal else "Visible dialog: none\n"
            return prefix + visible[-MAX_OBSERVATION:]
        except Exception as exc:
            return f"ERROR: Could not observe Bitburner UI: {type(exc).__name__}: {exc}"

    async def send_terminal(command: str, browser_session: BrowserSession) -> str:
        if not command.strip() or any(ch in command for ch in "\r\n\x00"):
            raise ValueError("Enter one non-empty terminal command on a single line")
        page = await _page(browser_session)
        await _need_clear_surface(page)
        field = await _visible_element(page, TERMINAL_INPUTS)
        if field is None:
            raise RuntimeError("Terminal input is not visible. Open the in-game Terminal using its visible navigation control, then retry.")
        before = await _visible(browser_session)
        await field.focus()
        await field.fill(command)
        await page.press("Enter")
        await asyncio.sleep(0.25)
        after = await _visible(browser_session)
        if after == before:
            raise RuntimeError("Enter was sent, but the visible game UI did not change. Check terminal focus and inspect the UI before retrying.")
        return after[-MAX_OBSERVATION:]

    @tools.action(description="Focus the visible in-game Bitburner terminal, enter one command, press Enter, and return the rendered result.")
    async def game_terminal(command: str, browser_session: BrowserSession) -> str:
        try:
            return await send_terminal(command, browser_session)
        except Exception as exc:
            return f"ERROR: Terminal command was not verified: {type(exc).__name__}: {exc}"

    @tools.action(description="Open an existing .js script with Bitburner's normal `nano` editor command. Confirms the filename exists in visible `ls` output and the editor opens.")
    async def game_open_editor(filename: str, browser_session: BrowserSession) -> str:
        try:
            if not SCRIPT_NAME.fullmatch(filename):
                raise ValueError("Filename must be a simple in-game .js script name, such as home.js")
            listing = await send_terminal("ls", browser_session)
            if filename not in listing:
                raise RuntimeError(f"{filename} was not present in the visible `ls` result; no editor was opened")
            await send_terminal(f"nano {filename}", browser_session)
            page = await _page(browser_session)
            editor = await _visible_element(page, EDITOR_SURFACES)
            state = await _visible(browser_session)
            if editor is None or filename not in state:
                raise RuntimeError(f"The normal editor transition for {filename} was not visible")
            return f"Opened existing {filename} in the in-game editor.\n{state[-MAX_OBSERVATION:]}"
        except Exception as exc:
            return f"ERROR: Could not open script editor: {type(exc).__name__}: {exc}"

    @tools.action(description="Replace the open in-game editor contents with model-authored Netscript, verify it is visible in the editor, then save through the visible Save control.")
    async def game_edit_script(filename: str, content: str, browser_session: BrowserSession) -> str:
        try:
            if not SCRIPT_NAME.fullmatch(filename):
                raise ValueError("Filename must be a simple in-game .js script name, such as home.js")
            if not content.strip() or len(content) > 30000:
                raise ValueError("Script content must contain 1 to 30,000 characters")
            page = await _page(browser_session)
            await _need_clear_surface(page)
            editor = await _visible_element(page, EDITOR_SURFACES)
            state = await _visible(browser_session)
            if editor is None or filename not in state:
                opened = await game_open_editor(filename, browser_session)
                if opened.startswith("ERROR:"):
                    return opened
                page = await _page(browser_session)
            field = await _visible_element(page, EDITOR_INPUTS)
            if field is None:
                raise RuntimeError("Editor is open, but its visible keyboard input could not be located")
            await field.focus()
            await field.fill(content)
            value = await field.get_attribute("value")
            state = await _visible(browser_session)
            # Monaco's UI renders model text into visible lines; plain textareas expose their value.
            rendered_ok = _visible_content_matches(content, state)
            if value != content and not rendered_ok:
                raise RuntimeError("Editor input did not match the supplied content in the visible editor; script was not saved")
            button = await _visible_element(page, SAVE_BUTTONS)
            if button is None:
                raise RuntimeError("Could not identify a visible Save button by accessible label/title; editor is left open for inspection")
            await button.click()
            await asyncio.sleep(0.25)
            final_state = await _visible(browser_session)
            still_open = await _visible_element(page, EDITOR_SURFACES)
            if still_open is None or filename not in final_state:
                raise RuntimeError("Save control was clicked, but the expected script editor is no longer visible")
            if not _visible_content_matches(content, final_state):
                raise RuntimeError("After saving, the visible editor no longer matches the supplied content")
            return f"Saved {filename}; the editor remains open and its visible contents still match.\n{final_state[-MAX_OBSERVATION:]}"
        except Exception as exc:
            return f"ERROR: Could not verify script edit/save: {type(exc).__name__}: {exc}"

    @tools.action(description="Run an existing Bitburner script through the visible terminal and report the game's rendered confirmation or error.")
    async def game_run_script(filename: str, browser_session: BrowserSession,
                              args: Optional[list[str]] = None) -> str:
        try:
            if not SCRIPT_NAME.fullmatch(filename):
                raise ValueError("Filename must be a simple in-game .js script name, such as home.js")
            args = args or []
            if len(args) > 16 or any(any(ch in arg for ch in "\r\n\x00") for arg in args):
                raise ValueError("Use at most 16 single-line script arguments")
            command = "run " + shlex.quote(filename)
            if args:
                command += " " + " ".join(shlex.quote(arg) for arg in args)
            state = await send_terminal(command, browser_session)
            result = state.casefold()
            if filename.casefold() not in result or not re.search(r"running script|pid\s*[:#]?\s*\d+|error|ram", result):
                raise RuntimeError(f"No visible run confirmation or game error for {filename}; inspect UI before retrying\n{state[-1200:]}")
            return state
        except Exception as exc:
            return f"ERROR: Script execution was not confirmed: {type(exc).__name__}: {exc}"

    return {
        "game_observe": game_observe,
        "game_terminal": game_terminal,
        "game_open_editor": game_open_editor,
        "game_edit_script": game_edit_script,
        "game_run_script": game_run_script,
    }
