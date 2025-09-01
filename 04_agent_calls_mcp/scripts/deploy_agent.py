import os
import time
from dotenv import load_dotenv
from bedrock_agentcore_starter_toolkit import Runtime
from boto3.session import Session

# Load environment variables from .env file
load_dotenv()

def main():
    # Get AWS region from environment variable, default to eu-central-1 if not set
    region = os.getenv("AWS_REGION", "eu-central-1")
    print(f"Using region: {region}")

    # Load configuration from environment variables
    tentant_id = os.getenv("ENTRA_TENANT_ID")
    audience = os.getenv("AGENT_ENTRA_CLIENT_ID")
    
    if not tentant_id or not audience:
        raise ValueError("ENTRA_TENANT_ID and AGENT_ENTRA_CLIENT_ID environment variables must be set")
    
    discovery_url = f"https://login.microsoftonline.com/{tentant_id}/v2.0/.well-known/openid-configuration"

    # Configure AgentCore runtime
    agentcore_runtime = Runtime()
    
    response = agentcore_runtime.configure(
        entrypoint="travel_agent_calls_mcp.py",
        auto_create_execution_role=True,
        auto_create_ecr=True,
        requirements_file="requirements.txt",
        region=region,
        agent_name="travel_agent_calls_mcp",
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
    
    # Save agent ARN to .env file
    if hasattr(launch_result, 'agent_arn') and launch_result.agent_arn:
        env_path = '.env'
        
        # Read existing .env content
        env_lines = []
        if os.path.exists(env_path):
            with open(env_path, 'r') as f:
                env_lines = f.readlines()
        
        # Update or add AGENT_ARN
        updated = False
        for i, line in enumerate(env_lines):
            if line.startswith('AGENT_ARN='):
                env_lines[i] = f'AGENT_ARN={launch_result.agent_arn}\n'
                updated = True
                break
        
        if not updated:
            env_lines.append(f'AGENT_ARN={launch_result.agent_arn}\n')
        
        # Write back to .env file
        with open(env_path, 'w') as f:
            f.writelines(env_lines)
        
        print(f"\n✅ Agent ARN saved to {env_path}")
        print(f"📝 Environment variables loaded automatically")

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