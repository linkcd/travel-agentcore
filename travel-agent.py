from strands import Agent, tool
from strands_tools import calculator  # Import the calculator tool
from bedrock_agentcore.runtime import BedrockAgentCoreApp
from strands.models import BedrockModel

app = BedrockAgentCoreApp()

# Create a custom weather tool for travel assistance
@tool
def weather():
    """ Get weather information for travel planning """
    # Dummy implementation - in production, integrate with weather API
    return "sunny and pleasant for travel"

# Configure the Bedrock model
model_id = "eu.anthropic.claude-3-7-sonnet-20250219-v1:0"
model = BedrockModel(
    model_id=model_id,
)

# Create the travel agent with tools
agent = Agent(
    model=model,
    tools=[calculator, weather],
    system_prompt="You're a helpful travel assistant. You can help with travel planning, provide weather information, and do simple math calculations for travel expenses, distances, and time calculations."
)

@app.entrypoint
def travel_agent_bedrock(payload):
    """
    Main entry point for the travel agent
    Processes user input and returns agent response
    """
    user_input = payload.get("prompt")
    print("Travel agent received input:", user_input)
    
    # Process the user input through the agent
    response = agent(user_input)
    
    # Return the text content from the response
    return response.message['content'][0]['text']

if __name__ == "__main__":
    # Run the AgentCore application
    app.run()