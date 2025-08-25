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

```bash
export AWS_REGION=eu-central-1
export ENTRA_TENANT_ID=[Entra Tenant ID]
export ENTRA_CLIENT_ID=[Entra Application (client) ID for MCP]
export ENTRA_DISCOVERY_URL=https://login.microsoftonline.com/${ENTRA_TENANT_ID}/v2.0/.well-known/openid-configuration

# Build and deploy MCP
python ./scripts/deploy_mcp.py
# after the deployment, the deployed mcp ARN is saved to ./scripts/.agent_arn file
```

### Invoke the MCP server
We will have to generate bearer token to invoke the mcp server.
### Option 2: Device Code Flow - Command Line
```bash
# 1. Use Device Code flow to get bearer token from Entra ID against MCP application
python ./scripts/user_auth.py
# Now the auth code is saved to ./scripts/.auth_token file

# 2. Load the token value and agent ARN, then invoke the agent 
source ./scripts/.auth_token
source ./scripts/.agent_arn
python ./scripts/invoke_mcp.py
```
