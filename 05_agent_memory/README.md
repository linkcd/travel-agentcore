# 05. Travel Agent with AgentCore Memory

This example demonstrates how to build a travel agent with persistent conversation memory using Amazon Bedrock AgentCore's native memory integration with the Strands framework.

## 1. What We're Building

We'll create a travel agent that remembers previous conversations across sessions. The agent uses AgentCore's short-term memory to maintain context and provide personalized responses based on conversation history.

**Key Features:**
- Persistent conversation memory across agent restarts
- Automatic memory resource creation and management
- Native Strands framework integration
- Colored terminal output for better user experience

## 2. Architecture

```
User Input → Travel Agent → AgentCore Memory
     ↑                            ↓
     └── Conversation History ←────┘
```

**Components:**
- **MemoryManager**: Creates and manages AgentCore memory resources
- **AgentCoreMemorySessionManager**: Handles session-based memory operations
- **Strands Agent**: Travel assistant with native memory integration
- **Rich Console**: Colored terminal output for debugging and responses

## 3. Setup and Run

### Prerequisites
- AWS credentials configured with AgentCore Memory permissions
- Python 3.10+
- uv package manager

### Quick Start

1. **Install Dependencies**
   ```bash
   uv sync --no-install-project
   ```

2. **Set AWS Region** (optional)
   ```bash
   export AWS_REGION=us-east-1
   ```

3. **Run Travel Agent**
   ```bash
   uv run travel_agent_with_memory.py
   ```
   
   The agent automatically creates memory resources on first run.

## 4. How Memory Works

### Memory Configuration
- **Memory Name**: `TravelAgentMemory2`
- **Retention**: 7 days
- **Actor ID**: `t3` (represents the user that talks to the agent)
- **Session ID**: `t3_session_1` (conversation session)

### Conversation Flow
1. **Initialization**: Agent loads previous conversation history from memory
2. **User Interaction**: Each message is automatically stored in AgentCore memory
3. **Context Awareness**: Agent uses conversation history to provide personalized responses
4. **Persistence**: Memory survives agent restarts and can be resumed later when using the same actor id and session id.

### Debug Features
- **Message History Hook**: Displays conversation context before each response (in grey) for debugging
- **Colored Output**: Agent responses in green, debug info in grey
- **Rich Terminal**: Enhanced console output using the Rich library

## 5. Demo

### Example Conversation

```
TRAVEL AGENT WITH MEMORY
Type 'quit' to exit

You: Hi, I'm planning a trip to Japan next month
🤖 Agent: Hello! How exciting that you're planning a trip to Japan next month...

You: What's the weather like in Tokyo in February?
🤖 Agent: Since you mentioned you're traveling to Japan next month, Tokyo in February...
```

### Memory Persistence Test

1. **Start conversation** with the agent
2. **Exit** the application
3. **Restart** the agent
4. **Continue conversation** - the agent remembers previous context

## 6. Key Benefits

- **Session Continuity**: Conversations persist across agent restarts
- **Automatic Management**: Memory operations handled transparently
- **Native Integration**: Built-in Strands framework memory support
- **Visual Debugging**: Colored output shows conversation flow and memory state
- **Simple Setup**: Single script handles both memory setup and agent execution

## 7. Related Documentation

- [Amazon Bedrock AgentCore Documentation](https://docs.aws.amazon.com/bedrock-agentcore/)
- [AgentCore Starter Toolkit](https://aws.github.io/bedrock-agentcore-starter-toolkit/)
- [Strands Framework Guide](https://github.com/awslabs/amazon-bedrock-agentcore-samples)