import streamlit as st
import requests
import urllib.parse
import secrets
import base64
import json
import os

# Azure AD configuration from environment variables
CLIENT_ID = os.getenv('ENTRA_CLIENT_ID')  
CLIENT_SECRET = os.getenv('ENTRA_CLIENT_SECRET')  # Add this env var if needed
TENANT_ID = os.getenv('ENTRA_TENANT_ID')
REDIRECT_URI = "http://localhost:8501"  # Streamlit root path

def get_auth_url():
    state = secrets.token_urlsafe(32)
    st.session_state.oauth_state = state
    
    params = {
        'client_id': CLIENT_ID,
        'response_type': 'code',
        'redirect_uri': REDIRECT_URI,
        'scope': 'openid profile email offline_access',
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
        'client_id': CLIENT_ID,
        'client_secret': CLIENT_SECRET,
        'code': code,
        'grant_type': 'authorization_code',
        'redirect_uri': REDIRECT_URI,
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

def call_agent(prompt, auth_token):
    """Call the travel agent with the user's prompt and JWT token"""
    # Configuration from invoke_agent.py
    REGION_NAME = "eu-central-1"
    
    # Validate AGENT_ARN environment variable
    invoke_agent_arn = os.getenv('AGENT_ARN')
    if not invoke_agent_arn:
        return {"error": "AGENT_ARN environment variable is not set. Please run: source ./scripts/.agent_arn"}
    
    # URL encode the agent ARN
    escaped_agent_arn = urllib.parse.quote(invoke_agent_arn, safe='')
    
    # Construct the URL
    url = f"https://bedrock-agentcore.{REGION_NAME}.amazonaws.com/runtimes/{escaped_agent_arn}/invocations?qualifier=DEFAULT"
    
    # Set up headers
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
            timeout=30
        )
        
        if response.status_code == 200:
            return response.json()
        else:
            return {"error": f"Agent returned status {response.status_code}: {response.text}"}
    
    except Exception as e:
        return {"error": f"Failed to call agent: {str(e)}"}

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
        if st.button("Show ID Token"):
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
        with st.expander("ID Token Details", expanded=True):
            if id_token:
                st.subheader("Raw ID Token (JWT):")
                st.code(id_token, language="text")
                
                payload = decode_jwt_payload(id_token)
                if payload:
                    st.subheader("Decoded ID Token Payload:")
                    st.json(payload)
            
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
        
        # Call agent and add response
        with st.chat_message("assistant"):
            with st.spinner("Thinking..."):
                agent_response = call_agent(prompt, id_token)
            
            if isinstance(agent_response, dict) and "error" in agent_response:
                response = f"Sorry, I encountered an error: {agent_response['error']}"
            elif isinstance(agent_response, dict):
                # Extract response from agent (adjust based on actual response format)
                response = agent_response.get('response', json.dumps(agent_response, indent=2))
            else:
                # Handle string response
                response = str(agent_response)
            
            st.markdown(response)
        
        st.session_state.messages.append({"role": "assistant", "content": response})
        
elif 'oauth_state' not in st.session_state:
    st.write("Click the button below to authenticate with Microsoft:")
    auth_url = get_auth_url()
    st.markdown(f'<a href="{auth_url}" target="_self">Login with Microsoft</a>', unsafe_allow_html=True)
else:
    st.write("Waiting for authentication...")