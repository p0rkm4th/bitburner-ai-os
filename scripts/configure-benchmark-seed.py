"""Prepare a clean benchmark profile through Bitburner's visible Options UI."""
import asyncio
import re

from browser_use import BrowserProfile, BrowserSession, Tools


GAME_URL = "https://bitburner-official.github.io/"


def click_index_for_label(summary: str, label: str) -> int:
    lines = summary.splitlines()
    for position, line in enumerate(lines):
        if line.strip() != label:
            continue
        for candidate in reversed(lines[max(0, position - 5):position]):
            match = re.search(r"\[(\d+)\]<(?:button\b|[^>]*role=button)", candidate)
            if match:
                return int(match.group(1))
    raise RuntimeError(f"Visible UI button {label!r} was not found")


async def main() -> None:
    profile = BrowserProfile(user_data_dir="/state/profile", headless=False,
                             allowed_domains=["bitburner-official.github.io"],
                             enable_default_extensions=False, keep_alive=False)
    session = BrowserSession(browser_profile=profile)
    tools = Tools()
    click_action = tools.registry.registry.actions["click"]
    try:
        await session.start()
        await session.navigate_to(GAME_URL)
        await asyncio.sleep(12)
        async def observe() -> str:
            return (await session.get_browser_state_summary(include_screenshot=False)).dom_state.llm_representation()

        summary = await observe()
        try:
            index = click_index_for_label(summary, "Exit Tutorial")
        except RuntimeError as error:
            raise RuntimeError(f"{error}; current visible UI follows:\n{summary}") from error
        await click_action.function(params=click_action.param_model(index=index), browser_session=session)
        await asyncio.sleep(1)
        summary = await observe()
        for label in ("Options", "Remote API"):
            index = click_index_for_label(summary, label)
            await click_action.function(params=click_action.param_model(index=index), browser_session=session)
            await asyncio.sleep(1)
            summary = await observe()
        port_match = re.search(r"\[(\d+)\]<input[^>]*placeholder=12525[^>]*value=0", summary)
        if port_match:
            input_action = tools.registry.registry.actions["input"]
            await input_action.function(
                params=input_action.param_model(index=int(port_match.group(1)), text="12525", clear=True),
                browser_session=session,
            )
            await asyncio.sleep(0.5)
            summary = await observe()
        await session.take_screenshot(path="/state/seed-ui.png")

        if "Remote API: Online" not in summary and "Status:\n\tOnline" not in summary and "Status: Online" not in summary:
            try:
                index = click_index_for_label(summary, "Connect")
            except RuntimeError as error:
                raise RuntimeError(f"{error}; current visible UI follows:\n{summary}") from error
            await click_action.function(params=click_action.param_model(index=index), browser_session=session)
            await asyncio.sleep(2)
            summary = await observe()

        if "Remote API: Online" not in summary and "Status:\n\tOnline" not in summary and "Status: Online" not in summary:
            raise RuntimeError(f"Visible Options page did not confirm Remote API Online; current UI follows:\n{summary}")
        # Persist the new Remote API settings through the game's own save UI.
        index = click_index_for_label(summary, "System")
        await click_action.function(params=click_action.param_model(index=index), browser_session=session)
        await asyncio.sleep(0.5)
        summary = await observe()
        index = click_index_for_label(summary, "Save Game")
        await click_action.function(params=click_action.param_model(index=index), browser_session=session)
        await asyncio.sleep(2)
        await session.stop()

        # Prove the game's own saved settings reconnect in a fresh browser session.
        session = BrowserSession(browser_profile=profile)
        await session.start()
        await session.navigate_to(GAME_URL)
        await asyncio.sleep(12)
        summary = await observe()
        if "Remote API: Online" not in summary:
            raise RuntimeError(f"Remote API did not reconnect after browser-session recreation; current UI follows:\n{summary}")
        print("Benchmark seed configured, saved through Bitburner UI, and reconnected Online after browser-session recreation.")
    finally:
        await session.stop()


if __name__ == "__main__":
    asyncio.run(main())
