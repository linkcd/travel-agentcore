# 02. agent_authN_end_users

## Overview

This example shows how to how to do Agent inbound authentication with Entra ID.

## AgentCore Document and User Guide
- https://github.com/awslabs/amazon-bedrock-agentcore-samples/blob/main/01-tutorials/03-AgentCore-identity/03-Inbound%20Auth%20example/inbound_auth_runtime_with_strands_and_bedrock_models.ipynb
- https://docs.aws.amazon.com/bedrock-agentcore/latest/devguide/identity-idp-microsoft.html

## 1. Prerequisite: Entra ID setup
- Create an application in Entra
- Take notes of Entra Tenent ID 
- Take notes of Entra Application (client) ID
- Create application secrete
- Create callback URL to http://localhost:8501 

![Entra ID app](./doc/EntraID-App.png)

## 2. Reuse the agent application code as before
the agent file is identical as [travel_agent_standalone.py](./travel_agent_standalone.py)

## 3. Create deployment script
[Deployment script](./scripts/deploy_agent.py)

## 4. Build and Deploy to AWS

1. **Setup Environment Variables**
   ```bash
   # Copy the example file and update with your values
   cp .env.example .env
   # Edit .env file with your Entra ID configuration
   ```

2. **Build and Deploy Agent**
   ```bash
   # Build and deploy agent
   python ./scripts/deploy_agent.py
   # The deployed agent ARN is automatically saved to .env file
   ```

## 5. End User Authentication and Invoke the agent 

### Streamlit App - Using Authentication Code Flow
```bash
# Run the Streamlit chat application (environment variables loaded automatically)
streamlit run client_app/app.py
```


## JWT Example
```json
{
  "aud": "2e9a7b16-.....",
  "iss": "https://login.microsoftonline.com/[ENTRA_TENANT_ID]/v2.0",
  "email": "EXAMPLE@ABCDEFG.onmicrosoft.com",
  "name": "Feng Lu",
  "preferred_username": "EXAMPLE@ABCDEFG.onmicrosoft.com",
  "ver": "2.0"
  ...
}
```