# Weather MCP
THis is a weather MCP server, running an AgentCore as a MCP for (dummy) weather information.
Document: https://docs.aws.amazon.com/bedrock-agentcore/latest/devguide/runtime-mcp.html 


## Create Entra App for Weather MCP
Create the Entra App
Configure your Azure AD app as a public client:
- Go to Azure Portal → App registrations → Your app 
- Navigate to "Authentication"
- Set "Allow public client flows" to "Yes"

Take notes of tenant ID and MCP Entra Application (client) ID

### Build and Deployment MCP with AgentCore Runtime
As MCP only supports OAuth, we need to configure the authentication as OAuth as we did in [02_agent_inbound_authn](../../../02_agent_inbound_authn/)

In addition, set the protocol to "MCP" during configuration to tell AgentCore that this is a MCP server.

1. **Setup Environment Variables**
   ```bash
   # Copy the example file and update with your values
   cp .env.example .env
   # Edit .env file with your Entra ID configuration
   ```

2. **Build and Deploy MCP**
   ```bash
   # Build and deploy MCP
   python ./scripts/deploy_mcp.py
   # The deployed agent ARN is automatically saved to .env file
   ```

### Invoke the MCP server
We will have to generate bearer token to invoke the mcp server.

**Using Device Code Flow**
```bash
# 1. Use Device Code flow to get bearer token from Entra ID against MCP application
python ./scripts/user_auth.py
# The auth token is automatically saved to .env file

# 2. Invoke the MCP server (environment variables loaded automatically)
python ./scripts/invoke_mcp.py
```

**Benefits of .env approach:**
- No manual sourcing of environment files
- Automatic loading of all environment variables
- Single source of truth for configuration
- Better error handling and validation
