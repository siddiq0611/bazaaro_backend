from fastapi import APIRouter, Depends, HTTPException, status, Form
from sqlalchemy.orm import Session
from ..keycloak_config import keycloak_openid, verify_keycloak_token, create_keycloak_user, assign_realm_role
from .. import schemas, oauth2, database, models

router = APIRouter(
    tags=["Authentication"]
)

@router.post('/signup', response_model=schemas.Token, status_code=201)
def signup(
    request: schemas.SignUp,
    db: Session = Depends(database.get_db)
):
    existing = db.query(models.User).filter(models.User.email == request.email).first()
    if existing:
        raise HTTPException(status_code=400, detail="Email already registered")

    try:
        full_name = f"{request.first_name} {request.last_name}"

        keycloak_id = create_keycloak_user(
            username=request.username,
            email=request.email,
            first_name=request.first_name,
            last_name=request.last_name,
            password=request.password
        )

        assign_realm_role(keycloak_id, "customer")

        token = keycloak_openid.token(request.username, request.password)
        access_token = token['access_token']

        new_user = models.User(
            name=full_name,
            email=request.email,
            password="keycloak_managed",
            keycloak_id=keycloak_id
        )
        db.add(new_user)
        db.commit()

        return {"access_token": access_token, "token_type": "bearer"}

    except HTTPException:
        raise
    except Exception as e:
        raise HTTPException(status_code=400, detail=f"Signup failed: {str(e)}")

@router.post('/login', response_model=schemas.Token)
def login(
    username: str = Form(...), 
    password: str = Form(...), 
    db: Session = Depends(database.get_db)
):
    try:
        token = keycloak_openid.token(username, password)
        access_token = token['access_token']
        token_info = verify_keycloak_token(access_token)
        email = token_info.get("email")
        if email:
            user = db.query(models.User).filter(models.User.email == email).first()
        
            if not user:
                keycloak_id = token_info.get("sub")
                user = models.User(
                    name=token_info.get("name", email.split("@")[0]),
                    email=email,
                    password="keycloak_managed", 
                    keycloak_id = keycloak_id
                )
                db.add(user)
                db.commit()
                db.refresh(user)
        
        return {
            "access_token": token['access_token'],
            "token_type": "bearer"
        }
    except Exception as e:
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail="Invalid credentials"
        )

@router.post('/logout')
def logout(current_user = Depends(oauth2.get_current_user)):
    return {
        "message": "Successfully logged out. Please remove your access token."
    }