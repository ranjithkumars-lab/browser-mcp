import asyncio
from playwright.async_api import async_playwright
import time

async def main():
    async with async_playwright() as p:
        browser = await p.chromium.launch(headless=True)
        context = await browser.new_context(viewport={'width': 1280, 'height': 800})
        page = await context.new_page()

        # Load the UI
        print("Loading UI...")
        await page.goto("http://localhost:5173")
        await page.wait_for_selector('textarea')
        await asyncio.sleep(3) # Let React render
        
        # Take an initial state screenshot
        await page.screenshot(path="c:/Users/ranjithks/.gemini/antigravity-ide/brain/cde74d85-20cd-485c-9a35-1d098952d7bd/ui_initial_state.png")

        # 2. Screenshot workflow
        print("Running screenshot workflow...")
        await page.fill('textarea', 'Go to https://example.com and take a screenshot.')
        await page.keyboard.press('Enter')
        
        # Wait for an image to appear in the chat
        await page.wait_for_selector('img[src*="/api/v1/artifacts"]', timeout=30000)
        # Wait a bit for the image to load fully
        await asyncio.sleep(2)
        await page.screenshot(path="c:/Users/ranjithks/.gemini/antigravity-ide/brain/cde74d85-20cd-485c-9a35-1d098952d7bd/ui_screenshot_workflow.png")

        print("Done!")
        await browser.close()

asyncio.run(main())
