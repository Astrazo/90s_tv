from playwright.sync_api import sync_playwright
import time

PROFILE_DIR = "browser_profile"

def automate(query: str):
    with sync_playwright() as runner:
        context = runner.firefox.launch_persistent_context(
            user_data_dir=PROFILE_DIR,
            headless=False
        )

        page = context.new_page()
        page.goto("https://www.youtube.com/watch?v=TKSmgmRb7NM", wait_until="domcontentloaded")
        time.sleep(5)
        page.keyboard.press("f")
        while True:
            time.sleep(1)
            
automate("Test")
