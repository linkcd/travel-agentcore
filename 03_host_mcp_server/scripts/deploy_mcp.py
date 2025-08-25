import os
import time
from bedrock_agentcore_starter_toolkit import Runtime
from boto3.session import Session

def main():
    # Load configuration from environment variables
    discovery_url = os.getenv("ENTRA_DISCOVERY_URL")
    audience = os.getenv("ENTRA_CLIENT_ID_MCP")
    
    if not discovery_url or not audience:
        raise ValueError("ENTRA_DISCOVERY_URL and ENTRA_CLIENT_ID_MCP environment variables must be set")
    
    # Get AWS region from environment variable, default to eu-central-1 if not set
    region = os.getenv("AWS_REGION", "eu-central-1")
    print(f"Using region: {region}")
    
    # Configure AgentCore runtime
    agentcore_runtime = Runtime()
    
    response = agentcore_runtime.configure(
        protocol="MCP",
        entrypoint="weather_mcp_server.py",
        auto_create_execution_role=True,
        auto_create_ecr=True,
        requirements_file="requirements.txt",
        region=region,
        agent_name="weather_mcp_server",
        authorizer_configuration={
            "customJWTAuthorizer": {
                "discoveryUrl": discovery_url,
                "allowedAudience": [audience]
            }
        }
    )
    
    print("Configuration response:", response)
    
    # Deploy the mcp
    launch_result = agentcore_runtime.launch()
    print("Launch result:", launch_result)
    
    # Save mcp ARN to file
    if hasattr(launch_result, 'agent_arn') and launch_result.agent_arn:
        script_dir = os.path.dirname(os.path.abspath(__file__))
        agent_arn_path = os.path.join(script_dir, '.agent_arn')
        with open(agent_arn_path, 'w') as f:
            f.write(f'export AGENT_ARN="{launch_result.agent_arn}"\n')
        print(f"\n✅ Agent ARN saved to {agent_arn_path}")
        print(f"📝 To use in your shell, run: source {agent_arn_path}")

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