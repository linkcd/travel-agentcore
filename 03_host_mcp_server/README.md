# 03. Host MCP Server with AgentCore Runtime

This example demonstrates how to build and deploy a dummy weather MCP server with AgentCore Runtime. It provides dummy weather information for testing.

Since MCP only supports OAuth, we use the same OAuth/JWT inbound authentication pattern as demonstrated in [02. Agent with Entra ID Inbound Authentication](../02_agent_inbound_authn/).

**Documentation:** https://docs.aws.amazon.com/bedrock-agentcore/latest/devguide/runtime-mcp.html 

## Architecture
![Architecture](./doc/architecture%203.png)


## 1. Create Entra ID App Registration for Weather MCP

1. **Create a new Entra ID application registration for Weather MCP**
   - Follow the same steps in [Step 1.1](../02_agent_inbound_authn/README.md) for creating app registration and scope
   - Enforce version 2 access token format as described in [Step 1.2](../02_agent_inbound_authn/README.md)

2. **Configure multi-tenant support**
   - Ensure this app registration is configured as a multi-tenant application

3. **Record configuration details**
   - Note the Tenant ID and MCP Entra Application (Client) ID

4. **Enable public client flow (for testing only)**
   - Enable "Allow public client flows" since we'll test the MCP server using Device Code Flow 

## 2. Build and Deploy MCP with AgentCore Runtime

Since MCP only supports OAuth, we need to configure AgentCore Runtime to use OAuth for inbound authentication, similar to [02. Agent with Entra ID Inbound Authentication](../02_agent_inbound_authn/).

Additionally, set the protocol to "MCP" during configuration to indicate that this is an MCP server.

Code snippet from the [deployment script](./scripts/deploy_mcp.py)
```python
   ...
    response = agentcore_runtime.configure(
        protocol="MCP", # This is MCP server
        entrypoint="weather_mcp_server.py",
        auto_create_execution_role=True,
        auto_create_ecr=True,
        requirements_file="requirements.txt",
        region=region,
        agent_name="weather_mcp_server",
        authorizer_configuration={
            "customJWTAuthorizer": {
                "discoveryUrl": discovery_url,
                "allowedAudience": [audience]
            }
        }
    )
    ...
```

## 3. Deployment Steps

1. **Setup Environment Variables**
```bash
# Copy the example file and update with your values
cp .env.example .env
# Edit .env file with your Entra ID configuration for MCP server
```

2. **Build and Deploy MCP**
```bash
# Build and deploy MCP
python ./scripts/deploy_mcp.py
# The deployed agent ARN is automatically saved to .env file
```

## 4. Invoke the MCP Server

You'll need to generate a bearer token to invoke the MCP server.

**Using Device Code Flow**
```bash
# 1. Use Device Code flow to get bearer token from Entra ID against MCP application
python ./scripts/user_auth.py
# The auth token is automatically saved to .env file

# User logs in with device code flow. Once complete, the access_token is saved to the .env file.

# 2. Invoke the MCP server (environment variables loaded automatically)
python ./scripts/invoke_mcp.py
```

This will print out the list of tools available in this MCP server:
```bash
🔄 Initializing MCP session...
✓ MCP session initialized

🔄 Listing available tools...

📋 Available MCP Tools:
==================================================
🔧 get_weather
   Description: Get current weather for a city
   Parameters: ['city']

🔧 get_forecast
   Description: Get weather forecast for a city
   Parameters: ['city', 'days']

✅ Successfully connected to MCP server!
Found 2 tools available.
```