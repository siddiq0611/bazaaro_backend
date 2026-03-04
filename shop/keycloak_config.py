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

def create_keycloak_user(username: str, email: str, first_name: str, last_name: str, password: str) -> str:
    user_id = keycloak_admin.create_user({
        "username": username,
        "email": email,
        "firstName": first_name,
        "lastName": last_name,
        "enabled": True,
        "emailVerified": True,
        "credentials": [{
            "type": "password",
            "value": password,
            "temporary": False
        }]
    })
    return user_id

def assign_realm_role(user_id: str, role_name: str):
    """Assigns a realm-level role to a Keycloak user."""
    role = keycloak_admin.get_realm_role(role_name)
    keycloak_admin.assign_realm_roles(user_id=user_id, roles=[role])

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

# def user_has_realm_role(user_id: str, required_role: str) -> bool:
#     try:
#         roles = keycloak_admin.get_realm_roles_of_user(user_id)
#         role_names = [role["name"] for role in roles]
#         return required_role in role_names
#     except Exception:
#         return False
    
def swap_realm_role(user_id: str, remove_role: str, add_role: str):
    """Removes one realm role and assigns another atomically."""
    try:
        role_to_remove = keycloak_admin.get_realm_role(remove_role)
        keycloak_admin.delete_realm_roles_of_user(user_id=user_id, roles=[role_to_remove])
    except Exception:
        pass  

    role_to_add = keycloak_admin.get_realm_role(add_role)
    keycloak_admin.assign_realm_roles(user_id=user_id, roles=[role_to_add])