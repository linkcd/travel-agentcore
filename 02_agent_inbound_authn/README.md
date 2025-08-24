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
```bash
# setup env variables
export AWS_REGION=eu-central-1
export ENTRA_TENANT_ID=[Entra Tenant ID]
export ENTRA_AUDIENCE=[Entra Application (client) ID]
export ENTRA_CLIENT_SECRET=[Entra Application Secret]
export ENTRA_DISCOVERY_URL=https://login.microsoftonline.com/${ENTRA_TENANT_ID}/v2.0/.well-known/openid-configuration

# build and deploy the agent
python ./scripts/deploy_agent.py
# after the deployment, the deployed agent ARN is saved to ./scripts/.agent_arn file
```

## 5. End User Authentication and Invoke the agent 

### Option 1: Authentication Code Flow - Streamlit App
```bash
# 1. Load environment variables for agent integration
source ./scripts/.agent_arn

# 2. Run the Streamlit chat application
streamlit run client_app/app.py
```

### Option 2: Device Code Flow - Command Line
```bash
# 1. Use Device Code flow to get bearer token from Entra ID  
python ./scripts/user_auth.py
# Now the auth code is saved to ./scripts/.auth_token file

# 2. Load the token value and agent ARN, then invoke the agent 
source ./scripts/.auth_token
source ./scripts/.agent_arn
python ./scripts/invoke_agent.py
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