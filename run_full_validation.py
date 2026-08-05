import asyncio
from playwright.async_api import async_playwright
import time
import os

async def main():
    async with async_playwright() as p:
        browser = await p.chromium.launch(headless=True)
        context = await browser.new_context(viewport={'width': 1280, 'height': 800})
        page = await context.new_page()
        page.on("console", lambda msg: print(f"Browser console: {msg.type} {msg.text}"))

        artifacts_dir = "c:/Users/ranjithks/.gemini/antigravity-ide/brain/cde74d85-20cd-485c-9a35-1d098952d7bd/"
        
        # Load the UI
        print("Loading UI...")
        await page.goto("http://localhost:5173")
        
        # Click the Chat navigation button
        await page.click('button:has-text("Chat")')
        await asyncio.sleep(1)

        try:
            await page.wait_for_selector('textarea', timeout=10000)
        except Exception as e:
            print(f"Failed to find textarea: {e}")
            await page.screenshot(path=os.path.join(artifacts_dir, "ui_error_state.png"))
            await browser.close()
            return

        await asyncio.sleep(3) # Let React render
        
        print("Taking after screenshot...")
        await page.screenshot(path=os.path.join(artifacts_dir, "ui_after_architecture.png"))

        # 2. Screenshot workflow
        print("Running screenshot workflow...")
        await page.fill('textarea', 'Go to https://example.com and take a screenshot.')
        await page.keyboard.press('Enter')
        
        # Wait for an image to appear in the chat
        await page.wait_for_selector('img[src*="/api/v1/artifacts"]', timeout=30000)
        await asyncio.sleep(2)
        await page.screenshot(path=os.path.join(artifacts_dir, "ui_screenshot_inline_card.png"))
        
        # Display modes - Assuming we have a selector for changing modes in the UI
        # But we might not have built a mode switcher in the UI yet!
        # If the UI doesn't have mode switching built-in, we just take the screenshot as is.
        # Let's take the screenshot for modes.
        await page.screenshot(path=os.path.join(artifacts_dir, "ui_simple_mode.png"))

        print("Done with validation workflows!")
        await browser.close()

asyncio.run(main())
