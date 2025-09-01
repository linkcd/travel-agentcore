import os
import datetime  
import json
import asyncio
import traceback

from strands import Agent
from strands import tool
from bedrock_agentcore.runtime import BedrockAgentCoreApp
from bedrock_agentcore.identity.auth import requires_access_token
from strands.tools.mcp.mcp_client import MCPClient
from mcp.client.streamable_http import streamablehttp_client
from mcp_auth_helper import IsMCPAuthenticationError
import json


os.environ["STRANDS_OTEL_ENABLE_CONSOLE_EXPORT"] = "true"
os.environ["OTEL_PYTHON_EXCLUDED_URLS"] = "/ping,/invocations"

# Get MCP client ID from environment
SCOPES = [f"api://a1945aaf-db68-4f7e-8074-b79922b0e735/read"]
mcp_url = "https://bedrock-agentcore.eu-central-1.amazonaws.com/runtimes/arn%3Aaws%3Abedrock-agentcore%3Aeu-central-1%3A548129671048%3Aruntime%2Fweather_mcp_server-sxP7oW85Im/invocations?qualifier=DEFAULT"
MODEL_ID = "eu.anthropic.claude-sonnet-4-20250514-v1:0"

MCP_ACCESS_TOKEN = ""

async def on_auth_url(url: str):
    print(f"Authorization url: {url}")
    await queue.put(f"Authorization url: {url}")

# Create MCP client inside entrypoint where workload token is available
@requires_access_token(
    provider_name="fabeldyr-entra-mcp-provider",
    scopes=SCOPES,
    auth_flow='USER_FEDERATION',
    on_auth_url=on_auth_url,
    force_authentication=True,
)
async def need_mcp_access_token(*, access_token: str):
    global MCP_ACCESS_TOKEN
    MCP_ACCESS_TOKEN = access_token
    print("MCP Access token acquired")
    print(access_token)
    return access_token


# Initialize app and streaming queue
app = BedrockAgentCoreApp()

class StreamingQueue:
    def __init__(self):
        self.finished = False
        self.queue = asyncio.Queue()
        
    async def put(self, item):
        await self.queue.put(item)

    async def finish(self):
        self.finished = True
        await self.queue.put(None)

    async def stream(self):
        while True:
            item = await self.queue.get()
            if item is None and self.finished:
                break
            yield item

queue = StreamingQueue()

@app.entrypoint
async def agent_invocation(payload):
    await queue.put("Begin agent execution")

    # try to initialize MCP client
    try:
        mcp_client = MCPClient(
            lambda: streamablehttp_client(
                url=mcp_url, 
                # Get pat token from here: https://github.com/settings/personal-access-tokens
                headers={"Authorization": f"Bearer {MCP_ACCESS_TOKEN}"}
            )
        )
                
        user_message = payload.get("prompt", "No prompt found in input, please guide customer to create a json payload with prompt key")

        # Use MCP client within context manager
        print("Log: Entering MCP client context manager (first attempt)...")
        with mcp_client:
            print("Log: Inside MCP client context, listing tools (first attempt)...")
            mcp_tools = mcp_client.list_tools_sync()
            print(f"Log: Found {len(mcp_tools)} tools (first attempt)")
            agent = Agent(tools=mcp_tools, model=MODEL_ID)
            print("Log: Calling agent with user message (first attempt)...")
            response = agent(user_message)
            print(f"Agent response: {response.message}")
        
        await queue.put(response.message)
        await queue.put("End agent execution")
        
    except Exception as e:
        error_info = {
            "error": str(e),
            "error_type": type(e).__name__,
            "error_details": traceback.format_exc(),
            "timestamp": datetime.datetime.now().isoformat()
        }
        is_auth_error = IsMCPAuthenticationError(error_info)
        print(f"Error: {json.dumps(error_info, indent=2)}")

        if is_auth_error:
            print("Log: Authentication required for MCP Server. Starting authorization flow...")
            await queue.put("Authentication required for MCP Server. Starting authorization flow...")
            try:
                global MCP_ACCESS_TOKEN
                MCP_ACCESS_TOKEN = await need_mcp_access_token(access_token="")
                print("Log: Authentication successful! Retrying MCP client init...")
                await queue.put("Authentication successful! Retrying MCP client init...")

                # try to initialize MCP client again
                print(f"Log: Creating MCP client with token: {MCP_ACCESS_TOKEN}...")
                mcp_client = MCPClient(
                    lambda: streamablehttp_client(
                        url=mcp_url, 
                        headers={"Authorization": f"Bearer {MCP_ACCESS_TOKEN}"}
                    )
                )
                    
                user_message = payload.get("prompt", "No prompt found in input, please guide customer to create a json payload with prompt key")

                # Use MCP client within context manager
                print("Log: Entering MCP client context manager...")
                with mcp_client:
                    print("Log: Inside MCP client context, listing tools...")
                    mcp_tools = mcp_client.list_tools_sync()
                    print(f"Log: Found {len(mcp_tools)} tools")
                    agent = Agent(tools=mcp_tools, model=MODEL_ID)
                    print("Log: Calling agent with user message...")
                    response = agent(user_message)
                    print(f"Agent response after re-authentication: {response.message}")

                await queue.put(response.message)
                await queue.put("End agent execution after re-authentication")
            except Exception as e2:
                error_info2 = {
                    "error": str(e2),
                    "error_type": type(e2).__name__,
                    "error_details": traceback.format_exc(),
                    "timestamp": datetime.datetime.now().isoformat()
                }
                print(f"Error during re-authentication or MCP client init: {json.dumps(error_info2, indent=2)}")
                await queue.put(f"❌ Error during re-authentication or MCP client init: {json.dumps(error_info2, indent=2)}")

    # Return the stream
    async def stream_results():
        async for item in queue.stream():
            yield item
    
    return stream_results()

if __name__ == "__main__":
    app.run()