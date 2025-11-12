#!/usr/bin/env python3
"""
Travel Agent with Memory
Demonstrates AgentCore short-term memory using native Strands integration.
"""

import logging
import os
from datetime import datetime
from strands import Agent
from strands.hooks import BeforeInvocationEvent, HookProvider, HookRegistry
from rich.console import Console
from rich.text import Text

# Native AgentCore memory integration
from bedrock_agentcore.memory.integrations.strands.config import AgentCoreMemoryConfig
from bedrock_agentcore.memory.integrations.strands.session_manager import AgentCoreMemorySessionManager
from bedrock_agentcore_starter_toolkit.operations.memory.manager import MemoryManager

# Initialize rich console
console = Console()

# Setup logging - suppress SDK logs, keep only app logs
logging.basicConfig(level=logging.WARNING, format="%(asctime)s - %(levelname)s - %(message)s")
logger = logging.getLogger("travel-agent")
logger.setLevel(logging.INFO)

# Suppress third-party library logs
logging.getLogger("boto3").setLevel(logging.WARNING)
logging.getLogger("botocore").setLevel(logging.WARNING)
logging.getLogger("bedrock_agentcore").setLevel(logging.WARNING)
logging.getLogger("bedrock_agentcore_starter_toolkit").setLevel(logging.WARNING)

# Configuration
REGION = os.getenv('AWS_REGION', 'us-east-1')
MEMORY_NAME = "TravelAgentMemory2"
ACTOR_ID = "t3"
SESSION_ID = "t3_session_1"

class PromptHookProvider(HookProvider):
    def on_before_invocation(self, event: BeforeInvocationEvent):
        """Print agent info before each execution"""
        console.print("\n" + "-"*50, style="dim")
        console.print("MESSAGE HISTORY:", style="dim")
        console.print("-"*50, style="dim")
        for i, msg in enumerate(event.agent.messages):
            console.print(f"{i}: {msg['role']} - {msg['content'][0]['text']}", style="dim")
        console.print("-"*50, style="dim")
    
    def register_hooks(self, registry: HookRegistry):
        registry.add_callback(BeforeInvocationEvent, self.on_before_invocation)

def setup_memory():

    # Initialize Memory Manager to get or create memory
    memory_manager = MemoryManager(region_name=REGION)
    
    # Get existing memory
    memory = memory_manager.get_or_create_memory(
        name=MEMORY_NAME,
        strategies=[],
        description="Short-term memory for travel agent conversations",
        event_expiry_days=7,
    )
    
    logger.info(f"✅ Memory ready (ID: {memory.id})")
    return memory.id

def create_travel_agent():
    """Create travel agent with native AgentCore memory integration"""
    # Ensure AWS region is set for Bedrock
    os.environ['AWS_DEFAULT_REGION'] = REGION
    
    # Setup memory
    memory_id = setup_memory()
    
    # Create AgentCore memory configuration
    agentcore_memory_config = AgentCoreMemoryConfig(
        memory_id=memory_id,
        session_id=SESSION_ID,
        actor_id=ACTOR_ID
    )
    
    # Create session manager with error handling
    try:
        session_manager = AgentCoreMemorySessionManager(
            agentcore_memory_config=agentcore_memory_config,
            region_name=REGION
        )
    except Exception as e:
        logger.error(f"Error creating session manager: {e}")
        raise e
    
    # Create agent with session manager - memory is handled automatically
    agent = Agent(
        name="TravelAssistant",
        model="global.anthropic.claude-sonnet-4-20250514-v1:0",
        system_prompt=
        f"""You are a helpful assistant with access to travel information.
            Use all you know about the user to provide helpful responses.
            
            Today's date: {datetime.today().strftime('%Y-%m-%d')}
        """,
        session_manager=session_manager,
        hooks=[PromptHookProvider()]
    )
    
    logger.info("✅ Travel agent created with AgentCore memory")
    return agent

def run_terminal_conversation():
    """Run terminal-based conversation with memory"""
    logger.info("🚀 Starting travel agent with memory")
    
    # Create agent (memory is automatically loaded)
    agent = create_travel_agent()
    
    print("\n" + "="*50)
    print("TRAVEL AGENT TERMINAL CHAT")
    print("Type 'quit' or 'exit' to end the conversation")
    print("="*50)
    
    while True:
        try:
            user_input = input("\n👤 You: ").strip()
            
            if user_input.lower() in ['quit', 'exit', 'q']:
                print("\n👋 Goodbye! Your conversation has been saved to memory.")
                break
            
            if not user_input:
                continue
                
            response = agent(user_input)
            
        except KeyboardInterrupt:
            print("\n\n👋 Goodbye! Your conversation has been saved to memory.")
            break
        except Exception as e:
            print(f"\n❌ Error: {e}")
            continue

if __name__ == "__main__":
    try:
        run_terminal_conversation()
        logger.info("🎉 Conversation ended successfully!")
    except Exception as e:
        logger.error(f"❌ Error: {e}")
        import traceback
        traceback.print_exc()
        exit(1)