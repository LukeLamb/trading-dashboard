"""
Pydantic schemas for User and UserProfile
"""

from pydantic import BaseModel, EmailStr, Field, validator
from typing import Optional
from datetime import datetime
from uuid import UUID


class UserCreate(BaseModel):
    """Schema for user registration"""
    username: str = Field(..., min_length=3, max_length=50, description="Unique username")
    email: EmailStr = Field(..., description="Valid email address")
    password: str = Field(..., min_length=8, description="Password (min 8 characters)")
    display_name: str = Field(..., min_length=3, max_length=100, description="Display name (unique)")
    character_type: str = Field(..., description="Character type: analyst, risk_taker, conservative, day_trader, hodler")
    bio: Optional[str] = Field(None, max_length=280, description="User bio (optional)")
    avatar_url: Optional[str] = Field(None, description="Avatar URL (optional)")

    @validator('character_type')
    def validate_character_type(cls, v):
        allowed = ['analyst', 'risk_taker', 'conservative', 'day_trader', 'hodler']
        if v not in allowed:
            raise ValueError(f'character_type must be one of: {", ".join(allowed)}')
        return v

    @validator('password')
    def validate_password(cls, v):
        if len(v) < 8:
            raise ValueError('Password must be at least 8 characters')
        if not any(char.isdigit() for char in v):
            raise ValueError('Password must contain at least one number')
        if not any(char in '!@#$%^&*()_+-=[]{}|;:,.<>?' for char in v):
            raise ValueError('Password must contain at least one special character')
        return v

    class Config:
        json_schema_extra = {
            "example": {
                "username": "johndoe",
                "email": "john@example.com",
                "password": "SecurePass123!",
                "display_name": "John Doe",
                "character_type": "analyst",
                "bio": "Aspiring trader learning the markets",
                "avatar_url": "/avatars/default_1.png"
            }
        }


class UserLogin(BaseModel):
    """Schema for user login"""
    username_or_email: str = Field(..., description="Username or email")
    password: str = Field(..., description="Password")

    class Config:
        json_schema_extra = {
            "example": {
                "username_or_email": "johndoe",
                "password": "SecurePass123!"
            }
        }


class Token(BaseModel):
    """Schema for JWT token response"""
    access_token: str
    token_type: str = "bearer"
    expires_in: int  # seconds


class UserResponse(BaseModel):
    """Schema for user response (without password)"""
    user_id: UUID
    username: str
    email: str
    created_at: datetime
    last_login: Optional[datetime]
    is_active: bool

    class Config:
        from_attributes = True


class UserProfileResponse(BaseModel):
    """Schema for user profile response"""
    profile_id: UUID
    user_id: UUID
    character_type: str
    display_name: str
    avatar_url: Optional[str]
    bio: Optional[str]
    current_level: int
    current_xp: int
    total_xp: int
    can_change_character: bool
    character_changed_at: Optional[datetime]
    created_at: datetime
    updated_at: datetime

    class Config:
        from_attributes = True
        json_schema_extra = {
            "example": {
                "profile_id": "123e4567-e89b-12d3-a456-426614174000",
                "user_id": "123e4567-e89b-12d3-a456-426614174001",
                "character_type": "analyst",
                "display_name": "John Doe",
                "avatar_url": "/avatars/default_1.png",
                "bio": "Aspiring trader learning the markets",
                "current_level": 5,
                "current_xp": 250,
                "total_xp": 750,
                "can_change_character": True,
                "character_changed_at": None,
                "created_at": "2025-10-06T10:00:00Z",
                "updated_at": "2025-10-06T15:30:00Z"
            }
        }


class UserProfileUpdate(BaseModel):
    """Schema for updating user profile"""
    display_name: Optional[str] = Field(None, min_length=3, max_length=100)
    bio: Optional[str] = Field(None, max_length=280)
    avatar_url: Optional[str] = None

    class Config:
        json_schema_extra = {
            "example": {
                "display_name": "John \"The Analyst\" Doe",
                "bio": "Level 15 trader, specializing in fundamental analysis",
                "avatar_url": "/avatars/analyst_pro.png"
            }
        }


class PasswordResetRequest(BaseModel):
    """Schema for password reset request"""
    email: EmailStr

    class Config:
        json_schema_extra = {
            "example": {
                "email": "john@example.com"
            }
        }


class PasswordReset(BaseModel):
    """Schema for completing password reset"""
    token: str
    new_password: str = Field(..., min_length=8)

    @validator('new_password')
    def validate_password(cls, v):
        if len(v) < 8:
            raise ValueError('Password must be at least 8 characters')
        if not any(char.isdigit() for char in v):
            raise ValueError('Password must contain at least one number')
        if not any(char in '!@#$%^&*()_+-=[]{}|;:,.<>?' for char in v):
            raise ValueError('Password must contain at least one special character')
        return v

    class Config:
        json_schema_extra = {
            "example": {
                "token": "abc123def456",
                "new_password": "NewSecurePass456!"
            }
        }
