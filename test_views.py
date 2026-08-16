import os
from playwright.sync_api import sync_playwright

def run():
    with sync_playwright() as p:
        browser = p.chromium.launch(headless=True)
        page = browser.new_page(viewport={"width": 1140, "height": 650})
        page_path = os.path.abspath("data/pages/launcher.html")
        page.goto(f"file://{page_path}")
        page.wait_for_timeout(500)

        # 1. Main View
        os.makedirs("/home/jules/verification", exist_ok=True)
        page.screenshot(path="/home/jules/verification/1_main_view.png")

        # 2. Click Mod List
        page.click("#modlistBtn")
        page.wait_for_timeout(500)
        page.screenshot(path="/home/jules/verification/2_modlist_view.png")

        # 3. Click Back
        page.click("text=← Back to Launcher")
        page.wait_for_timeout(300)

        # 4. Click Update
        page.click("button:has-text('UPDATE')")
        page.wait_for_timeout(500)
        page.screenshot(path="/home/jules/verification/3_update_view.png")

        browser.close()
        print("Screenshots captured successfully.")

if __name__ == "__main__":
    run()
