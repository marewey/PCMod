import os
from playwright.sync_api import sync_playwright

def verify_launcher():
    script_dir = os.path.dirname(os.path.abspath(__file__))
    launcher_path = os.path.abspath(os.path.join(script_dir, "data", "pages", "launcher.html"))

    os.makedirs("/home/jules/verification", exist_ok=True)
    screenshot_path = "/home/jules/verification/launcher_verification_final.png"

    with sync_playwright() as p:
        browser = p.chromium.launch(headless=True)
        context = browser.new_context(viewport={"width": 1100, "height": 655})
        page = context.new_page()

        print(f"Navigating to {launcher_path} ...")
        page.goto(f"file://{launcher_path}")

        page.wait_for_timeout(2000)

        print(f"Taking screenshot to {screenshot_path} ...")
        page.screenshot(path=screenshot_path)

        browser.close()
        print("Verification complete!")

if __name__ == "__main__":
    verify_launcher()
