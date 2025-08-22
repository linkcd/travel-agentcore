import os
import time
from bedrock_agentcore_starter_toolkit import Runtime
from boto3.session import Session

def main():
    # Load configuration from environment variables
    discovery_url = os.getenv("ENTRA_DISCOVERY_URL")
    audience = os.getenv("ENTRA_AUDIENCE")
    
    if not discovery_url or not audience:
        raise ValueError("ENTRA_DISCOVERY_URL and ENTRA_AUDIENCE environment variables must be set")
    
    # Get AWS region from environment variable, default to eu-central-1 if not set
    region = os.getenv("AWS_REGION", "eu-central-1")
    print(f"Using region: {region}")
    
    # Configure AgentCore runtime
    agentcore_runtime = Runtime()
    
    response = agentcore_runtime.configure(
        entrypoint="travel_agent_inbound_authn.py",
        auto_create_execution_role=True,
        auto_create_ecr=True,
        requirements_file="requirements.txt",
        region=region,
        agent_name="travel_agent_inbound_authn",
        authorizer_configuration={
            "customJWTAuthorizer": {
                "discoveryUrl": discovery_url,
                "allowedAudience": [audience]
            }
        }
    )
    
    print("Configuration response:", response)
    
    # Deploy the agent
    launch_result = agentcore_runtime.launch()
    print("Launch result:", launch_result)

    status_response = agentcore_runtime.status()
    status = status_response.endpoint['status']
    end_status = ['READY', 'CREATE_FAILED', 'DELETE_FAILED', 'UPDATE_FAILED']
    while status not in end_status:
        time.sleep(10)
        status_response = agentcore_runtime.status()
        status = status_response.endpoint['status']
        print(status)
    
    if status == 'READY':
        print("✅ Agent deployed successfully!")
    
    return status_response

if __name__ == "__main__":
    main()