import os
from dotenv import load_dotenv
from keycloak import KeycloakOpenID, KeycloakAdmin
from fastapi import HTTPException, status

load_dotenv()

KEYCLOAK_SERVER_URL = os.getenv("KEYCLOAK_SERVER_URL")
KEYCLOAK_REALM = os.getenv("KEYCLOAK_REALM")
KEYCLOAK_CLIENT_ID = os.getenv("KEYCLOAK_CLIENT_ID")
KEYCLOAK_CLIENT_SECRET = os.getenv("KEYCLOAK_CLIENT_SECRET")

KEYCLOAK_ADMIN_USERNAME = os.getenv("KEYCLOAK_ADMIN_USERNAME")
KEYCLOAK_ADMIN_PASSWORD = os.getenv("KEYCLOAK_ADMIN_PASSWORD")

keycloak_admin = KeycloakAdmin(
    server_url=KEYCLOAK_SERVER_URL,
    username=KEYCLOAK_ADMIN_USERNAME,
    password=KEYCLOAK_ADMIN_PASSWORD,
    realm_name=KEYCLOAK_REALM,
    user_realm_name="master",
    verify=True
)

keycloak_openid = KeycloakOpenID(
    server_url=KEYCLOAK_SERVER_URL,
    client_id=KEYCLOAK_CLIENT_ID,
    realm_name=KEYCLOAK_REALM,
    client_secret_key=KEYCLOAK_CLIENT_SECRET
)

def verify_keycloak_token(token: str):
    try:
        KEYCLOAK_PUBLIC_KEY = (
            "-----BEGIN PUBLIC KEY-----\n"
            + keycloak_openid.public_key()
            + "\n-----END PUBLIC KEY-----"
        )
        token_info = keycloak_openid.decode_token(
            token,
            key=KEYCLOAK_PUBLIC_KEY,
            options={"verify_signature": True, "verify_aud": False, "verify_exp": True}
        )
        
        return token_info
    except Exception as e:
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail=f"Invalid authentication credentials: {str(e)}",
            headers={"WWW-Authenticate": "Bearer"},
        )

def get_user_roles(token_info: dict) -> list:
    try:
        realm_access = token_info.get("realm_access", {})
        return realm_access.get("roles", [])
    except:
        return []

def user_has_realm_role(user_id: str, required_role: str) -> bool:
    try:
        roles = keycloak_admin.get_realm_roles_of_user(user_id)
        role_names = [role["name"] for role in roles]
        return required_role in role_names
    except Exception:
        return False