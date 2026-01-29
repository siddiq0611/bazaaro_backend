# from fastapi import APIRouter, Depends
# from .. import schemas, database
# from sqlalchemy.orm import Session
# from ..repositories import user

# router=APIRouter(
#     prefix="/user",
#     tags=['User']
# )
# get_db=database.get_db

# @router.post('', response_model=schemas.ShowUser)
# def create_user(request: schemas.User, db: Session=Depends(get_db)):
#     return user.create_user(request, db)

# @router.get('/{id}', response_model=schemas.ShowUser)
# def get_user(id: int, db: Session=Depends(get_db)):
#     return user.get_user(id, db)


from fastapi import APIRouter, Depends, HTTPException, status
from .. import schemas, database, oauth2, models
from sqlalchemy.orm import Session

router = APIRouter(
    prefix="/user",
    tags=['User']
)   
get_db = database.get_db

@router.get('/me', response_model=schemas.ShowUser)
def get_current_user_info(current_user = Depends(oauth2.get_current_user)):
    """Get current logged-in user info"""
    return current_user

@router.get('/{id}', response_model=schemas.ShowUser)
def get_user(id: int, db: Session = Depends(get_db)):
    """Get user by ID (authenticated users only)"""
    user = db.query(models.User).filter(models.User.id == id).first()
    if not user:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail=f"User with id {id} not found"
        )
    return user