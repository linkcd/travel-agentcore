import requests
import urllib.parse
import json
import os

# Configuration Constants
REGION_NAME = "eu-central-1"

# === Agent Invocation Demo ===
invoke_agent_arn = "arn:aws:bedrock-agentcore:eu-central-1:548129671048:runtime/travel_agent_inbound_authn-9jQJRuD5pz"
auth_token = os.environ.get('AUTH_TOKEN')

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