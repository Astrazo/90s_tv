from playwright.sync_api import sync_playwright, Page
from services import load_show_on_page, go_fullscreen
import json
import time

PROFILE_DIR = "browser_profile"
SCHEDULE_FILE = "schedule.json"


def load_schedule(filepath: str) -> list[dict]:
    with open(filepath, "r") as f:
        return json.load(f)


def setup_loading_overlay(page: Page):
    """
    Installs a black overlay that auto-appears on every page load and stays
    visible until we explicitly remove it.

    We use add_init_script (not page.evaluate) because the script needs to run
    at the very start of each navigation — before YouTube's own scripts fire,
    before the DOM is populated, so there's no flash of content.

    The overlay also listens for YouTube's fullscreenchange event and moves
    itself inside the fullscreen element when it activates. This is necessary
    because elements on document.body are hidden behind the Fullscreen API layer.
    Without this, the overlay would disappear the moment YouTube goes fullscreen.

    Call this once after creating the page, before any navigation.
    """
    page.add_init_script("""
        (() => {
            // Black background before body even exists — catches the very first paint.
            document.documentElement.style.cssText = 'background: #000 !important;';

            const OVERLAY_ID = '__90s_tv_overlay';

            function buildOverlay() {
                const div = document.createElement('div');
                div.id = OVERLAY_ID;
                div.style.cssText = `
                    position: fixed;
                    top: 0; left: 0;
                    width: 100vw; height: 100vh;
                    background: #000;
                    z-index: 2147483647;
                    pointer-events: none;
                `;
                return div;
            }

            // Inject as soon as body is available.
            document.addEventListener('DOMContentLoaded', () => {
                if (!document.getElementById(OVERLAY_ID)) {
                    document.body.appendChild(buildOverlay());
                }
            });

            // When YouTube enters fullscreen, the fullscreen element covers document.body.
            // We move our overlay inside it so it stays on top of the video.
            document.addEventListener('fullscreenchange', () => {
                const overlay = document.getElementById(OVERLAY_ID);
                if (!overlay) return;

                if (document.fullscreenElement) {
                    document.fullscreenElement.appendChild(overlay);
                } else {
                    document.body && document.body.appendChild(overlay);
                }
            });
        })();
    """)


def remove_loading_overlay(page: Page):
    """
    Removes the black overlay to reveal the video.
    Call this only after fullscreen is confirmed active and the video is playing.
    """
    try:
        page.evaluate("""
            const overlay = document.getElementById('__90s_tv_overlay');
            if (overlay) overlay.remove();
        """)
    except Exception:
        pass


def inject_black_overlay(page: Page):
    """
    Covers the current (active) page with black immediately.
    Used the moment the user clicks NEXT so they see an instant response
    while the navigation and setup happen in the background.
    """
    try:
        page.evaluate("""
            () => {
                if (document.getElementById('__90s_tv_overlay')) return;
                const overlay = document.createElement('div');
                overlay.id = '__90s_tv_overlay';
                overlay.style.cssText = `
                    position: fixed; top: 0; left: 0;
                    width: 100vw; height: 100vh;
                    background: #000; z-index: 2147483647;
                    pointer-events: none;
                `;
                const target = document.fullscreenElement || document.body;
                target.appendChild(overlay);
            }
        """)
    except Exception:
        pass


def inject_next_button(page: Page):
    """
    Injects the NEXT button inside the active fullscreen element.
    The button sets window.__90sTVNextClicked = true when clicked.
    Python polls that global once per second.
    """
    page.evaluate("""
        () => {
            const existing = document.getElementById('__90s_tv_next_btn');
            if (existing) existing.remove();

            window.__90sTVNextClicked = false;

            const btn = document.createElement('button');
            btn.id = '__90s_tv_next_btn';
            btn.textContent = '⏭  NEXT';
            btn.style.cssText = `
                position: fixed;
                top: 24px; right: 24px;
                z-index: 2147483647;
                padding: 10px 22px;
                background: rgba(0, 0, 0, 0.8);
                color: white;
                border: 2px solid rgba(255, 255, 255, 0.9);
                border-radius: 8px;
                font-size: 16px;
                font-family: monospace;
                letter-spacing: 1px;
                cursor: pointer;
            `;
            btn.onclick = () => {
                btn.textContent = '✓ switching...';
                btn.style.opacity = '0.5';
                window.__90sTVNextClicked = true;
            };

            const target = document.fullscreenElement || document.body;
            target.appendChild(btn);
        }
    """)


def next_button_was_clicked(page: Page) -> bool:
    """Checks if the NEXT button was clicked. Safe to call while page is loading."""
    try:
        return page.evaluate("window.__90sTVNextClicked === true")
    except Exception:
        return False


def load_and_reveal(page: Page, show: dict):
    """
    Loads a show, enters fullscreen, then removes the black overlay to reveal it.

    The loading overlay (from setup_loading_overlay) keeps the screen black
    throughout all of this. The user only sees the video once everything is ready:
      1. Page navigated and video started (under overlay)
      2. YouTube fullscreen activated (overlay moves inside fullscreen element)
      3. Overlay removed — user sees video playing fullscreen
    """
    load_show_on_page(page, show)
    go_fullscreen(page, show["url"])

    # Wait until YouTube's fullscreen is confirmed active before revealing.
    try:
        page.wait_for_function("() => document.fullscreenElement !== null", timeout=5000)
    except Exception:
        pass  # Fullscreen didn't activate — reveal anyway so user isn't stuck on black.

    # Brief pause to let the video visually settle before we pull back the curtain.
    time.sleep(0.5)

    remove_loading_overlay(page)


def run_test(schedule: list[dict]):
    """
    Loads shows immediately (ignoring schedule times) so you can test transitions.
    A NEXT button appears in the top-right corner — click it to cut to the next show.
    Loops back to the first show after the last one.
    """
    with sync_playwright() as playwright:
        browser_context = playwright.chromium.launch_persistent_context(
            user_data_dir=PROFILE_DIR,
            headless=False,
            args=["--start-fullscreen"],
            no_viewport=True
        )

        page = browser_context.new_page()

        # Install the overlay init script before any navigation.
        setup_loading_overlay(page)

        current_index = 0
        current_show = schedule[current_index]

        print(f"\nTest mode — loading: {current_show['label']}")
        load_and_reveal(page, current_show)
        inject_next_button(page)

        print("Click NEXT in the top-right corner to cut to the next show.")
        print("Press Ctrl+C to stop.\n")

        while True:
            if next_button_was_clicked(page):
                next_index = (current_index + 1) % len(schedule)
                next_show = schedule[next_index]

                print(f"  Cutting to: {next_show['label']}")

                # Cover the current show immediately so the user sees a response.
                inject_black_overlay(page)

                # Load the next show and reveal once everything is ready.
                load_and_reveal(page, next_show)

                current_index = next_index
                inject_next_button(page)

                print(f"  Now showing: {next_show['label']}\n")

            time.sleep(1)


if __name__ == "__main__":
    schedule = load_schedule(SCHEDULE_FILE)
    run_test(schedule)
