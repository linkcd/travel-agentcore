#!/usr/bin/env python3
import os
import time
import requests
from jose import jwt
from jose.backends.rsa_backend import RSAKey


TENANT_ID = os.environ["ENTRA_TENANT_ID"]
CLIENT_ID = os.environ["ENTRA_AUDIENCE"]

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
            
            
            # --- Export to shell ---
            script_dir = os.path.dirname(os.path.abspath(__file__))
            auth_token_path = os.path.join(script_dir, '.auth_token')
            with open(auth_token_path, 'w') as f:
                f.write(f'export AUTH_TOKEN="{id_token}"\n')
            
            print("\n✅ Token added to environment variable AUTH_TOKEN")
            print(f"\n📝 To use in your shell, run: source {auth_token_path}")
            print(f"\n🔑 Token: {id_token[:50]}...")

        except Exception as e:
            print("\n❌ ID Token verification FAILED")
            print("Reason:", str(e))
            # Still export the token even if verification fails
            script_dir = os.path.dirname(os.path.abspath(__file__))
            auth_token_path = os.path.join(script_dir, '.auth_token')
            with open(auth_token_path, 'w') as f:
                f.write(f'export AUTH_TOKEN="{id_token}"\n')
            print(f"\n📝 Token exported to {auth_token_path} (run: source {auth_token_path})")

        break

    elif data.get("error") == "authorization_pending":
        time.sleep(5)
    else:
        raise Exception(data)
