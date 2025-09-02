import streamlit as st
import requests
import urllib.parse
import secrets
import base64
import json
import os
import time
from dotenv import load_dotenv

# Load environment variables from .env file
load_dotenv()

# Azure AD configuration from environment variables
# Validate required Azure AD configuration
AGENT_ENTRA_CLIENT_ID = os.getenv('AGENT_ENTRA_CLIENT_ID')
if not AGENT_ENTRA_CLIENT_ID:
    raise ValueError("AGENT_ENTRA_CLIENT_ID environment variable is not set")

STEAMLIT_ENTRA_CLIENT_ID = os.getenv('STEAMLIT_ENTRA_CLIENT_ID')
if not STEAMLIT_ENTRA_CLIENT_ID:
    raise ValueError("STEAMLIT_ENTRA_CLIENT_ID environment variable is not set")

STEAMLIT_ENTRA_CLIENT_SECRET = os.getenv('STEAMLIT_ENTRA_CLIENT_SECRET')  
if not STEAMLIT_ENTRA_CLIENT_SECRET:
    raise ValueError("STEAMLIT_ENTRA_CLIENT_SECRET environment variable is not set")

TENANT_ID = os.getenv('ENTRA_TENANT_ID')
if not TENANT_ID:
    raise ValueError("ENTRA_TENANT_ID environment variable is not set")

REDIRECT_URI = "http://localhost:8501"  # Streamlit root path
SCOPE = f'openid profile email offline_access api://{AGENT_ENTRA_CLIENT_ID}/read'

def get_auth_url():
    state = secrets.token_urlsafe(32)
    st.session_state.oauth_state = state
    
    params = {
        'client_id': STEAMLIT_ENTRA_CLIENT_ID,
        'response_type': 'code',
        'redirect_uri': REDIRECT_URI,
        'scope': SCOPE,
        'state': state,
        'response_mode': 'query'
    }
    
    auth_url = f"https://login.microsoftonline.com/{TENANT_ID}/oauth2/v2.0/authorize?" + urllib.parse.urlencode(params)
    return auth_url

def exchange_code_for_token(code, state):
    # Debug info
    st.write(f"Received state: {state}")
    st.write(f"Session state: {st.session_state.get('oauth_state', 'None')}")
    
    token_url = f"https://login.microsoftonline.com/{TENANT_ID}/oauth2/v2.0/token"
    
    data = {
        'client_id': STEAMLIT_ENTRA_CLIENT_ID,
        'client_secret': STEAMLIT_ENTRA_CLIENT_SECRET,
        'code': code,
        'grant_type': 'authorization_code',
        'redirect_uri': REDIRECT_URI,
        'scope': SCOPE
    }
    
    response = requests.post(token_url, data=data)
    if response.status_code == 200:
        return response.json()
    else:
        st.error(f"Token exchange failed: {response.text}")
        return None

def decode_jwt_payload(token):
    # Decode JWT payload (without verification for display purposes)
    parts = token.split('.')
    if len(parts) != 3:
        return None
    
    payload = parts[1]
    # Add padding if needed
    payload += '=' * (4 - len(payload) % 4)
    
    try:
        decoded = base64.urlsafe_b64decode(payload)
        return json.loads(decoded)
    except:
        return None

def call_agent_stream(prompt, auth_token):
    """Call the travel agent with streaming response"""
    REGION_NAME = "eu-central-1"
    
    invoke_agent_arn = os.getenv('AGENT_ARN')
    if not invoke_agent_arn:
        yield "❌ Error: AGENT_ARN environment variable is not set"
        return
    
    escaped_agent_arn = urllib.parse.quote(invoke_agent_arn, safe='')
    url = f"https://bedrock-agentcore.{REGION_NAME}.amazonaws.com/runtimes/{escaped_agent_arn}/invocations?qualifier=DEFAULT"
    
    headers = {
        "Authorization": f"Bearer {auth_token}",
        "X-Amzn-Trace-Id": "streamlit-chat-trace",
        "Content-Type": "application/json"
    }
    
    try:
        response = requests.post(
            url,
            headers=headers,
            data=json.dumps({"prompt": prompt}),
            stream=True,
            timeout=300  # Increased timeout for OAuth flows
        )
        
        if response.status_code == 200:
            try:
                for line in response.iter_lines(decode_unicode=True):
                    if line.strip():
                        # Handle data: prefix from streaming
                        if line.startswith('data: '):
                            data = line[6:]  # Remove 'data: ' prefix
                            # Try to parse as JSON if it looks like JSON
                            if data.startswith('"') and data.endswith('"'):
                                try:
                                    yield json.loads(data)
                                except:
                                    yield data
                            else:
                                yield data
                        else:
                            yield line
            except GeneratorExit:
                # Handle generator cleanup gracefully
                response.close()
                return
        else:
            yield f"❌ Agent returned status {response.status_code}: {response.text}"
    
    except requests.exceptions.Timeout:
        yield "⏰ Request timed out. This may happen during OAuth authorization."
        yield "💡 If you were authorizing access, please try your request again after completing the authorization."
    except GeneratorExit:
        # Handle generator cleanup gracefully
        return
    except Exception as e:
        yield f"❌ Failed to call agent: {str(e)}"

# Main app
st.set_page_config(page_title="Chat Assistant", page_icon="💬")
st.title("Chat Assistant")

# Check for authorization code in URL
query_params = st.query_params
code = query_params.get('code')
state = query_params.get('state')

if code and state:
    st.write("Authorization code received, exchanging for token...")
    # Exchange code for token
    token_data = exchange_code_for_token(code, state)
    
    if token_data:
        # Store tokens in session state
        st.session_state.access_token = token_data.get('access_token')
        st.session_state.id_token = token_data.get('id_token')
        st.session_state.authenticated = True
        
        # Clear query params and rerun
        st.query_params.clear()
        st.rerun()

# Show authenticated state
if st.session_state.get('authenticated', False):
    # Get user info from token
    id_token = st.session_state.get('id_token')
    user_name = "User"
    if id_token:
        payload = decode_jwt_payload(id_token)
        if payload:
            user_name = payload.get('name', payload.get('preferred_username', 'User'))
    
    # Top navigation
    col1, col2, col3 = st.columns([2, 3, 1])
    with col1:
        if st.button("Show Tokens"):
            st.session_state.show_token = True
    with col2:
        st.write(f"Welcome, {user_name}")
    with col3:
        if st.button("Logout"):
            for key in ['access_token', 'id_token', 'authenticated', 'oauth_state', 'show_token', 'messages']:
                if key in st.session_state:
                    del st.session_state[key]
            st.rerun()
    
    # Token popup
    if st.session_state.get('show_token', False):
        with st.expander("Token Details", expanded=True):
            # ID Token Section
            if id_token:
                st.subheader("ID Token")
                st.text("Encoded (JWT):")
                st.text_area("ID Token (click to select all)", id_token, height=100, key="id_token_encoded")
                
                payload = decode_jwt_payload(id_token)
                if payload:
                    st.text("Decoded Payload:")
                    st.text_area("ID Token Payload (click to select all)", json.dumps(payload, indent=2), height=200, key="id_token_decoded")
            
            # Access Token Section
            access_token = st.session_state.get('access_token')
            if access_token:
                st.subheader("Access Token")
                st.text("Encoded (JWT):")
                st.text_area("Access Token (click to select all)", access_token, height=100, key="access_token_encoded")
                
                access_payload = decode_jwt_payload(access_token)
                if access_payload:
                    st.text("Decoded Payload:")
                    st.text_area("Access Token Payload (click to select all)", json.dumps(access_payload, indent=2), height=200, key="access_token_decoded")
            
            if st.button("Close"):
                st.session_state.show_token = False
                st.rerun()
    
    st.divider()
    
    # Chat interface
    
    # Initialize chat history
    if "messages" not in st.session_state:
        st.session_state.messages = []
    
    # Display chat messages
    for message in st.session_state.messages:
        with st.chat_message(message["role"]):
            st.markdown(message["content"])
    
    # Chat input
    if prompt := st.chat_input("What can I help you with?"):
        # Add user message to chat history
        st.session_state.messages.append({"role": "user", "content": prompt})
        with st.chat_message("user"):
            st.markdown(prompt)
        
        # Call agent with streaming response
        log_placeholder = None
        logs = []
        access_token = st.session_state.get('access_token')
        
        for chunk in call_agent_stream(prompt, access_token):
            if chunk == "---":
                # Finalize logs in first message
                if log_placeholder and logs:
                    log_placeholder.markdown("\n".join(logs))
                    st.session_state.messages.append({"role": "assistant", "content": "\n".join(logs)})
                continue
            elif chunk.startswith("**Answer:**"):
                # Show answer in separate message
                with st.chat_message("assistant"):
                    st.markdown(chunk)
                st.session_state.messages.append({"role": "assistant", "content": chunk})
                break
            else:
                # Create log message container if not exists
                if log_placeholder is None:
                    with st.chat_message("assistant"):
                        log_placeholder = st.empty()
                
                # Accumulate log messages
                logs.append(chunk)
                log_placeholder.markdown("\n".join(logs) + " ▌")
        
        # Final logs without cursor if no answer was provided
        if log_placeholder and logs and not any(msg.get("content", "").startswith("**Answer:**") for msg in st.session_state.messages[-2:]):
            log_placeholder.markdown("\n".join(logs))
            st.session_state.messages.append({"role": "assistant", "content": "\n".join(logs)})
        
elif 'oauth_state' not in st.session_state:
    st.write("Click the button below to authenticate with Microsoft:")
    auth_url = get_auth_url()
    st.markdown(f'<a href="{auth_url}" target="_self">Login with Microsoft</a>', unsafe_allow_html=True)
else:
    st.write("Waiting for authentication...")