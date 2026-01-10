from pydantic import BaseModel, EmailStr
from datetime import datetime
from typing import Optional


class UserBase(BaseModel):
    name: str
    email: EmailStr


class UserCreate(UserBase):
    google_id: Optional[str] = None
    image: Optional[str] = None


class UserUpdate(BaseModel):
    name: Optional[str] = None
    email: Optional[EmailStr] = None
    image: Optional[str] = None


class UserResponse(UserBase):
    id: str
    google_id: Optional[str] = None
    image: Optional[str] = None
    created_at: datetime
    updated_at: datetime

    model_config = {"from_attributes": True}


class UserSyncRequest(BaseModel):
    """Request from NextAuth to sync user data"""
    google_id: str
    email: EmailStr
    name: str
    image: Optional[str] = None


class UserSyncResponse(UserResponse):
    """Response from sync endpoint including JWT token"""
    access_token: str
    token_type: str = "bearer"
