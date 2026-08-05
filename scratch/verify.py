import httpx
import json
import asyncio
import uuid

async def chat_with_agent(prompt: str):
    print(f"\n--- USER: {prompt} ---")
    url = "http://localhost:8080/api/v1/chat/stream"
    payload = {
        "messages": [{"role": "user", "content": prompt}],
        "model": "deepseek-coder",  # Provide a model if required, though typically it routes correctly
        "user_id": str(uuid.uuid4())
    }
    
    try:
        async with httpx.AsyncClient(timeout=120) as client:
            async with client.stream("POST", url, json=payload) as response:
                if response.status_code != 200:
                    print(f"Server error: {response.status_code}")
                    print(await response.aread())
                    return
                
                async for chunk in response.aiter_lines():
                    if chunk.startswith("data: "):
                        data = json.loads(chunk[6:])
                        if "type" not in data:
                            print(f"\n[RAW] {data}")
                        elif data["type"] == "text":
                            print(data["delta"], end="", flush=True)
                        elif data["type"] == "tool_call":
                            print(f"\n[TOOL CALL] {data['name']}")
                        elif data["type"] == "message":
                            print(f"\n[MESSAGE] {data}")
                        elif data["type"] == "done":
                            print("\n[DONE]")
                        elif data["type"] == "error":
                            print(f"\n[ERROR] {data}")
    except Exception as e:
        print(f"Exception: {e}")

async def main():
    await chat_with_agent("give me a summary from the following url 'https://www.example.com/'")
    await chat_with_agent("take a screenshot of the page 'https://www.example.com/'")

if __name__ == "__main__":
    asyncio.run(main())
