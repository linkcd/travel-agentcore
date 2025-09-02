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

MCP_ACCESS_TOKEN = None
auth_url_holder = {"url": None}

async def on_auth_url(url: str):
    print(f"Authorization url: {url}")
    auth_url_holder["url"] = url

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
            if item is None:
                if self.finished:
                    break
                continue
            yield item

queue = StreamingQueue()

@app.entrypoint
async def agent_invocation(payload):
    async def stream_response():
        user_message = payload.get("prompt", "No prompt found in input")
        if not user_message or user_message == "No prompt found in input":
            yield "❌ No valid prompt provided"
            return

        yield "- 🚀 Starting travel agent"
        yield f"- 📝 Processing request: {user_message[:50]}{'...' if len(user_message) > 50 else ''}"
        
        try:
            yield "- 🔗 Connecting to weather service"
            
            global MCP_ACCESS_TOKEN
            mcp_client = MCPClient(
                lambda: streamablehttp_client(
                    url=mcp_url, 
                    headers={"Authorization": f"Bearer {MCP_ACCESS_TOKEN}"}
                )
            )
            
            yield "- 🔍 Discovering available tools"
            
            with mcp_client:
                mcp_tools = mcp_client.list_tools_sync()
                yield f"- ✅ Found {len(mcp_tools)} tools"
                yield "- 🤖 Initializing AI agent"
                yield "- 💭 Processing your request"
                
                agent = Agent(tools=mcp_tools, model=MODEL_ID)
                response = agent(user_message)
                
                # Extract clean response text
                if hasattr(response, 'message') and isinstance(response.message, dict):
                    if 'content' in response.message and isinstance(response.message['content'], list):
                        clean_response = response.message['content'][0].get('text', str(response.message))
                    else:
                        clean_response = str(response.message)
                else:
                    clean_response = str(response.message)
                
                yield "---"  # Separator
                yield f"**Answer:** {clean_response}"
            
        except Exception as e:
            error_info = {
                "error": str(e),
                "error_type": type(e).__name__,
                "timestamp": datetime.datetime.now().isoformat()
            }
            
            global MCP_ACCESS_TOKEN
            if "client initialization failed" in str(e).lower() or IsMCPAuthenticationError(error_info) or not MCP_ACCESS_TOKEN:
                yield "- 🔐 Authentication required"
                yield "- 🔑 Requesting access permissions"
                
                try:
                    # Start the auth process
                    auth_task = asyncio.create_task(need_mcp_access_token(access_token=""))
                    
                    # Wait a moment for the auth URL to be set
                    await asyncio.sleep(1)
                    
                    if auth_url_holder["url"]:
                        yield f"- 🔗 **Please click this link to authorize:** {auth_url_holder['url']}"
                        yield "- ⏳ Waiting for you to complete authorization..."
                    
                    MCP_ACCESS_TOKEN = await asyncio.wait_for(auth_task, timeout=300)
                    
                    yield "- ✅ Authentication successful"
                    yield "- 🔗 Reconnecting to weather service"
                    yield "- 🔍 Rediscovering tools"

                    mcp_client = MCPClient(
                        lambda: streamablehttp_client(
                            url=mcp_url, 
                            headers={"Authorization": f"Bearer {MCP_ACCESS_TOKEN}"}
                        )
                    )
                    
                    with mcp_client:
                        mcp_tools = mcp_client.list_tools_sync()
                        yield f"- ✅ Reconnected! Found {len(mcp_tools)} tools"
                        yield "- 💭 Processing your request"
                        
                        agent = Agent(tools=mcp_tools, model=MODEL_ID)
                        response = agent(user_message)
                        
                        # Extract clean response text
                        if hasattr(response, 'message') and isinstance(response.message, dict):
                            if 'content' in response.message and isinstance(response.message['content'], list):
                                clean_response = response.message['content'][0].get('text', str(response.message))
                            else:
                                clean_response = str(response.message)
                        else:
                            clean_response = str(response.message)
                        
                        yield "---"  # Separator
                        yield f"**Answer:** {clean_response}"
                        
                except asyncio.TimeoutError:
                    yield "⏰ Authorization timed out. Please try again."
                except Exception as e2:
                    yield f"❌ Authentication failed: {str(e2)}"
            else:
                yield f"❌ Service error: {str(e)}"
    
    return stream_response()

if __name__ == "__main__":
    app.run()