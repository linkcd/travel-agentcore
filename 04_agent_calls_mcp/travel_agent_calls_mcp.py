import os
import json
import asyncio
import logging
from datetime import datetime, timezone
from typing import Dict, Any, Optional, AsyncGenerator

from strands import Agent
from bedrock_agentcore.runtime import BedrockAgentCoreApp
from bedrock_agentcore.identity.auth import requires_access_token
from strands.tools.mcp.mcp_client import MCPClient
from mcp.client.streamable_http import streamablehttp_client
from mcp_auth_helper import IsMCPAuthenticationError

# Configure logging
logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)

# Environment configuration
os.environ["STRANDS_OTEL_ENABLE_CONSOLE_EXPORT"] = "true"
os.environ["OTEL_PYTHON_EXCLUDED_URLS"] = "/ping,/invocations"

# Load configuration from JSON file
try:
    with open("weather_mcp.json", "r") as f:
        config = json.load(f)
except (FileNotFoundError, json.JSONDecodeError) as e:
    raise Exception(f"Failed to load weather_mcp.json: {e}")

# Validate required configuration values
required_keys = ["MCP_AUTH_SCOPE", "MCP_URL"]
for key in required_keys:
    if key not in config or not config[key] or config[key].strip() == "":
        raise Exception(f"Missing or empty required MCP configuration: {key}")

# Configuration constants
SCOPES = [config["MCP_AUTH_SCOPE"]]
MCP_URL = config["MCP_URL"]
MODEL_ID = "eu.anthropic.claude-sonnet-4-20250514-v1:0"

class AuthState:
    """Manages authentication state and URLs"""
    def __init__(self):
        self.access_token: Optional[str] = None
        self.auth_url: Optional[str] = None
    
    def set_auth_url(self, url: str) -> None:
        logger.info("Authorization URL received")
        self.auth_url = url
    
    def set_access_token(self, token: str) -> None:
        self.access_token = token
        logger.info("MCP access token acquired")

auth_state = AuthState()

@requires_access_token(
    provider_name="fabeldyr-entra-mcp-provider",
    scopes=SCOPES,
    auth_flow='USER_FEDERATION',
    on_auth_url=auth_state.set_auth_url,
    force_authentication=True,
)
async def acquire_mcp_access_token(*, access_token: str) -> str:
    """Acquire MCP access token through OAuth flow"""
    auth_state.set_access_token(access_token)
    return access_token

def create_mcp_client(access_token: str) -> MCPClient:
    """Create MCP client with authentication"""
    return MCPClient(
        lambda: streamablehttp_client(
            url=MCP_URL,
            headers={"Authorization": f"Bearer {access_token}"}
        )
    )

def extract_response_text(response: Any) -> str:
    """Extract clean text from agent response"""
    if hasattr(response, 'message') and isinstance(response.message, dict):
        if 'content' in response.message and isinstance(response.message['content'], list):
            return response.message['content'][0].get('text', str(response.message))
        return str(response.message)
    return str(response.message)

def is_auth_error(error: Exception) -> bool:
    """Check if error requires authentication"""
    error_info = {
        "error": str(error),
        "error_type": type(error).__name__,
        "timestamp": datetime.now(timezone.utc).isoformat()
    }
    return (
        "client initialization failed" in str(error).lower() or
        IsMCPAuthenticationError(error_info) or
        not auth_state.access_token
    )

app = BedrockAgentCoreApp()

async def process_with_mcp(user_message: str) -> AsyncGenerator[str, None]:
    """Process user message with MCP tools"""
    yield "- 🔗 Connecting to weather MCP server..."
    
    mcp_client = create_mcp_client(auth_state.access_token)
    
    with mcp_client:
        mcp_tools = mcp_client.list_tools_sync()
        yield f"- ✅ Found {len(mcp_tools)} tools in MCP server"
        yield "- 🤖 Initializing agent with MCP tools and processing your request..."        
        agent = Agent(tools=mcp_tools, model=MODEL_ID)
        response = agent(user_message)
        
        yield "---"
        yield f"**Answer:** {extract_response_text(response)}"

async def handle_authentication(user_message: str) -> AsyncGenerator[str, None]:
    """Handle MCP authentication flow"""
    yield "- 🔐 Attempting to authenticate with MCP server - checking for cached token (take a few seconds) or requesting user authorization..."    
    try:
        auth_task = asyncio.create_task(acquire_mcp_access_token(access_token=""))
        # AgentCore python sdk default poll interval is 5 sec. Wait for 7sec fetching cached token and auth url
        # https://github.com/aws/bedrock-agentcore-sdk-python/blob/3093768aa8600509c3bbba899123d78a6a1fedcb/src/bedrock_agentcore/services/identity.py#L25C1-L25C37
        await asyncio.sleep(7) 

        if auth_state.access_token:
            yield "- ✅ Cached access token found, proceeding with request..."
        else:
            # no cached access token available, user interaction needed
            yield f"- 🔗 **No access token found. Please click this link to login and authorize MCP server:** {auth_state.auth_url}"            
            yield "- ⏳ Waiting for you to complete authorization..."
            await asyncio.wait_for(auth_task, timeout=300) # Wait for user to complete authentication
        
        yield "- ✅ MCP Authentication successful"
        yield "- 🔗 Reconnecting to the MCP server..."
        
        # Process request after authentication
        async for message in process_with_mcp(user_message):
            yield message
            
    except asyncio.TimeoutError:
        yield "⏰ Authorization timed out. Please try again."
    except Exception as e:
        yield f"❌ Authentication failed: {str(e)}"

@app.entrypoint
async def agent_invocation(payload: Dict[str, Any]) -> AsyncGenerator[str, None]:
    """Main agent invocation handler"""
    user_message = payload.get("prompt", "")
    if not user_message:
        yield "❌ No valid prompt provided"
        return

    yield "- 🚀 Agent starts processing the request..."
    
    try:
        async for message in process_with_mcp(user_message):
            yield message
    except Exception as e:
        if is_auth_error(e):
            async for message in handle_authentication(user_message):
                yield message
        else:
            yield f"❌ Service error: {str(e)}"

if __name__ == "__main__":
    app.run()