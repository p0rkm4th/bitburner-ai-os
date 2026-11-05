"""Small, visible-UI helpers for repetitive Bitburner operations.

All actions go through the existing Browser Use session and its DOM/keyboard
Actor API. They never inspect game internals, call page.evaluate, or touch saves.
"""
import asyncio
import hashlib
import re
import shlex
from typing import Optional

from browser_use import BrowserSession, Tools


GAME_HOST = "bitburner-official.github.io"
MAX_OBSERVATION = 2800
SCRIPT_NAME = re.compile(r"^[A-Za-z0-9_.-]+\.js$")
GAME_TABS = {
    "terminal", "script editor", "active scripts", "create program", "stats",
    "hacknet", "city", "travel", "milestones", "documentation",
}


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


def _known_game_modal(visible: str) -> bool:
    text = visible.casefold()
    return (("offline for" in text and "your scripts generated" in text)
            or ("message received from" in text and "message was saved" in text)
            or ("runtime error" in text and "script:" in text and "pid:" in text))


def visible_runtime_error(visible: str) -> str:
    """Return a bounded runtime-error excerpt from rendered Bitburner UI text."""
    match = re.search(r"\bRUNTIME\s+ERROR\b", visible, re.IGNORECASE)
    if not match:
        return ""
    excerpt = visible[match.start():match.start() + 700]
    excerpt = re.sub(r"\[\d+\]", "", excerpt)
    return excerpt.strip()


async def _modal(page, visible: str = "") -> Optional[str]:
    """Detect visible modal surfaces and stop before clicking covered controls."""
    selectors = ('[role="dialog"]', '[aria-modal="true"]', '.MuiDialog-root', '.MuiModal-root')
    for selector in selectors:
        for element in await page.get_elements_by_css_selector(selector):
            box = await element.get_bounding_box()
            if box and _box_dimension(box, "width") > 0 and _box_dimension(box, "height") > 0:
                info = await element.get_basic_info()
                attrs = getattr(info, "attributes", None) or (info.get("attributes", {}) if isinstance(info, dict) else {})
                role = str(attrs.get("role", "")).casefold()
                if attrs.get("aria-hidden") == "true":
                    continue
                # The game can retain an empty aria-modal presentation shell
                # after closing a popup. Count it only while it still contains
                # a visible interactive control and recognizable visible game
                # content. The jump3R message uses this presentation shell.
                if role == "presentation":
                    # Accessibility snapshots can expose a generic modal shell
                    # even when no dialog is open. Only Bitburner's known modal
                    # presentation qualifies; do not infer a dialog merely
                    # because the shell contains a button.
                    if selector != ".MuiModal-root" or not _known_game_modal(visible):
                        continue
                    controls = await page.get_elements_by_css_selector(
                        '[aria-modal="true"] button, [aria-modal="true"] [role="button"], '
                        '.MuiModal-root button, .MuiModal-root [role="button"]'
                    )
                    visible_controls = []
                    for control in controls:
                        control_box = await control.get_bounding_box()
                        if control_box and _box_dimension(control_box, "width") > 0 and _box_dimension(control_box, "height") > 0:
                            visible_controls.append(control)
                    if not visible_controls:
                        continue
                label = attrs.get("aria-label") or role or selector
                return str(label)[:100]
    return None


async def _need_clear_surface(page, browser_session: BrowserSession) -> None:
    visible = await _visible(browser_session)
    modal = await _modal(page, visible)
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


RUN_COMMAND = re.compile(r"^\s*run\s+([A-Za-z0-9_.-]+\.js)(?:\s+.*)?$", re.IGNORECASE)
CONFIRMED_RUN = re.compile(r"running script.*\bpid\s*[:#]?\s*[1-9]\d*", re.IGNORECASE)
IN_GAME_SCP = re.compile(r"^scp\s+[A-Za-z0-9_.-]+\.js\s+[A-Za-z0-9_.-]+$", re.IGNORECASE)


def find_visible_tab_node(dom_state, tab: str):
    """Find one freshly observed visible navigation button by its rendered label."""
    matches = []
    for node in getattr(dom_state, "selector_map", {}).values():
        attrs = getattr(node, "attributes", {}) or {}
        if str(attrs.get("role", "")).casefold() != "button" or not getattr(node, "is_visible", False):
            continue
        label = " ".join(str(node.get_all_children_text()).split()).casefold()
        if label == tab.casefold():
            matches.append(node)
    return matches[0] if len(matches) == 1 else None


def find_visible_close_node(dom_state):
    """Find a unique freshly observed visible button with the exact label Close."""
    matches = []
    for node in getattr(dom_state, "selector_map", {}).values():
        attrs = getattr(node, "attributes", {}) or {}
        if str(attrs.get("role", "")).casefold() != "button" or not getattr(node, "is_visible", False):
            continue
        label = " ".join(str(node.get_all_children_text()).split()).casefold()
        if label == "close":
            matches.append(node)
    return matches[0] if len(matches) == 1 else None


def visible_progress(visible: str, baseline_money: Optional[str] = None,
                     baseline_hacking_level: Optional[int] = None) -> str:
    """Extract only game stats rendered in the visible DOM; never inspect game objects."""
    money = re.search(r"\bMoney\b[^$\n]{0,40}\$\s*([\d,.]+\s*[kmbt]?)", visible, re.IGNORECASE)
    hacking = re.search(r"\b(?:Hack|Hacking(?:\s+Level)?)\b\s*:?\s*(\d+)\b", visible, re.IGNORECASE)
    income = re.search(r"\b(?:script\s+)?(?:income|profit|production)\b[^$\n]{0,40}\$\s*([\d,.]+\s*[kmbt]?)\s*(?:/\s*s|per\s+second)",
                       visible, re.IGNORECASE)
    lines = ["Visible gameplay stats (DOM text only):",
             f"Money: ${money.group(1).strip()}" if money else "Money: unavailable on the current visible screen",
             f"Hacking level: {hacking.group(1)}" if hacking else "Hacking level: unavailable on the current visible screen",
             f"Visible script income: ${income.group(1).strip()}/s" if income else "Visible script income: unavailable on the current screen"]
    if money and baseline_money is not None:
        lines.append(f"Money comparison: current ${money.group(1).strip()}, baseline ${baseline_money}")
    if hacking and baseline_hacking_level is not None:
        delta = int(hacking.group(1)) - baseline_hacking_level
        lines.append(f"Hacking-level change from baseline: {delta:+d}")
    lines.append("Use the returned rendered UI text to inspect Active Scripts and script output; no hidden game state was read.")
    return "\n".join(lines)


TERMINAL_INPUTS = (
    "#terminal-input",
    'input[aria-label*="terminal" i]',
    'input[placeholder*="command" i]',
    'textarea[aria-label*="terminal" i]',
)
SEMANTIC_CLOSE_CONTROLS = (
    '.MuiModal-root button[class*="closeButton"]',
    '[role="dialog"] button[aria-label*="close" i]',
    '[aria-modal="true"] button[aria-label*="close" i]',
    '[role="dialog"] [role="button"][aria-label*="dismiss" i]',
    '[aria-modal="true"] [role="button"][aria-label*="dismiss" i]',
    '[role="dialog"] button[title*="close" i]',
    '[aria-modal="true"] button[title*="close" i]',
)
MODAL_BUTTONS = ('[aria-modal="true"] button', '[aria-modal="true"] [role="button"]',
                 '[role="dialog"] button', '[role="dialog"] [role="button"]',
                 '.MuiModal-root button', '.MuiModal-root [role="button"]')
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


async def _dismiss_dialog_once(browser_session: BrowserSession) -> str:
    """Dismiss one visible dialog using a fresh, visible control and verify the transition."""
    page = await _page(browser_session)
    before_state = await _visible(browser_session)
    modal = await _modal(page, before_state)
    if not modal:
        return "No visible dialog was detected; no input was sent."
    close = await _visible_element(page, SEMANTIC_CLOSE_CONTROLS)
    if close is not None:
        await close.click()
    else:
        summary = await browser_session.get_browser_state_summary(include_screenshot=False)
        close_node = find_visible_close_node(summary.dom_state)
        if close_node is not None:
            close = await page.get_element(close_node.backend_node_id)
            await close.click()
        else:
            modal_buttons = []
            for selector in MODAL_BUTTONS:
                found = []
                for button in await page.get_elements_by_css_selector(selector):
                    box = await button.get_bounding_box()
                    if box and _box_dimension(box, "width") > 0 and _box_dimension(box, "height") > 0:
                        found.append(button)
                if found:
                    modal_buttons = found
                    break
            if len(modal_buttons) == 1:
                await modal_buttons[0].click()
            else:
                await page.press("Escape")
    await asyncio.sleep(0.15)
    state = await _visible(browser_session)
    remaining = await _modal(page, state)
    if remaining:
        return (f"ERROR: Dialog ({remaining}) remains after one close attempt. "
                "Inspect the visible UI and report the blocker; no further input was sent.\n" +
                state[-MAX_OBSERVATION:])
    return "Dialog dismissed and verified absent.\n" + state[-MAX_OBSERVATION:]


def _dialog_signature(modal: Optional[str], visible: str) -> str:
    """Fingerprint the same visible blocker without relying on element indexes."""
    excerpt = visible_runtime_error(visible) or visible[-900:]
    normalized = re.sub(r"\[\d+\]", "", excerpt)
    normalized = re.sub(r"\bPID:\s*\S+", "PID", normalized, flags=re.IGNORECASE)
    normalized = re.sub(r"\s+", " ", normalized).strip().casefold()
    return hashlib.sha256(f"{modal or ''}|{normalized}".encode()).hexdigest()


async def _clear_known_modal_before_action(browser_session: BrowserSession, action: str) -> Optional[str]:
    """Close only recognized game notices; return their visible text without doing the requested action."""
    page = await _page(browser_session)
    visible = await _visible(browser_session)
    modal = await _modal(page, visible)
    if not modal:
        return None
    if not _known_game_modal(visible):
        raise RuntimeError(f"A visible dialog ({modal}) is covering the game. Inspect and dismiss it with its visible UI control, then retry.")
    body = visible[-MAX_OBSERVATION:]
    result = await _dismiss_dialog_once(browser_session)
    if not result.startswith("Dialog dismissed and verified absent"):
        raise RuntimeError(result)
    return (f"NO_PROGRESS: A recognized Bitburner dialog was dismissed before {action}; the requested action was not performed. "
            "Read the visible dialog text, then choose the next action.\nDialog content:\n" + body + "\n" + result)


def register_game_tools(tools: Tools, *, include_editor: bool = True,
                        action_state: Optional[dict] = None) -> dict[str, object]:
    """Register a small deterministic tool set on the existing Browser Use controller."""
    action_state = action_state if action_state is not None else {}
    last_observation: Optional[str] = None
    last_confirmed_run: Optional[str] = None

    @tools.action(description="Return a compact observation of the visible Bitburner UI, including dialogs and visible game state. Does not change the game.")
    async def game_observe(browser_session: BrowserSession) -> str:
        nonlocal last_observation
        try:
            page = await _page(browser_session)
            visible = await _visible(browser_session)
            if last_observation == visible:
                return ("NO_PROGRESS: This rendered observation is identical to the previous one; no input was sent. "
                        "Choose one different action based on the visible state, or report the blocker instead of observing again.")
            last_observation = visible
            modal = await _modal(page, visible)
            prefix = f"Visible dialog: {modal}\n" if modal else "Visible dialog: none\n"
            return prefix + visible[-MAX_OBSERVATION:]
        except Exception as exc:
            return f"ERROR: Could not observe Bitburner UI: {type(exc).__name__}: {exc}"

    @tools.action(description=(
        "Report money, hacking level, and visible script income from the rendered game UI only. "
        "Optionally compare money text and hacking level with a previous observation; no hidden game state is read."
    ))
    async def game_progress(browser_session: BrowserSession, baseline_money: Optional[str] = None,
                            baseline_hacking_level: Optional[int] = None) -> str:
        try:
            await _page(browser_session)
            visible = await _visible(browser_session)
            return visible_progress(visible, baseline_money, baseline_hacking_level) + "\n\n" + visible[-1800:]
        except Exception as exc:
            return f"ERROR: Could not verify visible gameplay progress: {type(exc).__name__}: {exc}"

    @tools.action(description=(
        "Open one allowlisted Bitburner navigation tab by matching its freshly observed visible button label. "
        "Allowed: Terminal, Script Editor, Active Scripts, Create Program, Stats, Hacknet, City, Travel, "
        "Milestones, Documentation. Does not use stored element indexes."
    ))
    async def game_open_tab(tab: str, browser_session: BrowserSession) -> str:
        try:
            label = " ".join(tab.split())
            if label.casefold() not in GAME_TABS:
                raise ValueError("Unknown game tab. Use one of the allowlisted visible tab names in the tool description.")
            page = await _page(browser_session)
            blocked = await _clear_known_modal_before_action(browser_session, f"opening {label!r}")
            if blocked:
                return blocked
            before = await browser_session.get_browser_state_summary(include_screenshot=False)
            node = find_visible_tab_node(before.dom_state, label)
            if node is None:
                raise RuntimeError(f"Could not identify exactly one fresh visible navigation button labelled {label!r}")
            element = await page.get_element(node.backend_node_id)
            await element.click()
            await asyncio.sleep(0.15)
            after = await _visible(browser_session)
            if after == before.dom_state.llm_representation():
                raise RuntimeError(f"Clicked {label!r}, but the rendered game UI did not change")
            if label.casefold() == "active scripts" and action_state.get("ram_rejection"):
                action_state["ram_rejection"]["diagnosed"] = True
            return f"Opened visible game tab {label!r}.\n{after[-MAX_OBSERVATION:]}"
        except Exception as exc:
            return f"ERROR: Could not open Bitburner tab: {type(exc).__name__}: {exc}"

    @tools.action(description=(
        "Dismiss one visible in-game dialog using its accessible close control, a unique visible button inside the modal, or Escape, then verify it is gone. "
        "If it remains, report the blocker; do not retry blindly."
    ))
    async def game_dismiss_dialog(browser_session: BrowserSession) -> str:
        signature = None
        try:
            page = await _page(browser_session)
            before = await _visible(browser_session)
            modal = await _modal(page, before)
            if not modal:
                action_state.pop("failed_dialog_signature", None)
                return "No visible dialog was detected; no input was sent."
            signature = _dialog_signature(modal, before)
            if action_state.get("failed_dialog_signature") == signature:
                return ("NO_PROGRESS: The same visible dialog remains after one close attempt. "
                        "No input was sent. Read the dialog and report the exact blocker; do not retry dismissal.")
            result = await _dismiss_dialog_once(browser_session)
            if result.startswith("Dialog dismissed and verified absent") or "No visible dialog was detected" in result:
                action_state.pop("failed_dialog_signature", None)
            else:
                action_state["failed_dialog_signature"] = signature
            return result
        except Exception as exc:
            if signature:
                action_state["failed_dialog_signature"] = signature
            return f"ERROR: Could not dismiss visible dialog: {type(exc).__name__}: {exc}"

    async def _ensure_terminal(page, browser_session: BrowserSession):
        field = await _visible_element(page, TERMINAL_INPUTS)
        if field is not None:
            return page, field
        # Alt+T is the documented in-game Terminal shortcut. Reacquire the page
        # and input after navigation so no stale element handle is reused.
        await page.press("Alt+t")
        await asyncio.sleep(0.15)
        page = await _page(browser_session)
        field = await _visible_element(page, TERMINAL_INPUTS)
        if field is None:
            raise RuntimeError("Terminal input is still not visible after the documented Alt+T shortcut; inspect the game UI")
        return page, field

    async def send_terminal(command: str, browser_session: BrowserSession) -> str:
        nonlocal last_confirmed_run
        normalized_command = command.strip()
        if (not command.strip() or len(command) > 500 or
                any(ch in command for ch in "\r\n\x00;") or normalized_command.casefold().startswith(("wget ", "rm "))):
            raise ValueError("Enter one permitted, non-empty game Terminal command on a single line (no chaining, downloads, or deletion)")
        if normalized_command.casefold().startswith("scp ") and not IN_GAME_SCP.fullmatch(normalized_command):
            raise ValueError("Use the documented in-game copy syntax `scp filename.js server` with a simple .js filename and server name")
        run_match = RUN_COMMAND.fullmatch(command)
        run_filename = run_match.group(1).casefold() if run_match else None
        page = await _page(browser_session)
        blocked = await _clear_known_modal_before_action(browser_session, f"running terminal command {normalized_command!r}")
        if blocked:
            return blocked
        if run_filename and run_filename == last_confirmed_run:
            return (f"NO_PROGRESS: {run_match.group(1)} already received a visible positive PID. "
                    "Do not run it again yet. Inspect `ps`, `tail`, Active Scripts, or the visible error and act on that evidence.")
        if normalized_command.casefold() == action_state.get("last_terminal_command"):
            return (f"NO_PROGRESS: The same Terminal command ({normalized_command}) was already executed with no intervening "
                    "Terminal action. Choose a different diagnostic or gameplay action; this repeat was not sent.")
        page, field = await _ensure_terminal(page, browser_session)
        before = await _visible(browser_session)
        await field.focus()
        await field.fill(command)
        await page.press("Enter")
        await asyncio.sleep(0.25)
        after = await _visible(browser_session)
        # Bitburner starts Netscript asynchronously. A positive PID can be
        # followed almost immediately by a runtime-error modal, so sample the
        # same visible UI briefly before reporting that the run only started.
        # This is ordinary rendered UI observation; it does not inspect game
        # objects or change the script.
        if run_filename and CONFIRMED_RUN.search(after):
            for _ in range(4):
                await asyncio.sleep(0.25)
                observed = await _visible(browser_session)
                runtime_error = visible_runtime_error(observed)
                if runtime_error:
                    after = observed
                    break
        if after == before:
            raise RuntimeError("Enter was sent, but the visible game UI did not change. Check terminal focus and inspect the UI before retrying.")
        if run_filename and run_filename == str(action_state.get("last_deployed_filename", "")).casefold():
            action_state["deployments_without_run"] = 0
            action_state.pop("last_deployed_filename", None)
        action_state["last_terminal_command"] = normalized_command.casefold()
        if not run_filename:
            # A successfully executed diagnostic command permits a later
            # deliberate relaunch after the positive PID check.
            last_confirmed_run = None
        ram_error = re.search(
            r"Cannot run\s+([A-Za-z0-9_.-]+\.js)\s+\(t=\d+\)\s+on\s+([A-Za-z0-9_.-]+)\.\s+This script requires\s+([\d.]+)\s*GB of RAM",
            after, re.IGNORECASE,
        )
        if ram_error:
            action_state["ram_rejection"] = {
                "filename": ram_error.group(1).casefold(),
                "host": ram_error.group(2),
                "required_ram": ram_error.group(3),
                "diagnosed": False,
            }
        elif (action_state.get("ram_rejection") and
              re.fullmatch(r"\s*(?:ps|mem\s+[A-Za-z0-9_.-]+\.js)\s*", normalized_command, re.IGNORECASE)):
            action_state["ram_rejection"]["diagnosed"] = True
        if run_filename and CONFIRMED_RUN.search(after):
            action_state.pop("ram_rejection", None)
            last_confirmed_run = run_filename
            action_state["confirmed_script_run"] = run_filename
        return after[-MAX_OBSERVATION:]

    @tools.action(description=(
        "Focus the visible in-game Bitburner terminal, enter one command, press Enter, and return the rendered result. "
        "Recognized offline-progress, message, and script runtime-error dialogs are dismissed once before acting; in that case the command is not sent and their visible text is returned. "
        "An identical consecutive Terminal command is rejected as NO_PROGRESS. "
        "Use `scp filename.js server` only for the documented in-game copy operation; it cannot access the host filesystem. "
        "Use `cat filename.txt` to inspect a simple in-game text report that the script-only Remote API cannot read."
    ))
    async def game_terminal(command: str, browser_session: BrowserSession) -> str:
        try:
            result = await send_terminal(command, browser_session)
            # Preserve the game's exact rendered error while making it
            # unambiguous to the model that this was a failed game action.
            error_patterns = (
                r"(?im)^\s*(?:Cannot run .*?requires .*? RAM|not enough RAM|insufficient RAM)",
                r"(?im)^\s*(?:Incorrect usage|Command .+ not found|ERROR:|Runtime error:|Cannot .+)",
                r"(?im)^\s*.*(?:does not have root access|cannot hack this server yet|requires root access).*$",
            )
            if any(re.search(pattern, result) for pattern in error_patterns):
                return "VISIBLE GAME ERROR (verbatim):\n" + result
            return result
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
            await _need_clear_surface(page, browser_session)
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

    @tools.action(description=(
        "Run an existing Bitburner script through the visible terminal and report the game's rendered confirmation or error. "
        "After a positive PID, briefly rechecks the rendered UI for an immediate Netscript runtime-error dialog. A PID alone is not success."
    ))
    async def game_run_script(filename: str, browser_session: BrowserSession,
                              args: Optional[list[str]] = None) -> str:
        try:
            if not SCRIPT_NAME.fullmatch(filename):
                raise ValueError("Filename must be a simple in-game .js script name, such as home.js")
            args = args or []
            if len(args) > 16 or any(len(arg) > 100 or not re.fullmatch(r"[A-Za-z0-9_.-]*", arg) for arg in args):
                raise ValueError("Use at most 16 short script arguments containing letters, numbers, dots, underscores, or hyphens")
            command = "run " + shlex.quote(filename)
            if args:
                command += " " + " ".join(shlex.quote(arg) for arg in args)
            state = await send_terminal(command, browser_session)
            if state.startswith("NO_PROGRESS:"):
                return state
            result = state.casefold()
            if filename.casefold() not in result or not re.search(r"running script|pid\s*[:#]?\s*\d+|error|ram", result):
                raise RuntimeError(f"No visible run confirmation or game error for {filename}; inspect UI before retrying\n{state[-1200:]}")
            return state
        except Exception as exc:
            return f"ERROR: Script execution was not confirmed: {type(exc).__name__}: {exc}"

    actions = {
        "game_observe": game_observe,
        "game_progress": game_progress,
        "game_dismiss_dialog": game_dismiss_dialog,
        "game_open_tab": game_open_tab,
        "game_terminal": game_terminal,
        "game_open_editor": game_open_editor,
        "game_edit_script": game_edit_script,
        "game_run_script": game_run_script,
    }
    if not include_editor:
        # If the official Remote API is configured, script authoring goes through
        # that validated path. Keep execution and observation in the visible UI.
        for name in ("game_open_editor", "game_edit_script"):
            tools.registry.registry.actions.pop(name, None)
            actions.pop(name, None)
    return actions
