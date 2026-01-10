from datetime import datetime, timedelta
from fastapi import APIRouter, Depends, HTTPException, Header, status
from sqlalchemy.orm import Session
from typing import Optional
import jwt
import os

from app.database import get_db
from app.models.user import User
from app.schemas.user import UserResponse, UserSyncRequest, UserSyncResponse


router = APIRouter(prefix="/auth", tags=["auth"])

# Add these to your config/settings
# SECRET_KEY = os.getenv("JWT_SECRET_KEY", None)
SECRET_KEY = os.environ["JWT_SECRET_KEY"]
ALGORITHM = "HS256"
ACCESS_TOKEN_EXPIRE_MINUTES = 60 * 24 * 7  # 1 week


def get_current_user(
    authorization: Optional[str] = Header(None),
    db: Session = Depends(get_db)
):
    """Dependency to get current user from JWT token in Authorization header"""
    if not authorization:
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail="Not authenticated",
            headers={"WWW-Authenticate": "Bearer"}
        )

    # Extract token from "Bearer <token>" format
    if not authorization.startswith("Bearer "):
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail="Invalid authentication scheme",
            headers={"WWW-Authenticate": "Bearer"}
        )

    access_token = authorization.split(" ")[1]

    try:
        payload = jwt.decode(access_token, SECRET_KEY, algorithms=[ALGORITHM])
        user_id: str = payload.get("sub")
        if user_id is None:
            raise HTTPException(
                status_code=status.HTTP_401_UNAUTHORIZED,
                detail="Invalid authentication credentials",
                headers={"WWW-Authenticate": "Bearer"}
            )
    except jwt.ExpiredSignatureError:
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail="Token has expired",
            headers={"WWW-Authenticate": "Bearer"}
        )
    # except jwt.JWTError:
    #     raise HTTPException(
    #         status_code=status.HTTP_401_UNAUTHORIZED,
    #         detail="Could not validate credentials",
    #         headers={"WWW-Authenticate": "Bearer"}
    #     )

    # Fixed: User IDs are UUIDs (strings), not integers
    user = db.query(User).filter(User.id == user_id).first()
    if user is None:
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail="User not found",
            headers={"WWW-Authenticate": "Bearer"}
        )

    return user


def create_access_token(data: dict, expires_delta: timedelta = None):
    """Create JWT token"""
    to_encode = data.copy()
    if expires_delta:
        expire = datetime.utcnow() + expires_delta
    else:
        expire = datetime.utcnow() + timedelta(minutes=ACCESS_TOKEN_EXPIRE_MINUTES)
    
    to_encode.update({"exp": expire})
    encoded_jwt = jwt.encode(to_encode, SECRET_KEY, algorithm=ALGORITHM)
    return encoded_jwt


@router.post("/sync", response_model=UserSyncResponse)
def sync_user(
    user_data: UserSyncRequest,
    db: Session = Depends(get_db)
):
    """
    Sync user from NextAuth session.
    Creates user if doesn't exist, updates if exists.
    Called from frontend after successful Google sign-in.
    Returns JWT token in response body.
    """
    # Try to find user by google_id first
    user = db.query(User).filter(User.google_id == user_data.google_id).first()

    if not user:
        # Try to find by email (in case user existed before OAuth)
        user = db.query(User).filter(User.email == user_data.email).first()

        if user:
            # Link existing user to Google account
            user.google_id = user_data.google_id
            user.image = user_data.image
        else:
            # Create new user
            user = User(
                google_id=user_data.google_id,
                email=user_data.email,
                name=user_data.name,
                image=user_data.image,
            )
            db.add(user)
    else:
        # Update existing user info
        user.name = user_data.name
        user.email = user_data.email
        user.image = user_data.image

    db.commit()
    db.refresh(user)

    # Generate JWT token
    access_token = create_access_token(
        data={
            "sub": str(user.id),
            "email": user.email,
            "google_id": user.google_id
        }
    )

    # Return user data with JWT token in response body
    return {
        **user.__dict__,
        "access_token": access_token,
        "token_type": "bearer"
    }


@router.get("/me", response_model=UserResponse)
def get_current_user_info(
    x_user_id: Optional[str] = Header(None, alias="X-User-Id"),
    db: Session = Depends(get_db)
):
    """Get current user info based on user ID from header."""
    if not x_user_id:
        raise HTTPException(status_code=401, detail="Not authenticated")

    user = db.query(User).filter(User.id == x_user_id).first()
    if not user:
        raise HTTPException(status_code=404, detail="User not found")

    return user


# def get_current_user(
#     x_user_id: Optional[str] = Header(None, alias="X-User-Id"),
#     db: Session = Depends(get_db)
# ) -> User:
#     """Dependency to get current authenticated user."""
#     if not x_user_id:
#         raise HTTPException(status_code=401, detail="Not authenticated")

#     user = db.query(User).filter(User.id == x_user_id).first()
#     if not user:
#         raise HTTPException(status_code=401, detail="User not found")

#     return user
