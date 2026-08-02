import asyncio
import json
from mcp import ClientSession
from mcp.client.sse import sse_client
import ollama

async def main():
    # URL to the browser-mcp server's SSE endpoint.
    # Change "localhost" to your server's IP (e.g. 192.168.0.168) if running remotely.
    server_url = "http://localhost:8001/mcp/sse"
    
    # Define the model to use (Ensure you have pulled a tool-calling capable model like llama3.1)
    # e.g., run `ollama run llama3.1` in your terminal first.
    model = "llama3.1" 
    
    print(f"Connecting to MCP server at {server_url}...")
    
    async with sse_client(server_url) as (read_stream, write_stream):
        async with ClientSession(read_stream, write_stream) as session:
            await session.initialize()
            print("Connected successfully!")
            
            # 1. Fetch available tools from the MCP server
            tools_response = await session.list_tools()
            mcp_tools = tools_response.tools
            
            # Format tools for Ollama
            ollama_tools = []
            for tool in mcp_tools:
                ollama_tools.append({
                    "type": "function",
                    "function": {
                        "name": tool.name,
                        "description": tool.description,
                        "parameters": tool.inputSchema
                    }
                })
            
            print(f"Loaded {len(ollama_tools)} tools from Browser MCP.")
            
            # 2. Setup Ollama interaction
            messages = [
                {
                    "role": "user", 
                    "content": "Can you navigate to https://example.com, extract the page text, and summarize it for me?"
                }
            ]
            
            print(f"\nSending prompt to Ollama ({model}): {messages[0]['content']}")
            
            # Call Ollama with tools
            response = ollama.chat(
                model=model,
                messages=messages,
                tools=ollama_tools,
            )
            
            messages.append(response["message"])
            
            # 3. Handle tool calls from Ollama
            if response["message"].get("tool_calls"):
                print("\nOllama decided to call tools:")
                for tool_call in response["message"]["tool_calls"]:
                    tool_name = tool_call["function"]["name"]
                    tool_args = tool_call["function"]["arguments"]
                    print(f"\n  -> Calling '{tool_name}' with arguments: {json.dumps(tool_args)}")
                    
                    try:
                        # Execute the tool using the MCP server
                        result = await session.call_tool(tool_name, arguments=tool_args)
                        
                        # Format the result back for Ollama
                        tool_result_content = []
                        for content in result.content:
                            if content.type == "text":
                                tool_result_content.append(content.text)
                        
                        result_text = "\n".join(tool_result_content)
                        print(f"  <- Result snippet: {result_text[:200]}...\n")
                        
                        messages.append({
                            "role": "tool",
                            "name": tool_name,
                            "content": result_text,
                        })
                    except Exception as e:
                        print(f"  <- Error calling tool: {e}")
                        messages.append({
                            "role": "tool",
                            "name": tool_name,
                            "content": f"Error: {e}",
                        })
                
                # 4. Get final response from Ollama after executing tools
                print("Waiting for final response from Ollama...\n")
                final_response = ollama.chat(
                    model=model,
                    messages=messages,
                )
                print("================ FINAL RESPONSE ================")
                print(final_response["message"]["content"])
                print("================================================")
                
            else:
                print("\nOllama did not use any tools. Response:")
                print(response["message"]["content"])

if __name__ == "__main__":
    asyncio.run(main())
