from fastapi import APIRouter, Depends, HTTPException, status
from sqlalchemy.orm import Session
from database import get_db
from models import User, AuditLog, PasswordResetToken
from schemas import (
    UserCreate, UserLogin, TokenResponse,
    RefreshTokenRequest, PasswordResetRequest,
    PasswordResetConfirm, MasterKeyReset
)
from security import (
    hash_password, verify_password,
    create_access_token, create_refresh_token, decode_token
)
import uuid
from datetime import datetime, timedelta

router = APIRouter(prefix="/auth", tags=["auth"])

MAX_USERS = 5
MASTER_KEY = "ZENVORA"

@router.post("/signup", status_code=status.HTTP_201_CREATED)
def signup(user_data: UserCreate, db: Session = Depends(get_db)):
    if db.query(User).filter(User.email == user_data.email).first():
        raise HTTPException(status_code=400, detail="Email already registered")

    total_users = db.query(User).filter(User.is_active == True).count()
    if total_users >= MAX_USERS:
        raise HTTPException(status_code=400, detail="Maximum 5 users allowed")

    role = "owner" if total_users == 0 else "staff"

    new_user = User(
        email=user_data.email,
        password_hash=hash_password(user_data.password),
        role=role
    )
    db.add(new_user)
    db.commit()
    db.refresh(new_user)

    access_token = create_access_token(data={"sub": str(new_user.id), "role": new_user.role})
    refresh_token = create_refresh_token(data={"sub": str(new_user.id)})

    return {
        "message": f"User created as {role}",
        "access_token": access_token,
        "refresh_token": refresh_token,
        "token_type": "bearer",
        "role": role
    }

@router.post("/login", response_model=TokenResponse)
def login(user_data: UserLogin, db: Session = Depends(get_db)):
    user = db.query(User).filter(User.email == user_data.email, User.is_active == True).first()
    if not user or not verify_password(user_data.password, user.password_hash):
        raise HTTPException(status_code=401, detail="Invalid credentials")

    access_token = create_access_token(data={"sub": str(user.id), "role": user.role})
    refresh_token = create_refresh_token(data={"sub": str(user.id)})

    return {
        "access_token": access_token,
        "refresh_token": refresh_token,
        "token_type": "bearer"
    }

@router.post("/refresh", response_model=TokenResponse)
def refresh_token_endpoint(req: RefreshTokenRequest, db: Session = Depends(get_db)):
    try:
        payload = decode_token(req.refresh_token)
        if payload.get("type") != "refresh":
            raise HTTPException(status_code=401, detail="Invalid token type")
        user_id = payload.get("sub")
        user = db.query(User).filter(User.id == user_id, User.is_active == True).first()
        if not user:
            raise HTTPException(status_code=401, detail="User not found")
    except Exception:
        raise HTTPException(status_code=401, detail="Invalid or expired refresh token")

    new_access = create_access_token(data={"sub": user_id, "role": user.role})
    new_refresh = create_refresh_token(data={"sub": user_id})
    return {
        "access_token": new_access,
        "refresh_token": new_refresh,
        "token_type": "bearer"
    }

@router.post("/forgot-password")
def forgot_password(req: PasswordResetRequest, db: Session = Depends(get_db)):
    user = db.query(User).filter(User.email == req.email, User.is_active == True).first()
    if not user:
        raise HTTPException(status_code=404, detail="If email exists, a reset link has been sent")

    token_str = str(uuid.uuid4())
    expires = datetime.utcnow() + timedelta(hours=1)
    reset_entry = PasswordResetToken(
        user_id=user.id,
        token=token_str,
        expires_at=expires
    )
    db.add(reset_entry)
    db.commit()

    return {"message": "Password reset link sent", "reset_token": token_str}

@router.post("/reset-password")
def reset_password(req: PasswordResetConfirm, db: Session = Depends(get_db)):
    token_entry = db.query(PasswordResetToken).filter(
        PasswordResetToken.token == req.token,
        PasswordResetToken.used == False,
        PasswordResetToken.expires_at > datetime.utcnow()
    ).first()
    if not token_entry:
        raise HTTPException(status_code=400, detail="Invalid or expired token")

    user = db.query(User).filter(User.id == token_entry.user_id).first()
    if not user:
        raise HTTPException(status_code=404, detail="User not found")

    user.password_hash = hash_password(req.new_password)
    token_entry.used = True
    db.commit()

    audit = AuditLog(user_id=user.id, action="PASSWORD_RESET_TOKEN", details={"method": "email"})
    db.add(audit)
    db.commit()

    return {"message": "Password reset successfully"}

@router.post("/master-reset")
def master_key_reset(req: MasterKeyReset, db: Session = Depends(get_db)):
    if req.master_key != MASTER_KEY:
        raise HTTPException(status_code=403, detail="Invalid master key")

    user = db.query(User).filter(User.email == req.email, User.is_active == True).first()
    if not user:
        raise HTTPException(status_code=404, detail="User not found")

    user.password_hash = hash_password(req.new_password)
    db.commit()

    audit = AuditLog(user_id=user.id, action="PASSWORD_RESET_MASTER", details={"method": "master_key"})
    db.add(audit)
    db.commit()

    return {"message": "Password reset using master key"}