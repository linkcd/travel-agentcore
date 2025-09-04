import streamlit as st
import requests
import urllib.parse
import json
import os
from dotenv import load_dotenv
import uuid
from datetime import datetime
from auth_helper import AuthHelper, JWTHelper, Config

# Load .env
load_dotenv()
Config.validate()

def call_agent_stream(prompt, auth_token):
    """Call the travel agent with streaming response"""
    REGION_NAME = "eu-central-1"
    response = None
    
    try:
        invoke_agent_arn = os.getenv('AGENT_ARN')
        if not invoke_agent_arn:
            yield "❌ Error: AGENT_ARN environment variable is not set"
            return
        
        escaped_agent_arn = urllib.parse.quote(invoke_agent_arn, safe='')
        url = f"https://bedrock-agentcore.{REGION_NAME}.amazonaws.com/runtimes/{escaped_agent_arn}/invocations?qualifier=DEFAULT"
        
        headers = {
            "Authorization": f"Bearer {auth_token}",
            "X-Amzn-Trace-Id": "streamlit-chat-trace",
            "Content-Type": "application/json",
            "X-Amzn-Bedrock-AgentCore-Runtime-Session-Id": st.session_state.active_session_id
        }
        
        response = requests.post(
            url,
            headers=headers,
            data=json.dumps({"prompt": prompt}),
            stream=True,
            timeout=300
        )
        
        if response.status_code == 200:
            for line in response.iter_lines(decode_unicode=True):
                if line.strip():
                    if line.startswith('data: '):
                        data = line[6:]
                        if data.startswith('"') and data.endswith('"'):
                            try:
                                yield json.loads(data)
                            except:
                                yield data
                        else:
                            yield data
                    else:
                        yield line
        else:
            yield f"❌ Agent returned status {response.status_code}: {response.text}"
    
    except requests.exceptions.Timeout:
        yield "⏰ Request timed out. This may happen during OAuth authorization."
        yield "💡 If you were authorizing access, please try your request again after completing the authorization."
    except Exception as e:
        yield f"❌ Failed to call agent: {str(e)}"
    finally:
        # Always clean up the response
        if response is not None:
            try:
                response.close()
            except:
                pass

def render_token_details():
    """Render token details popup"""
    if st.session_state.get('show_token', False):
        with st.expander("Token Details", expanded=True):
            id_token = st.session_state.get('id_token')
            access_token = st.session_state.get('access_token')
            
            if id_token:
                st.subheader("ID Token")
                st.text_area("ID Token (JWT)", id_token, height=100, key="id_token_encoded")
                
                payload = JWTHelper.decode_payload(id_token)
                if payload:
                    st.text_area("ID Token Payload", json.dumps(payload, indent=2), height=200, key="id_token_decoded")
            
            if access_token:
                st.subheader("Access Token")
                st.text_area("Access Token (JWT)", access_token, height=100, key="access_token_encoded")
                
                access_payload = JWTHelper.decode_payload(access_token)
                if access_payload:
                    st.text_area("Access Token Payload", json.dumps(access_payload, indent=2), height=200, key="access_token_decoded")
            
            if st.button("Close"):
                st.session_state.show_token = False
                st.rerun()

def init_chat_sessions():
    """Initialize chat sessions in session state"""
    if "chat_sessions" not in st.session_state:
        st.session_state.chat_sessions = {}
    if "active_session_id" not in st.session_state:
        # Create first session
        session_id = str(uuid.uuid4())
        st.session_state.chat_sessions[session_id] = {
            "id": session_id,
            "name": session_id,
            "messages": [],
            "created_at": datetime.now()
        }
        st.session_state.active_session_id = session_id

def create_new_session():
    """Create a new chat session"""
    session_id = str(uuid.uuid4())
    st.session_state.chat_sessions[session_id] = {
        "id": session_id,
        "name": session_id,
        "messages": [],
        "created_at": datetime.now()
    }
    st.session_state.active_session_id = session_id

def delete_session(session_id):
    """Delete a chat session"""
    if len(st.session_state.chat_sessions) > 1:
        del st.session_state.chat_sessions[session_id]
        if st.session_state.active_session_id == session_id:
            st.session_state.active_session_id = list(st.session_state.chat_sessions.keys())[0]

def render_sidebar():
    """Render the chat sessions sidebar"""
    with st.sidebar:
        st.header("Chat Sessions")
        
        # New chat button
        if st.button("➕ New Chat", use_container_width=True):
            if "creating_session" not in st.session_state:
                st.session_state.creating_session = True
                create_new_session()
                st.rerun()
        
        # Reset creation flag
        if "creating_session" in st.session_state:
            del st.session_state.creating_session
        
        st.divider()
        
        # List all sessions
        for session_id, session in st.session_state.chat_sessions.items():
            col1, col2 = st.columns([3, 1])
            
            with col1:
                is_active = session_id == st.session_state.active_session_id
                button_style = "🔵" if is_active else "⚪"
                if st.button(f"{button_style} {session['name']}", key=f"session_{session_id}", use_container_width=True):
                    st.session_state.active_session_id = session_id
                    st.rerun()
            
            with col2:
                if len(st.session_state.chat_sessions) > 1:
                    if st.button("🗑️", key=f"delete_{session_id}", help="Delete session"):
                        delete_session(session_id)
                        st.rerun()

def get_active_session():
    """Get the currently active session"""
    return st.session_state.chat_sessions[st.session_state.active_session_id]

def render_chat_interface():
    """Render the main chat interface"""
    active_session = get_active_session()
    
    # Display session name
    st.subheader(f"💬 {active_session['name']}")
    
    # Display chat messages
    for message in active_session["messages"]:
        with st.chat_message(message["role"]):
            st.markdown(message["content"])
    
    # Chat input
    if prompt := st.chat_input("What can I help you with?"):
        active_session["messages"].append({"role": "user", "content": prompt})
        with st.chat_message("user"):
            st.markdown(prompt)
        
        # Stream agent response
        log_placeholder = None
        logs = []
        access_token = st.session_state.get('access_token')
        
        try:
            for chunk in call_agent_stream(prompt, access_token):
                if chunk == "---":
                    if log_placeholder and logs:
                        log_placeholder.markdown("\n".join(logs))
                        active_session["messages"].append({"role": "assistant", "content": "\n".join(logs)})
                elif chunk.startswith("**Answer:**"):
                    with st.chat_message("assistant"):
                        st.markdown(chunk)
                    active_session["messages"].append({"role": "assistant", "content": chunk})
                else:
                    if log_placeholder is None:
                        with st.chat_message("assistant"):
                            log_placeholder = st.empty()
                    logs.append(chunk)
                    log_placeholder.markdown("\n".join(logs) + " ▌")
        except:
            pass
        
        # Final cleanup
        try:
            if log_placeholder and logs and not any(msg.get("content", "").startswith("**Answer:**") for msg in active_session["messages"][-2:]):
                log_placeholder.markdown("\n".join(logs))
                active_session["messages"].append({"role": "assistant", "content": "\n".join(logs)})
        except:
            pass

def main():
    st.set_page_config(page_title="AgentCore Chat Assistant", page_icon="💬")
    st.title("AgentCore Chat Assistant")
    
    # Validate configuration
    try:
        Config.validate()
    except ValueError as e:
        st.error(f"Configuration Error: {e}")
        st.info("Please check your .env file and ensure all required environment variables are set.")
        return
    
    # Handle OAuth callback
    AuthHelper.handle_oauth_callback()
    
    if st.session_state.get('authenticated', False):
        # Initialize chat sessions
        init_chat_sessions()
        
        # Render sidebar
        render_sidebar()
        
        # Top navigation
        col1, col2, col3 = st.columns([2, 3, 1])
        with col1:
            if st.button("Show Tokens"):
                st.session_state.show_token = True
        with col2:
            st.write(f"Welcome, {AuthHelper.get_user_name()}")
        with col3:
            if st.button("Logout"):
                AuthHelper.logout()
        
        render_token_details()
        st.divider()
        render_chat_interface()
        
    elif 'oauth_state' not in st.session_state:
        st.write("Click the button below to authenticate with Microsoft:")
        auth_url = AuthHelper.get_auth_url()
        st.markdown(f'<a href="{auth_url}" target="_self">Login with Microsoft</a>', unsafe_allow_html=True)
    else:
        st.write("Waiting for authentication...")

if __name__ == "__main__":
    main()