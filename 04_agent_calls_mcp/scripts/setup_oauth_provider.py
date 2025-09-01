import os
from bedrock_agentcore.services.identity import IdentityClient
from dotenv import load_dotenv

load_dotenv()

MCP_TENANT_3LO_CLIENT_ID = os.getenv('MCP_TENANT_3LO_CLIENT_ID')
MCP_TENANT_3LO_SECRETE = os.getenv('MCP_TENANT_3LO_SECRETE')

def main():
    region = os.getenv('AWS_REGION', 'eu-central-1')
    identity_client = IdentityClient(region)

    # Configure Entra OAuth2 provider - On-Behalf-Of User
    # See supported providers: https://docs.aws.amazon.com/bedrock-agentcore-control/latest/APIReference/API_CreateOauth2CredentialProvider.html
    #https://github.com/aws/bedrock-agentcore-sdk-python/blob/3093768aa8600509c3bbba899123d78a6a1fedcb/src/bedrock_agentcore/identity/auth.py#L21
    # https://docs.aws.amazon.com/bedrock-agentcore/latest/APIReference/API_GetResourceOauth2Token.html
    # https://github.com/aws/bedrock-agentcore-sdk-python/blob/3093768aa8600509c3bbba899123d78a6a1fedcb/src/bedrock_agentcore/services/identity.py#L50
    google_provider = identity_client.create_oauth2_credential_provider({
        "name":"fabeldyr-entra-mcp-provider",
        "credentialProviderVendor":"MicrosoftOauth2",
        "oauth2ProviderConfigInput":{
            "microsoftOauth2ProviderConfig": {
                "clientId": MCP_TENANT_3LO_CLIENT_ID,
                "clientSecret": MCP_TENANT_3LO_SECRETE
            }
        }
    })
    print(google_provider)

if __name__ == "__main__":
    main()