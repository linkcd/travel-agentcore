# Travel Agent with Amazon Bedrock AgentCore

A collection of examples demonstrating how to build, deploy, and secure AI travel agents using Amazon Bedrock AgentCore.

## 🎯 Overview

This repository showcases different patterns for implementing intelligent travel agents that can provide personalized travel recommendations, weather information, and travel planning assistance. Each example builds upon the previous one, demonstrating increasingly sophisticated deployment and security patterns.

## 📚 Examples

### [01. Standalone Agent](./01_agent_standalone/)
**Basic AgentCore deployment with no authentication**

Learn the fundamentals of building and deploying agents to AWS using Amazon Bedrock AgentCore Runtime. This example covers:
- Local development and testing
- Cloud deployment with CodeBuild
- Basic agent invocation
- Monitoring and observability

**Key Technologies:** Amazon Bedrock, AgentCore Runtime, Strands Framework

---

### [02. Agent with Entra ID Authentication](./02_agent_inbound_authn/)
**Secure agent access with Microsoft Entra ID integration**

Extend the basic agent with enterprise-grade authentication using Microsoft Entra ID. This example demonstrates:
- JWT-based authentication with Entra ID
- Two authentication flows: Device Code and Authorization Code
- Streamlit chat interface with OAuth2
- Secure token management and validation

**Key Technologies:** AgentCore Runtime, Microsoft Entra ID, OAuth2, JWT, Streamlit

---

### [03. MCP Server with AgentCore](./03_host_mcp_server/)
**Model Context Protocol (MCP) server deployment with Entra ID authentication**

Deploy a weather MCP server using Amazon Bedrock AgentCore Runtime with Microsoft Entra ID authentication. This example demonstrates:
- MCP server implementation with FastMCP
- AgentCore Runtime as MCP protocol host
- OAuth2 authentication with Entra ID 
- Sample code of Device Code flow for token generation

**Key Technologies:** MCP Protocol, FastMCP, AgentCore Runtime, Microsoft Entra ID

---



## 🚀 Getting Started
   - New to AgentCore? Start with [Example 01](./01_agent_standalone/)
   - Need authentication? Jump to [Example 02](./02_agent_inbound_authn/)
   - Want host MCP server in the cloud? Try [Example 03](./03_host_mcp_server/)
   - Looking for specific features? Check the roadmap above

3. **Follow the Pattern**
   Each example includes:
   - Detailed setup instructions
   - Step-by-step deployment guide
   - Testing and validation steps
   - Troubleshooting tips

## 📖 Documentation

- [Amazon Bedrock AgentCore Documentation](https://docs.aws.amazon.com/bedrock-agentcore/)
- [AgentCore Starter Toolkit](https://aws.github.io/bedrock-agentcore-starter-toolkit/)
- [Strands Framework Guide](https://github.com/awslabs/amazon-bedrock-agentcore-samples)

## 🤝 Contributing

We welcome contributions! Each example directory contains its own README with specific implementation details. Feel free to:
- Report issues or bugs
- Suggest new example patterns
- Submit improvements or optimizations
- Share your own agent implementations

## 📄 License

This project is licensed under the MIT License - see the LICENSE file for details.