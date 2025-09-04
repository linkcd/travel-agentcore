# Travel Agent with Amazon Bedrock AgentCore

A collection of examples demonstrating how to build, deploy, and secure agentic workload using Amazon Bedrock AgentCore.

## 🎯 Overview

This repository showcases different patterns for implementing agents that can provide personalized travel recommendations, weather information, and travel planning assistance. Each example builds upon the previous one, demonstrating increasingly sophisticated deployment and security patterns.

## 📚 Step By Step examples

### [01. Standalone Agent](./01_agent_standalone/)
**Basic AgentCore Runtime Deployment**

Learn the fundamentals of building and deploying agents to AWS using Amazon Bedrock AgentCore Runtime. This example covers:
- Local development and testing
- Cloud build and deployment with CodeBuild
- Basic agent invocation
- Monitoring and observability

**Key Technologies:** Amazon Bedrock AgentCore Runtime, Strands Framework

---

### [02. Agent with Entra ID Inbound Authentication](./02_agent_inbound_authn/)
**Secure agent inbound access with Microsoft Entra ID integration**

Extend the basic agent with enterprise-grade authentication using Microsoft Entra ID. This example demonstrates:
- JWT-based authentication with Entra ID
- Authorization Code Flow
- Streamlit client interface with OAuth2
- Secure token management and validation

**Key Technologies:** AgentCore Runtime, Microsoft Entra ID, OAuth2, JWT, Streamlit

---

### [03. MCP Server with AgentCore](./03_host_mcp_server/)
**Build and deploy Model Context Protocol (MCP) server with AgentCore Runtime**

Deploy a dummy weather MCP server using Amazon Bedrock AgentCore Runtime, with Microsoft Entra ID authentication. This example demonstrates:
- MCP server implementation with FastMCP
- Deploy it with AgentCore Runtime as MCP protocol host
- OAuth2 authentication with Entra ID for inbound access
- Sample code of Device Code flow for token generation and testing

**Key Technologies:** MCP Protocol, FastMCP, AgentCore Runtime, Microsoft Entra ID

---



## 🛠️ Project Setup

### Prerequisites
- An AWS Account
- Entra ID (as Identity Provider)
- Permissions to create application registrations in Entra ID. Note that we are not running any workload in Azure/Entra ID. It is only used for Identity provider.

### Initial Setup

1. **Clone the Repository**
   ```bash
   git clone <repository-url>
   cd travel-agentcore
   ```

2. **Create and Activate Python Virtual Environment**
   ```bash
   python -m venv .venv
   source .venv/bin/activate  # On Windows: .venv\Scripts\activate
   ```

3. **Install Dependencies**
   ```bash
   pip install -r requirements.txt
   ```
   
   This installs all packages needed for deployment and testing scripts across all examples.

## 🚀 Choose Your Starting Point
- Want to build and run your agent in the cloud? Check out [Example 01](./01_agent_standalone/)
- Need inbound authentication for your agent? Jump to [Example 02](./02_agent_inbound_authn/)
- Want host MCP server in the cloud? Try [Example 03](./03_host_mcp_server/)
- Looking for specific features? Check the roadmap above



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