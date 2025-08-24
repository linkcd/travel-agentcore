import streamlit as st
import requests
import urllib.parse
import secrets
import base64
import json

import os

# Azure AD configuration from environment variables
CLIENT_ID = os.getenv('ENTRA_AUDIENCE')  # Using ENTRA_AUDIENCE as CLIENT_ID
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
    
    # Skip state validation for now since Streamlit session state is lost on redirect
    # if st.session_state.get('oauth_state') != state:
    #     st.error("Invalid state parameter")
    #     return None
    
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

# Main app
st.title("Custom OAuth with Raw JWT Token")

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
    st.success("Authentication successful!")
    
    access_token = st.session_state.get('access_token')
    id_token = st.session_state.get('id_token')
    
    if id_token:
        st.subheader("Raw ID Token (JWT):")
        st.code(id_token, language="text")
        
        # Decode and display ID token payload
        payload = decode_jwt_payload(id_token)
        if payload:
            st.subheader("Decoded ID Token Payload:")
            st.json(payload)
    
    if st.button("Logout"):
        for key in ['access_token', 'id_token', 'authenticated', 'oauth_state']:
            if key in st.session_state:
                del st.session_state[key]
        st.rerun()
        
elif 'oauth_state' not in st.session_state:
    st.write("Click the button below to authenticate with Microsoft:")
    auth_url = get_auth_url()
    st.markdown(f'<a href="{auth_url}" target="_self">Login with Microsoft</a>', unsafe_allow_html=True)
else:
    st.write("Waiting for authentication...")