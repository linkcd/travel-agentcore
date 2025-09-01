# 04 Agent calls MCP with 3LO outbound auth

1. Create new agent as 02
2. reuse the mcp server from 03
3. create mcp_tenant_client for resource provider (multi tenant)
- create secrete
- set callback to https://bedrock-agentcore.eu-central-1.amazonaws.com/identities/oauth2/callback

? create secrete in mcp entra app registration? (cannot be the user facing client or agent as they can be hosted anywhere)

test steps:
1. double check the hardcoded mcp info in agent code
2. deploy agent
3. user_auth
4. invoke agent

todo:
1. make sure .env ignore and env sample
2. readme
3. refactoring the code to use global vairable for access token inside of agent code, not exception.