import requests
import urllib.parse
import json
import os
import dotenv

# Load environment variables from .env file
dotenv.load_dotenv()

# Configuration Constants
REGION_NAME = "eu-central-1"

# === Agent Invocation Demo ===
# Validate required environment variables
invoke_agent_arn = os.environ.get('AGENT_ARN')
auth_token = os.environ.get('AUTH_TOKEN')

if not invoke_agent_arn:
    print("❌ Error: AGENT_ARN environment variable is not set")
    print("📝 Please run: source ./scripts/.agent_arn")
    exit(1)

if not auth_token:
    print("❌ Error: AUTH_TOKEN environment variable is not set")
    print("📝 Please run: source ./scripts/.auth_token")
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
    data=json.dumps({"prompt": "i am traveling to shanghai, what is the weather of shanghai in next week?"})
)

# Print response in a safe manner
print(f"Status Code: {invoke_response.status_code}")
print(f"Response Headers: {dict(invoke_response.headers)}")

# Handle response based on status code
if invoke_response.status_code == 200:
    print("Streaming Response:")
    print(invoke_response.text)
elif invoke_response.status_code >= 400:
    print(f"Error Response ({invoke_response.status_code}):")
    print(invoke_response.text)
else:
    print(f"Unexpected status code: {invoke_response.status_code}")
    print("Response text:")
    print(invoke_response.text[:500])