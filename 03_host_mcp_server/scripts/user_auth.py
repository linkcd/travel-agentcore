#!/usr/bin/env python3
import os
import time
import requests
from dotenv import load_dotenv
from jose import jwt
from jose.backends.rsa_backend import RSAKey

# Load environment variables from .env file
load_dotenv()

# Validate required environment variables
if not os.environ.get("ENTRA_TENANT_ID"):
    raise ValueError("ENTRA_TENANT_ID environment variable is not set")
if not os.environ.get("ENTRA_CLIENT_ID_MCP"):
    raise ValueError("ENTRA_CLIENT_ID_MCP environment variable is not set")

TENANT_ID = os.environ["ENTRA_TENANT_ID"]
CLIENT_ID = os.environ["ENTRA_CLIENT_ID_MCP"]

DEVICE_CODE_URL = f"https://login.microsoftonline.com/{TENANT_ID}/oauth2/v2.0/devicecode"
TOKEN_URL = f"https://login.microsoftonline.com/{TENANT_ID}/oauth2/v2.0/token"

# Request v2 ID token only
SCOPE = "openid profile email offline_access"

def get_signing_key(jwks, token):
    """Find matching key from JWKS using kid in token header"""
    headers = jwt.get_unverified_header(token)
    kid = headers["kid"]
    for key in jwks["keys"]:
        if key["kid"] == kid:
            return RSAKey(key, algorithm="RS256")
    raise Exception("❌ No matching key found in JWKS for kid=" + kid)


# Step 1: Request device code
resp = requests.post(DEVICE_CODE_URL, data={"client_id": CLIENT_ID, "scope": SCOPE})
resp.raise_for_status()
dc = resp.json()

print("=== DEVICE FLOW ===")
print(f"Go to {dc['verification_uri']} and enter code: {dc['user_code']}")
print(f"Direct link: {dc['verification_uri']}?otc={dc['user_code']}")
print("===================\n")

# Step 2: Poll for token
while True:
    token_resp = requests.post(
        TOKEN_URL,
        data={
            "grant_type": "urn:ietf:params:oauth:grant-type:device_code",
            "client_id": CLIENT_ID,
            "device_code": dc["device_code"],
        },
    )
    data = token_resp.json()

    if "id_token" in data:
        id_token = data["id_token"]
        print("\n🔑 v2 ID Token received!\n")

        try:
            # --- Load OIDC config & JWKS ---
            oidc_config_url = f"https://login.microsoftonline.com/{TENANT_ID}/v2.0/.well-known/openid-configuration"
            oidc_config = requests.get(oidc_config_url).json()
            jwks_uri = oidc_config["jwks_uri"]
            issuer_v2 = oidc_config["issuer"]

            jwks = requests.get(jwks_uri).json()

            # --- Debug: Token header + claims ---
            unverified_header = jwt.get_unverified_header(id_token)
            unverified_claims = jwt.get_unverified_claims(id_token)

            print("=== DEBUG ID TOKEN ===")
            print("Header:", unverified_header)
            print("Claims:", unverified_claims)
            print("Issuer from OIDC config:", issuer_v2)
            print("JWKS URI:", jwks_uri)
            print("===================\n")

            # --- Match signing key ---
            signing_key = get_signing_key(jwks, id_token)
            print("✅ Found signing key for kid:", unverified_header["kid"])

            # --- Verify token ---
            token_iss = unverified_claims["iss"]
            if token_iss != issuer_v2:
                raise Exception(f"Unexpected issuer: {token_iss}")

            audience = unverified_claims["aud"]
            claims = jwt.decode(
                id_token,
                signing_key.to_pem().decode("utf-8"),
                algorithms=["RS256"],
                audience=audience,
                issuer=issuer_v2,  # enforce v2 issuer
            )

            print("\n✅ v2 ID Token verification PASSED")
            print("Verified Claims:", claims)

            # --- Print raw token ---
            print("\n🔑 Raw v2 ID Token (JWT):")
            print(id_token)
            
            
            # --- Save to .env file ---
            env_path = '.env'
            
            # Read existing .env content
            env_lines = []
            if os.path.exists(env_path):
                with open(env_path, 'r') as f:
                    env_lines = f.readlines()
            
            # Update or add AUTH_TOKEN
            updated = False
            for i, line in enumerate(env_lines):
                if line.startswith('AUTH_TOKEN='):
                    env_lines[i] = f'AUTH_TOKEN={id_token}\n'
                    updated = True
                    break
            
            if not updated:
                env_lines.append(f'AUTH_TOKEN={id_token}\n')
            
            # Write back to .env file
            with open(env_path, 'w') as f:
                f.writelines(env_lines)
            
            print("\n✅ Token saved to .env file")
            print(f"\n🔑 Token: {id_token[:50]}...")

        except Exception as e:
            print("\n❌ ID Token verification FAILED")
            print("Reason:", str(e))
            # Still save the token even if verification fails
            env_path = '.env'
            
            # Read existing .env content
            env_lines = []
            if os.path.exists(env_path):
                with open(env_path, 'r') as f:
                    env_lines = f.readlines()
            
            # Update or add AUTH_TOKEN
            updated = False
            for i, line in enumerate(env_lines):
                if line.startswith('AUTH_TOKEN='):
                    env_lines[i] = f'AUTH_TOKEN={id_token}\n'
                    updated = True
                    break
            
            if not updated:
                env_lines.append(f'AUTH_TOKEN={id_token}\n')
            
            # Write back to .env file
            with open(env_path, 'w') as f:
                f.writelines(env_lines)
            
            print(f"\n📝 Token saved to .env file")

        break

    elif data.get("error") == "authorization_pending":
        time.sleep(5)
    else:
        raise Exception(data)
