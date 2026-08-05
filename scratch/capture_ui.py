import asyncio
from playwright.async_api import async_playwright
import os
import shutil

async def handle_chat_stream(route):
    # We will fulfill the request with a mocked SSE response.
    # We will simulate a timeline progression, an artifact (screenshot), and a final message.
    mocked_sse = (
        'data: {"type": "message", "role": "progress", "step": "Navigating to https://www.example.com", "status": "running"}\n\n'
        'data: {"type": "message", "role": "progress", "step": "Navigating to https://www.example.com", "status": "success"}\n\n'
        'data: {"type": "tool_call", "name": "browser.automation.execute"}\n\n'
        'data: {"type": "message", "role": "status", "content": "Action completed successfully."}\n\n'
        'data: {"type": "message", "role": "artifact", "artifact_id": "mock_art_123", "artifact_type": "image/png", "url": "https://dummyimage.com/600x400/000/fff&text=Mock+Screenshot", "metadata": {}}\n\n'
        'data: {"type": "text", "delta": "I have successfully "}\n\n'
        'data: {"type": "text", "delta": "taken the screenshot and navigated to the site."}\n\n'
        'data: {"type": "done"}\n\n'
    )
    
    await route.fulfill(
        status=200,
        headers={
            "Content-Type": "text/event-stream",
            "Cache-Control": "no-cache",
            "Connection": "keep-alive"
        },
        body=mocked_sse
    )

async def main():
    # Make sure we have artifacts dir
    artifacts_dir = "C:\\Users\\ranjithks\\.gemini\\antigravity-ide\\brain\\cde74d85-20cd-485c-9a35-1d098952d7bd"
    os.makedirs(artifacts_dir, exist_ok=True)
    
    print("Starting Playwright to capture UI screenshots...")
    async with async_playwright() as p:
        browser = await p.chromium.launch(headless=True)
        context = await browser.new_context(viewport={"width": 1280, "height": 800})
        page = await context.new_page()
        
        # Intercept chat stream API calls
        await page.route("**/api/v1/chat/stream", handle_chat_stream)
        
        page.on("console", lambda msg: print(f"BROWSER CONSOLE: {msg.type} {msg.text}"))
        page.on("pageerror", lambda err: print(f"BROWSER ERROR: {err}"))
        
        print("Navigating to UI...")
        await page.goto("http://localhost:5173")
        await page.wait_for_load_state("networkidle")
        
        print("Switching to Chat page...")
        await page.click("button:has-text('Chat')")
        await page.wait_for_selector("textarea", timeout=10000)
        
        # Take a 'Before' screenshot of empty state
        before_path = os.path.join(artifacts_dir, "ui_empty_state.png")
        await page.screenshot(path=before_path)
        print(f"Captured: {before_path}")
        
        # Interact with composer
        print("Sending a message...")
        try:
            await page.wait_for_selector("textarea", timeout=10000)
            await page.fill("textarea", "Take a screenshot of example.com")
            await page.click("button.chat-send-button")
        except Exception as e:
            print(f"Error interacting with composer: {e}")
            print(await page.content())
            raise
        
        # Wait for the mocked stream to finish and render
        await asyncio.sleep(2)
        
        after_path = os.path.join(artifacts_dir, "ui_timeline_artifact.png")
        await page.screenshot(path=after_path)
        print(f"Captured: {after_path}")
        
        await browser.close()

if __name__ == "__main__":
    asyncio.run(main())
