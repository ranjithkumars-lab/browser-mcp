import asyncio
import json
import sys
from mcp import ClientSession
from mcp.client.sse import sse_client
from ollama import AsyncClient

# Configuration
MCP_SERVER_URL = "http://192.168.0.168:8001/mcp/"
OLLAMA_HOST = "http://10.0.0.170:11444"
MODEL = "gpt-oss:20b"

async def chat_loop():
    print(f"Connecting to MCP server at {MCP_SERVER_URL}...")
    
    async with sse_client(MCP_SERVER_URL) as (read_stream, write_stream):
        async with ClientSession(read_stream, write_stream) as session:
            await session.initialize()
            
            # Fetch tools
            tools_response = await session.list_tools()
            mcp_tools = tools_response.tools
            
            ollama_tools = [
                {
                    "type": "function",
                    "function": {
                        "name": tool.name,
                        "description": tool.description,
                        "parameters": tool.inputSchema
                    }
                }
                for tool in mcp_tools
            ]
            
            print(f"Connected! Loaded {len(ollama_tools)} tools.")
            print(f"Connecting to Ollama at {OLLAMA_HOST} with model '{MODEL}'...")
            
            # Initialize Ollama Async Client with custom host
            ollama_client = AsyncClient(host=OLLAMA_HOST)
            
            messages = []
            
            print("\n" + "="*60)
            print("Interactive MCP Chat started. Type 'quit' or 'exit' to stop.")
            print("="*60)
            
            while True:
                try:
                    user_input = input("\nYou: ")
                    if user_input.strip().lower() in ['quit', 'exit']:
                        break
                    if not user_input.strip():
                        continue
                        
                    messages.append({"role": "user", "content": user_input})
                    
                    # Generate response
                    print("Agent is thinking...", end="", flush=True)
                    
                    response = await ollama_client.chat(
                        model=MODEL,
                        messages=messages,
                        tools=ollama_tools,
                    )
                    
                    print("\r" + " " * 30 + "\r", end="", flush=True) # Clear "thinking..."
                    
                    message = response["message"]
                    messages.append(message)
                    
                    if message.get("content"):
                        print(f"Agent: {message['content']}")
                        
                    # Handle tool calls
                    while message.get("tool_calls"):
                        for tool_call in message["tool_calls"]:
                            tool_name = tool_call["function"]["name"]
                            tool_args = tool_call["function"]["arguments"]
                            print(f"\n[🔧 Tool Execution] Calling '{tool_name}' with {json.dumps(tool_args)}")
                            
                            try:
                                result = await session.call_tool(tool_name, arguments=tool_args)
                                
                                tool_result_content = []
                                for content in result.content:
                                    if content.type == "text":
                                        tool_result_content.append(content.text)
                                
                                result_text = "\n".join(tool_result_content)
                                print(f"[🔧 Tool Result] {result_text[:300]}{'...' if len(result_text) > 300 else ''}")
                                
                                messages.append({
                                    "role": "tool",
                                    "name": tool_name,
                                    "content": result_text,
                                })
                            except Exception as e:
                                print(f"[❌ Tool Error] {e}")
                                messages.append({
                                    "role": "tool",
                                    "name": tool_name,
                                    "content": f"Error: {e}",
                                })
                        
                        # Get follow-up response after tool execution
                        print("\nAgent is analyzing tool results...", end="", flush=True)
                        response = await ollama_client.chat(
                            model=MODEL,
                            messages=messages,
                            tools=ollama_tools,
                        )
                        print("\r" + " " * 40 + "\r", end="", flush=True)
                        
                        message = response["message"]
                        messages.append(message)
                        
                        if message.get("content"):
                            print(f"Agent: {message['content']}")
                            
                except KeyboardInterrupt:
                    print("\nExiting...")
                    break
                except Exception as e:
                    print(f"\nError: {e}")

if __name__ == "__main__":
    if sys.platform == 'win32':
        asyncio.set_event_loop_policy(asyncio.WindowsSelectorEventLoopPolicy())
    asyncio.run(chat_loop())
