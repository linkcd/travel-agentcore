import requests
import urllib.parse
import json
import os
from dotenv import load_dotenv

# Load environment variables from .env file
load_dotenv()

# Configuration Constants
REGION_NAME = os.getenv('AWS_REGION', 'eu-central-1')

# === Agent Invocation Demo ===
# Validate required environment variables
invoke_agent_arn = os.environ.get('AGENT_ARN')
auth_token = os.environ.get('AUTH_TOKEN')

if not invoke_agent_arn or not auth_token:
    print("❌ Error: Required environment variables not set")
    print("📝 Please ensure AGENT_ARN and AUTH_TOKEN are set in .env file")
    print("📝 Run: python ./scripts/deploy_agent.py && python ./scripts/user_auth.py")
    exit(1)

# URL encode the agent ARN
escaped_agent_arn = urllib.parse.quote(invoke_agent_arn, safe='')

# Construct the URL
url = f"https://bedrock-agentcore.{REGION_NAME}.amazonaws.com/runtimes/{escaped_agent_arn}/invocations?qualifier=DEFAULT"

# Set up headers
headers = {
    "Authorization": f"Bearer {auth_token}",
    "X-Amzn-Trace-Id": "your-trace-id", 
    "Content-Type": "application/json"
}

# Enable verbose logging for requests
import logging
logging.basicConfig(level=logging.DEBUG)
logging.getLogger("urllib3.connectionpool").setLevel(logging.DEBUG)

invoke_response = requests.post(
    url,
    headers=headers,
    data=json.dumps({"prompt": "i am traveling to shanghai, any suggestions?"})
)

# Print response in a safe manner
print(f"Status Code: {invoke_response.status_code}")
print(f"Response Headers: {dict(invoke_response.headers)}")

# Handle response based on status code
if invoke_response.status_code == 200:
    response_data = invoke_response.json()
    print("Response JSON:")
    print(json.dumps(response_data, indent=2))  
elif invoke_response.status_code >= 400:
    print(f"Error Response ({invoke_response.status_code}):")
    error_data = invoke_response.json()
    print(json.dumps(error_data, indent=2))
    
else:
    print(f"Unexpected status code: {invoke_response.status_code}")
    print("Response text:")
    print(invoke_response.text[:500])