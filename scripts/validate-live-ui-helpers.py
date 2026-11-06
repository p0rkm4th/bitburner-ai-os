"""Exercise deterministic visible UI helpers against a disposable game profile.

Run inside the deployment image with a fresh copy of a benchmark profile mounted
at /state/profile. The optional HEADLESS=1 setting runs the rendered UI checks
without opening a desktop display.
"""
import asyncio
import os
import re

from browser_use import BrowserProfile, BrowserSession, Tools

from app.game_tools import register_game_tools


async def main() -> None:
    profile = BrowserProfile(
        user_data_dir=os.getenv("STATE_DIR", "/state") + "/profile",
        headless=os.getenv("HEADLESS", "0") == "1",
        allowed_domains=["bitburner-official.github.io"],
        enable_default_extensions=False,
        keep_alive=False,
    )
    browser = BrowserSession(browser_profile=profile)
    tools = Tools(exclude_actions=["evaluate", "click", "input", "navigate"])
    actions = register_game_tools(tools, include_editor=False)
    try:
        await browser.start()
        await browser.navigate_to("https://bitburner-official.github.io/")
        await asyncio.sleep(15)
        observed = await actions["game_observe"](browser_session=browser)
        if observed.startswith("ERROR:"):
            raise RuntimeError(observed)
        if "Offline for" in observed and "Your scripts generated" in observed:
            dismissed = await actions["game_terminal"](command="help", browser_session=browser)
            if (not dismissed.startswith("NO_PROGRESS:")
                    or "requested action was not performed" not in dismissed
                    or "Offline for" not in dismissed):
                raise RuntimeError(f"Terminal did not safely clear and report the offline dialog: {dismissed}")
            observed = await actions["game_observe"](browser_session=browser)
            if "Visible dialog: none" not in observed:
                raise RuntimeError(f"Offline dialog remained after one dismissal: {observed}")
        if "TYPE ERROR" in observed:
            dismissed = await actions["game_dismiss_dialog"](browser_session=browser)
            if ("dismissed and verified absent" not in dismissed
                    or "TYPE ERROR" not in dismissed
                    or "ns.getMoney is not a function" not in dismissed):
                raise RuntimeError(f"Type Error modal was not diagnosed and dismissed once: {dismissed}")
            observed = await actions["game_observe"](browser_session=browser)
            if "Visible dialog: none" not in observed:
                raise RuntimeError(f"Type Error modal remained after one dismissal: {observed}")
        if "Exit Tutorial" in observed:
            blocked = await actions["game_terminal"](command="ls", browser_session=browser)
            if not blocked.startswith("BLOCKED:") or "the command was not executed" not in blocked:
                raise RuntimeError(f"Tutorial-blocked Terminal command was not reported clearly: {blocked}")
            advanced = await actions["game_tutorial"](action="next", browser_session=browser)
            if not advanced.startswith("Advanced one tutorial page; the rendered transition was verified."):
                raise RuntimeError(f"Could not advance the tutorial using its visible Next button: {advanced}")
            observed = await actions["game_observe"](browser_session=browser)
            if "Exit Tutorial" not in observed:
                raise RuntimeError(f"Tutorial control was not visible after advancing one page: {observed}")
            exited = await actions["game_tutorial"](action="exit", browser_session=browser)
            if not exited.startswith("Exited the visible tutorial; the rendered transition was verified."):
                raise RuntimeError(f"Could not dismiss the tutorial in the disposable validation profile: {exited}")
            observed = await actions["game_observe"](browser_session=browser)
            if "This tutorial will show you the basics" in observed:
                raise RuntimeError(f"Tutorial remained visible in the disposable validation profile: {observed}")
        opened = await actions["game_open_tab"](tab="Create Program", browser_session=browser)
        if opened.startswith("ERROR:") or "Opened visible game tab 'Create Program'" not in opened:
            raise RuntimeError(opened)
        listing = await actions["game_terminal"](command="ls", browser_session=browser)
        if listing.startswith(("ERROR:", "NO_PROGRESS:")):
            raise RuntimeError(f"Visible Terminal ls could not be verified: {listing}")
        command_echoes = list(re.finditer(r"\[home\s+[^]]*\]\s*>\s*ls(?:\s|$)", listing, re.IGNORECASE))
        latest_output = listing[command_echoes[-1].end():].strip() if command_echoes else ""
        if not command_echoes or not latest_output or latest_output.casefold().startswith("please follow the tutorial"):
            raise RuntimeError(f"Terminal did not visibly execute the latest ls; it may have been blocked by game UI: {listing[-1600:]}")
        print("Visible UI helper integration passed: modal/tutorial state handled, Create Program opened by fresh semantic label, and Terminal ls visibly executed:\n" + listing[-1600:])
    finally:
        await browser.stop()


if __name__ == "__main__":
    asyncio.run(main())
