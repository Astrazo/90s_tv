from playwright.sync_api import Page
import time


# For each supported service, this is the CSS selector for the main video player element.
# We use this to wait for the player to be ready and to focus it before pressing fullscreen.
#
# NOTE: Netflix, Disney+, and Stan selectors are educated guesses.
# They need to be verified against real pages once we have accounts to test with.
PLAYER_SELECTORS = {
    "youtube.com":    "#movie_player",
    "netflix.com":    ".VideoContainer",
    "disneyplus.com": "div[data-testid='video-player']",
    "stan.com.au":    "video",
}


# ──────────────────────────────────────────────
# Per-service load functions
#
# Each function receives a Playwright Page that has already navigated to the URL.
# Its job is to: wait for the player to be ready, then start the video if needed.
# Fullscreen is handled separately (see go_fullscreen below).
# ──────────────────────────────────────────────

def load_youtube(page: Page):
    """
    Waits for the YouTube player to appear, then clicks play if it hasn't auto-started.
    """
    page.wait_for_selector("#movie_player", state="visible", timeout=15000)

    # Give YouTube a moment to settle before checking whether the video is playing.
    time.sleep(3)

    play_button = page.locator("button[aria-label='Play']")
    if play_button.is_visible():
        print("  Video wasn't playing — clicking the play button.")
        play_button.click()
    else:
        print("  Video appears to be playing already.")


def load_netflix(page: Page):
    """
    Netflix usually auto-plays when you land on a show URL, so we just wait for the player.
    TODO: Verify the selector and any needed click-to-play logic with a real Netflix URL.
    """
    raise NotImplementedError(
        "Netflix is not implemented yet. "
        "Find the correct player selector and fill in this function."
    )


def load_disney_plus(page: Page):
    """
    TODO: Verify the selector and any needed click-to-play logic with a real Disney+ URL.
    """
    raise NotImplementedError(
        "Disney+ is not implemented yet. "
        "Find the correct player selector and fill in this function."
    )


def load_stan(page: Page):
    """
    TODO: Verify the selector and any needed click-to-play logic with a real Stan URL.
    """
    raise NotImplementedError(
        "Stan is not implemented yet. "
        "Find the correct player selector and fill in this function."
    )


# Maps a URL domain to the function that starts playback on that service.
# To add a new service: write a load_X function above, then add one line here,
# and add its player selector to PLAYER_SELECTORS.
SERVICE_HANDLERS = {
    "youtube.com":    load_youtube,
    "netflix.com":    load_netflix,
    "disneyplus.com": load_disney_plus,
    "stan.com.au":    load_stan,
}


# ──────────────────────────────────────────────
# Helper functions used by main.py
# ──────────────────────────────────────────────

def get_domain(url: str) -> str | None:
    """
    Finds which supported service a URL belongs to.
    e.g. "https://www.youtube.com/watch?v=abc" -> "youtube.com"
    Returns None if no known service matches.
    """
    for domain in SERVICE_HANDLERS:
        if domain in url:
            return domain
    return None


def get_handler(url: str):
    """Returns the load function for the given URL, or None if the service isn't supported."""
    domain = get_domain(url)
    return SERVICE_HANDLERS.get(domain)


def go_fullscreen(page: Page, url: str):
    """
    Triggers YouTube-style fullscreen ('f' key) on the video player.
    'f' is the standard fullscreen shortcut across YouTube, Netflix, Disney+, and Stan.

    We focus the player element first so the keypress lands in the right place
    instead of the browser address bar or some other element.
    """
    domain = get_domain(url)

    # Fall back to a plain <video> tag if we don't have a specific selector for this service.
    player_selector = PLAYER_SELECTORS.get(domain, "video")

    # The player should already be visible if we called load_X first,
    # but we wait anyway in case this is called right after page load.
    page.wait_for_selector(player_selector, state="visible", timeout=15000)

    # Use focus() not click() — click() toggles play/pause, which is not what we want here.
    page.focus(player_selector)
    page.keyboard.press("f")

    print("  Fullscreen triggered.")


def mute_page(page: Page):
    """Silences all video elements on the page. Used when preloading in the background."""
    page.evaluate("document.querySelectorAll('video').forEach(v => v.muted = true)")


def unmute_page(page: Page):
    """Restores audio on all video elements. Called when we cut to a preloaded page."""
    page.evaluate("document.querySelectorAll('video').forEach(v => v.muted = false)")


def load_show_on_page(page: Page, show: dict, muted: bool = False):
    """
    Navigates a page to the show's URL and runs service-specific setup (play button, etc.).

    muted=True is used when preloading in the background so the user doesn't hear it.
    We mute both before and after the handler runs to catch videos that auto-play.
    """
    print(f"  Loading: {show['label']}")

    handler = get_handler(show["url"])
    if handler is None:
        print(f"  ERROR: No handler found for URL: {show['url']}")
        print(f"  Add support for this service in services.py.")
        return

    page.goto(show["url"], wait_until="domcontentloaded")

    if muted:
        mute_page(page)

    handler(page)

    if muted:
        # Mute again in case the handler triggered playback that un-muted the video.
        mute_page(page)
