import asyncio
from playwright.async_api import async_playwright

async def main():
    async with async_playwright() as p:
        browser = await p.chromium.launch(headless=True)
        page = await browser.new_page()
        await page.goto("http://localhost:5173/chat")
        await asyncio.sleep(2)
        print("PAGE CONTENT:", await page.evaluate("document.body.innerText"))
        await browser.close()

asyncio.run(main())
