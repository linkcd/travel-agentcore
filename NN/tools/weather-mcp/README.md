# Weather MCP
THis is a public MCP server, running an AgentCore as a MCP for (dummy) weather information.
Document: https://docs.aws.amazon.com/bedrock-agentcore/latest/devguide/runtime-mcp.html 

Addition to the same AgentCore build and deployment process, also use the "--protocol MCP" during configuration

```bash
agentcore configure -r eu-central-1 -e weather_mcp_server.py --protocol MCP

# Cloud Build
agentcore launch
```