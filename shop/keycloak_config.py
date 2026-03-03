from keycloak import KeycloakOpenID, KeycloakAdmin
from fastapi import HTTPException, status


KEYCLOAK_SERVER_URL = "http://localhost:8080"
KEYCLOAK_REALM = "ecommerce"
KEYCLOAK_CLIENT_ID = "ecommerce-api"
KEYCLOAK_CLIENT_SECRET = "053E0EMlhPibProXql0KmOS0hbocBdlV" 

KEYCLOAK_ADMIN_USERNAME = "admin"
KEYCLOAK_ADMIN_PASSWORD = "admin1@*"  # change if different

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
    """Verify and decode Keycloak token"""
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
    """Extract roles from token"""
    try:
        realm_access = token_info.get("realm_access", {})
        return realm_access.get("roles", [])
    except:
        return []

def check_role(roles: list, required_role: str) -> bool:
    """Check if user has required role"""
    return required_role in roles

def user_has_realm_role(user_id: str, required_role: str) -> bool:
    try:
        roles = keycloak_admin.get_realm_roles_of_user(user_id)
        role_names = [role["name"] for role in roles]
        return required_role in role_names
    except Exception:
        return False