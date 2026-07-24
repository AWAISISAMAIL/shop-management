from pydantic import BaseModel, EmailStr, constr
from typing import Optional
from datetime import datetime

# ---------- Auth ----------
class UserCreate(BaseModel):
    email: EmailStr
    password: constr(min_length=6)

class UserLogin(BaseModel):
    email: EmailStr
    password: str

class TokenResponse(BaseModel):
    access_token: str
    refresh_token: str
    token_type: str = "bearer"

class RefreshTokenRequest(BaseModel):
    refresh_token: str

class PasswordResetRequest(BaseModel):
    email: EmailStr

class PasswordResetConfirm(BaseModel):
    token: str
    new_password: constr(min_length=6)

class MasterKeyReset(BaseModel):
    email: EmailStr
    master_key: str
    new_password: constr(min_length=6)

# ---------- User Out ----------
class UserOut(BaseModel):
    id: str
    email: str
    role: str
    is_active: bool

    class Config:
        from_attributes = True