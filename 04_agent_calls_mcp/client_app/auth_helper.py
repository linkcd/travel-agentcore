import streamlit as st
import requests
import urllib.parse
import secrets
import base64
import json
import os
from typing import Optional, Dict, Any
from dotenv import load_dotenv

# Load .env from parent directory
load_dotenv()

class Config:
    AGENT_ENTRA_CLIENT_ID = os.getenv('AGENT_ENTRA_CLIENT_ID')
    STEAMLIT_ENTRA_CLIENT_ID = os.getenv('STEAMLIT_ENTRA_CLIENT_ID')
    STEAMLIT_ENTRA_CLIENT_SECRET = os.getenv('STEAMLIT_ENTRA_CLIENT_SECRET')
    TENANT_ID = os.getenv('ENTRA_TENANT_ID')
    REDIRECT_URI = "http://localhost:8501"
    
    @classmethod
    def validate(cls):
        required = ['AGENT_ENTRA_CLIENT_ID', 'STEAMLIT_ENTRA_CLIENT_ID', 'STEAMLIT_ENTRA_CLIENT_SECRET', 'TENANT_ID']
        for attr in required:
            if not getattr(cls, attr):
                raise ValueError(f"{attr} environment variable is not set")
    
    @classmethod
    def get_scope(cls):
        return f'openid profile email offline_access api://{cls.AGENT_ENTRA_CLIENT_ID}/read'

class JWTHelper:
    @staticmethod
    def decode_payload(token: str) -> Optional[Dict[str, Any]]:
        """Decode JWT payload without verification"""
        parts = token.split('.')
        if len(parts) != 3:
            return None
        
        payload = parts[1] + '=' * (4 - len(parts[1]) % 4)
        
        try:
            decoded = base64.urlsafe_b64decode(payload)
            return json.loads(decoded)
        except:
            return None

class AuthHelper:
    @staticmethod
    def get_auth_url() -> str:
        state = secrets.token_urlsafe(32)
        st.session_state.oauth_state = state
        
        params = {
            'client_id': Config.STEAMLIT_ENTRA_CLIENT_ID,
            'response_type': 'code',
            'redirect_uri': Config.REDIRECT_URI,
            'scope': Config.get_scope(),
            'state': state,
            'response_mode': 'query'
        }
        
        return f"https://login.microsoftonline.com/{Config.TENANT_ID}/oauth2/v2.0/authorize?" + urllib.parse.urlencode(params)
    
    @staticmethod
    def exchange_code_for_token(code: str, state: str) -> Optional[Dict[str, Any]]:
        token_url = f"https://login.microsoftonline.com/{Config.TENANT_ID}/oauth2/v2.0/token"
        
        data = {
            'client_id': Config.STEAMLIT_ENTRA_CLIENT_ID,
            'client_secret': Config.STEAMLIT_ENTRA_CLIENT_SECRET,
            'code': code,
            'grant_type': 'authorization_code',
            'redirect_uri': Config.REDIRECT_URI,
            'scope': Config.get_scope()
        }
        
        response = requests.post(token_url, data=data)
        if response.status_code == 200:
            return response.json()
        else:
            st.error(f"Token exchange failed: {response.text}")
            return None
    
    @staticmethod
    def handle_oauth_callback() -> bool:
        """Handle OAuth callback and return True if authentication successful"""
        query_params = st.query_params
        code = query_params.get('code')
        state = query_params.get('state')
        
        if code and state:
            st.write("Authorization code received, exchanging for token...")
            token_data = AuthHelper.exchange_code_for_token(code, state)
            
            if token_data:
                st.session_state.access_token = token_data.get('access_token')
                st.session_state.id_token = token_data.get('id_token')
                st.session_state.authenticated = True
                st.query_params.clear()
                st.rerun()
                return True
        return False
    
    @staticmethod
    def get_user_name() -> str:
        """Extract user name from ID token"""
        id_token = st.session_state.get('id_token')
        if id_token:
            payload = JWTHelper.decode_payload(id_token)
            if payload:
                return payload.get('name', payload.get('preferred_username', 'User'))
        return "User"
    
    @staticmethod
    def logout():
        """Clear authentication state"""
        keys_to_clear = ['access_token', 'id_token', 'authenticated', 'oauth_state', 'show_token', 'messages']
        for key in keys_to_clear:
            if key in st.session_state:
                del st.session_state[key]
        st.rerun()