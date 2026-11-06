"""Exercise deterministic visible UI helpers against a disposable game profile.

Run inside the deployment image with a fresh copy of a benchmark profile mounted
at /state/profile. The optional HEADLESS=1 setting runs the rendered UI checks
without opening a desktop display.
"""
import asyncio
import os

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
        opened = await actions["game_open_tab"](tab="Create Program", browser_session=browser)
        if opened.startswith("ERROR:") or "Opened visible game tab 'Create Program'" not in opened:
            raise RuntimeError(opened)
        listing = await actions["game_terminal"](command="ls", browser_session=browser)
        if listing.startswith(("ERROR:", "NO_PROGRESS:")):
            raise RuntimeError(f"Visible Terminal ls could not be verified: {listing}")
        print("Visible UI helper integration passed: modal state handled, Create Program opened by fresh semantic label, and Terminal ls returned:\n" + listing[-1600:])
    finally:
        await browser.stop()


if __name__ == "__main__":
    asyncio.run(main())
