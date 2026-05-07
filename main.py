from playwright.sync_api import sync_playwright
from services import go_fullscreen, unmute_page, load_show_on_page
import json
import time
import datetime

PROFILE_DIR = "browser_profile"
SCHEDULE_FILE = "schedule.json"

# How often (seconds) the main loop wakes up to check the schedule.
# Keeping this short means we catch show transitions quickly.
CHECK_INTERVAL_SECONDS = 10

# How many seconds before the next show starts to begin preloading it in the background.
# 90 seconds gives the page time to fully load and buffer before we need to cut to it.
PRELOAD_SECONDS_BEFORE = 90


def load_schedule(filepath: str) -> list[dict]:
    """
    Reads the schedule JSON file and returns a list of show entries.
    Each entry looks like:
        { "label": "Seinfeld", "time": "20:00", "url": "https://..." }
    """
    with open(filepath, "r") as file:
        return json.load(file)


def get_current_time_str() -> str:
    """Returns the current local time as a string like '20:05'."""
    return datetime.datetime.now().strftime("%H:%M")


def find_show_for_current_time(schedule: list[dict]) -> dict | None:
    """
    Returns the show that should be playing right now.

    Walks the schedule and returns the last show whose start time is <= the current time.
    That's the one that's currently "on air." Returns None if we're before the first show.
    """
    current_time_str = get_current_time_str()
    current_show = None

    for show in schedule:
        if show["time"] <= current_time_str:
            current_show = show  # Keep overwriting — we want the latest one that's started.

    return current_show


def find_next_show(schedule: list[dict], current_show: dict | None) -> dict | None:
    """
    Returns the show that comes after current_show in the schedule.

    If current_show is None (nothing is on yet), returns the first show of the day.
    Returns None if current_show is the last show of the day.
    """
    if current_show is None:
        return schedule[0] if schedule else None

    for i, show in enumerate(schedule):
        if show["time"] == current_show["time"]:
            if i + 1 < len(schedule):
                return schedule[i + 1]
            else:
                return None  # We're on the last show of the day.

    return None


def seconds_until_show(show: dict) -> int:
    """
    Returns how many seconds until a given show starts.
    Returns a negative number if the show has already started.
    """
    now = datetime.datetime.now()

    # Parse the "HH:MM" time string and attach today's date so we can subtract properly.
    show_time = datetime.datetime.strptime(show["time"], "%H:%M").replace(
        year=now.year, month=now.month, day=now.day
    )

    return int((show_time - now).total_seconds())


def run_tv(schedule: list[dict]):
    """
    The main loop. Opens the browser and switches shows on schedule.

    At any given moment we manage up to two pages (browser tabs):
      - active_page:    the tab currently on screen, playing the show.
      - preloaded_page: a hidden tab silently loading the next show in the background.

    When it's time to switch:
      1. Bring the preloaded tab to the front.
      2. Unmute it.
      3. Trigger fullscreen.
      4. Close the old tab.

    Because the new tab was already loaded and buffered, the user experiences this
    as a near-instant cut — no loading screens, no flash of an empty page.
    """
    with sync_playwright() as playwright:
        browser_context = playwright.chromium.launch_persistent_context(
            user_data_dir=PROFILE_DIR,
            headless=False,
            args=["--start-fullscreen"],
            no_viewport=True
        )

        active_page = browser_context.new_page()
        preloaded_page = None

        currently_playing_url = None
        preloading_url = None  # Tracks what we've already started preloading.
                               # Prevents us from kicking off the same preload twice.

        print("90s TV is running. Press Ctrl+C to stop.\n")

        while True:
            current_show = find_show_for_current_time(schedule)
            next_show = find_next_show(schedule, current_show)

            # ──────────────────────────────────────────
            # STEP 1: Switch to a new show if it's time.
            # ──────────────────────────────────────────

            if current_show is None:
                print(f"[{get_current_time_str()}] Nothing scheduled yet. Waiting...")

            elif current_show["url"] != currently_playing_url:
                print(f"[{get_current_time_str()}] Now playing: {current_show['label']}")

                if preloaded_page is not None and preloading_url == current_show["url"]:
                    # The upcoming show was preloaded and is ready in a background tab.
                    # Cut to it: swap pages, unmute, fullscreen, close the old one.
                    print("  Cutting to preloaded page (seamless)...")

                    old_page = active_page
                    active_page = preloaded_page
                    preloaded_page = None
                    preloading_url = None

                    active_page.bring_to_front()
                    unmute_page(active_page)
                    go_fullscreen(active_page, current_show["url"])
                    old_page.close()

                else:
                    # No preloaded page available (e.g. first run, or preload didn't finish).
                    # Load directly on the active page — the user will see it load.
                    print("  No preloaded page available. Loading directly...")
                    load_show_on_page(active_page, current_show)
                    go_fullscreen(active_page, current_show["url"])

                currently_playing_url = current_show["url"]

            else:
                print(f"[{get_current_time_str()}] Still playing: {current_show['label']}")

            # ────────────────────────────────────────────────────────────────────
            # STEP 2: Preload the next show in a background tab if we're close.
            # ────────────────────────────────────────────────────────────────────

            should_start_preload = (
                next_show is not None          # There is a next show.
                and preloaded_page is None     # We haven't already opened a preload tab.
                and preloading_url != next_show["url"]  # We haven't already preloaded this one.
            )

            if should_start_preload:
                time_left = seconds_until_show(next_show)

                if time_left <= PRELOAD_SECONDS_BEFORE:
                    print(f"  Preloading: {next_show['label']} (starts in {time_left}s)")

                    preloading_url = next_show["url"]
                    preloaded_page = browser_context.new_page()
                    load_show_on_page(preloaded_page, next_show, muted=True)

                    print("  Preload complete. Ready to cut when the time comes.")

            time.sleep(CHECK_INTERVAL_SECONDS)


# ── Entry point ──
# The `if __name__` guard means this only runs when you execute main.py directly.
# Without it, any other file that imports from main.py would immediately start the TV.
if __name__ == "__main__":
    schedule = load_schedule(SCHEDULE_FILE)
    run_tv(schedule)
