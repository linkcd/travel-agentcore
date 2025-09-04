# Travel Agent with Amazon Bedrock AgentCore Runtime

## Overview

This tutorial demonstrates how to host a Strands Agent using Amazon Bedrock models in Amazon Bedrock AgentCore Runtime. The agent provides travel assistance with weather information and basic calculations.

## AgentCore Document and User Guide
- Document: https://docs.aws.amazon.com/bedrock-agentcore/
- AgentCore Starter Toolkit User Guide: https://aws.github.io/bedrock-agentcore-starter-toolkit/index.html

## 1. Local dev environment setup
```bash
python -m venv .venv
source .venv/bin/activate
pip install -r requirements.txt
```

## 2. Create the app file of your agent
Create a simple agent [travel_agent_standalone.py](./travel-agent.py)

## 3. Run and test the agent locally
```bash
# Start your agent
python travel_agent_standalone.py
```

```bash
# Test it (in another terminal)
curl -X POST http://localhost:8080/invocations \
  -H "Content-Type: application/json" \
  -d '{"prompt": "Im planning to travel to Shanghai, and suggestion?"}'
```

## 4. Build and Deploy to AWS

### 4.1 Configure Deployment Options
We are going to use AgentCore CLI for build and deployment. You can find CLI ref at https://aws.github.io/bedrock-agentcore-starter-toolkit/api-reference/cli.html (AgentCore CLI is included in the PIP package *bedrock-agentcore-starter-toolkit*) 

```bash
# Pass region, entrypoint and name of your agent as parameters
agentcore configure --region eu-central-1 --entrypoint travel_agent_standalone.py --name travel_agent_standalone
```

Based on your inputs, it generates (or update) these following files for real deployment:
- [Dockerfile](./Dockerfile)
- .bedrock_agentcore.yaml ([Example](./.bedrock_agentcore.example.yaml))
- .dockerignore

### 4.2 Build (Cloud vs Local) 
There are several options for building the agent docker image:

#### 4.2.1. Local Build (requires docker on local machine)
If you are using ARM64 machine, you can build it locally fairly fast. 
```bash
agentcore launch --local            # Build and run locally
# or
agentcore launch --local-build      # Build locally, deploy to cloud                                    
```
**NOTE**: 
If you are using Non-ARM64 machine (For example: x86_64/Windows with WSL), you can follow the [custom image build steps](https://docs.aws.amazon.com/bedrock-agentcore/latest/devguide/getting-started-custom.html#build-and-deploy-arm64-image) for docker cross-platform build. However, cross-platform build could be very slow (more than 1 hour). 


#### 4.2.2. Cloud Build (RECOMMENDED)
You can Cloud Build (using AWS CodeBuild), which ideal for:
- CI/CD pipeline
- You do not have Docker 
- You are using non-ARM64 machine (such as x86_64/Windows with WSL) 

```bash
agentcore launch          # Uses CodeBuild - no local Docker needed
```

## 5. Invoke the agent 
Once the Cloud Build and Deployment is done, the deployed agent information such as agent_arn are stored in .bedrock_agentcore.yaml.
Based on these info, you can invoke the agent using AgentCore CLI. 
```bash
# Test your deployed agent
agentcore invoke '{"prompt": "Im planning to travel to Shanghai, and suggestion?"}'
```
## 6. Authentication when invoking the agent
As default, the AgentCor Runtime is using AWS IAM for invoke authentication. If you need to protect your agent with OAuth/JWT issue from an Identity Provider (idp) such as Entra ID, check out the [Example 2 OAuth Inbound Authentication](../02_agent_inbound_authn/)

## 7. Observability
### 7.1. CloudWatch Logs
After the agent is deployed, you can monitor the agent logs in CloudWatch Logs. 
The **agentcore launch** should have printed out the following useful info:
```bash
# Agent logs available at:                                                                                                                                                      
#    /aws/bedrock-agentcore/runtimes/travel_agent-...                                                                                                               
#    /aws/bedrock-agentcore/runtimes/travel_agent-...                                                                                                  
#                                                                                                                                                                                  
# 💡 Tail logs with:                                                                                                                                                               
#    aws logs tail /aws/bedrock-agentcore/runtimes/travel_agent-... --follow                                                                                        
#    aws logs tail /aws/bedrock-agentcore/runtimes/travel_agent-... --since 1h                                                                                      