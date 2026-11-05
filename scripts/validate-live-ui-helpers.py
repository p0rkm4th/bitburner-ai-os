"""Exercise deterministic visible UI helpers against a disposable game profile.

Run inside the deployment image with a fresh copy of the clean benchmark profile
mounted at /state/profile. This test makes no gameplay changes beyond navigation.
"""
import asyncio
import os

from browser_use import BrowserProfile, BrowserSession, Tools

from app.game_tools import register_game_tools


async def main() -> None:
    profile = BrowserProfile(
        user_data_dir=os.getenv("STATE_DIR", "/state") + "/profile",
        headless=True,
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
            dismissed = await actions["game_dismiss_dialog"](browser_session=browser)
            if dismissed.startswith("ERROR:"):
                raise RuntimeError(dismissed)
        opened = await actions["game_open_tab"](tab="Create Program", browser_session=browser)
        if opened.startswith("ERROR:") or "Opened visible game tab 'Create Program'" not in opened:
            raise RuntimeError(opened)
        print("Visible UI helper integration passed: modal state handled and Create Program opened by fresh semantic label.")
    finally:
        await browser.stop()


if __name__ == "__main__":
    asyncio.run(main())
