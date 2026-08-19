import os
from playwright.sync_api import sync_playwright

def run():
    with sync_playwright() as p:
        browser = p.chromium.launch(headless=True)
        page = browser.new_page(viewport={"width": 1100, "height": 690})
        page_path = os.path.abspath("data/pages/launcher.html")
        page.goto(f"file://{page_path}")
        page.wait_for_timeout(1000)
        os.makedirs("/home/jules/verification", exist_ok=True)
        screenshot_path = "/home/jules/verification/launcher_card_style.png"
        page.screenshot(path=screenshot_path)
        browser.close()
        print(f"Card screenshot saved to {screenshot_path}")

if __name__ == "__main__":
    run()
