import asyncio
from browser_mcp.app import create_browser_context
from browser_mcp.config.loader import load_browser_settings
from browser_mcp.browser.orchestration.planner import ExecutionPlanner
from browser_mcp.browser.orchestration.executor import BrowserExecutor
from browser_mcp.browser.orchestration.forms import FormEngine

async def main():
    settings = load_browser_settings()
    ctx = create_browser_context(settings)
    await ctx.start()
    
    navigation = ctx.container.resolve("navigation_manager")
    screenshot = ctx.container.resolve("screenshot_manager")
    elements = ctx.container.resolve("element_engine")
    sessions = ctx.container.resolve("browser_sessions")
    
    # Initialize Orchestrator
    form_engine = FormEngine(elements)
    executor = BrowserExecutor(navigation, screenshot, form_engine)
    planner = ExecutionPlanner(executor)
    
    # Create session
    session_res = await sessions.create_session(profile="temporary")
    session_id = session_res["session_id"]
    context_res = await sessions.create_context(session_id)
    context_id = context_res["context_id"]
    page_res = await sessions.new_page(session_id, context_id)
    page_id = page_res["page_id"]
    
    print("Testing screenshot...")
    await navigation.goto(session_id, page_id, "https://www.example.com/")
    res = await screenshot.capture_viewport(session_id, page_id)
    print("Screenshot result:", res)
    
    print("\nTesting login task...")
    res = await planner.execute_task(session_id, page_id, "login", {
        "url": "https://dev.amrita.ac.in/",
        "username": "Administrator",
        "password": "CSSAAPV@24"
    })
    print("Login result:", res)
    
    print("\nTesting register task...")
    res = await planner.execute_task(session_id, page_id, "register", {
        "url": "https://mybharat.gov.in/nasha_mukt/delegate_registration",
        "Name": "Ranjithkumar Sekar",
        "Mobile": "9080148600",
        "DOB": "01/05/1998",
        "State": "TAMIL NADU",
        "District": "NAMAKKAL",
        "Referral Code": "TEST1CODE"
    })
    print("Register result:", res)

if __name__ == "__main__":
    asyncio.run(main())
