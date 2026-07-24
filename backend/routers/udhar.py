from fastapi import APIRouter, Depends, HTTPException, status, Query
from sqlalchemy.orm import Session
from typing import List, Optional
from uuid import UUID
from datetime import datetime, date
from pydantic import BaseModel, ConfigDict

from database import get_db
from models import Udhar, User
from dependencies import get_current_user

router = APIRouter(prefix="/udhar", tags=["udhar"])

class UdharCreate(BaseModel):
    customer_name: str
    amount: float
    type: str
    udhar_date: Optional[date] = None
    notes: Optional[str] = None

class UdharOut(BaseModel):
    model_config = ConfigDict(from_attributes=True)
    id: UUID
    customer_name: str
    amount: float
    paid_amount: float
    remaining_amount: float
    type: str
    udhar_date: date
    notes: Optional[str] = None
    is_settled: bool
    created_by: UUID
    deleted_at: Optional[datetime] = None
    created_at: datetime

class PaymentCreate(BaseModel):
    amount: float

def normalize_udhar_type(t: str) -> str:
    t_upper = t.upper()
    if t_upper not in ["RECEIVABLE", "PAYABLE"]:
        raise HTTPException(status_code=400, detail="Type must be RECEIVABLE or PAYABLE")
    return t_upper

def attach_remaining(udhar: Udhar):
    udhar.remaining_amount = round(udhar.amount - udhar.paid_amount, 2)

@router.post("/", response_model=UdharOut, status_code=status.HTTP_201_CREATED)
def create_udhar(
    udhar: UdharCreate,
    current_user: User = Depends(get_current_user),
    db: Session = Depends(get_db)
):
    udhar_type = normalize_udhar_type(udhar.type)

    new_udhar = Udhar(
        customer_name=udhar.customer_name,
        amount=udhar.amount,
        paid_amount=0.0,
        type=udhar_type,
        udhar_date=udhar.udhar_date or datetime.utcnow().date(),
        notes=udhar.notes,
        created_by=current_user.id
    )
    db.add(new_udhar)
    db.commit()
    db.refresh(new_udhar)
    attach_remaining(new_udhar)
    return new_udhar

@router.get("/", response_model=List[UdharOut])
def list_udhar(
    type: Optional[str] = Query(None),
    is_settled: Optional[bool] = Query(None),
    db: Session = Depends(get_db)
):
    query = db.query(Udhar).filter(Udhar.deleted_at == None)

    if type:
        udhar_type = normalize_udhar_type(type)
        query = query.filter(Udhar.type == udhar_type)
    if is_settled is not None:
        query = query.filter(Udhar.is_settled == is_settled)

    results = query.order_by(Udhar.udhar_date.desc()).all()
    for r in results:
        attach_remaining(r)
    return results

@router.get("/{udhar_id}", response_model=UdharOut)
def get_udhar(udhar_id: str, db: Session = Depends(get_db)):
    udhar = db.query(Udhar).filter(Udhar.id == udhar_id, Udhar.deleted_at == None).first()
    if not udhar:
        raise HTTPException(status_code=404, detail="Udhar entry not found")
    attach_remaining(udhar)
    return udhar

@router.post("/{udhar_id}/payment", response_model=UdharOut)
def add_payment(
    udhar_id: str,
    payment: PaymentCreate,
    current_user: User = Depends(get_current_user),
    db: Session = Depends(get_db)
):
    if payment.amount <= 0:
        raise HTTPException(status_code=400, detail="Payment amount must be positive")

    udhar = db.query(Udhar).filter(Udhar.id == udhar_id, Udhar.deleted_at == None).first()
    if not udhar:
        raise HTTPException(status_code=404, detail="Udhar entry not found")
    if udhar.is_settled:
        raise HTTPException(status_code=400, detail="Already fully settled")

    remaining = round(udhar.amount - udhar.paid_amount, 2)
    if payment.amount > remaining:
        raise HTTPException(status_code=400, detail=f"Payment exceeds remaining amount ({remaining})")

    udhar.paid_amount = round(udhar.paid_amount + payment.amount, 2)
    if udhar.paid_amount >= udhar.amount:
        udhar.is_settled = True
        udhar.paid_amount = udhar.amount

    db.commit()
    db.refresh(udhar)
    attach_remaining(udhar)
    return udhar

@router.put("/{udhar_id}/settle", response_model=UdharOut)
def settle_udhar(
    udhar_id: str,
    current_user: User = Depends(get_current_user),
    db: Session = Depends(get_db)
):
    udhar = db.query(Udhar).filter(Udhar.id == udhar_id, Udhar.deleted_at == None).first()
    if not udhar:
        raise HTTPException(status_code=404, detail="Udhar entry not found")
    if udhar.is_settled:
        raise HTTPException(status_code=400, detail="Already settled")

    udhar.paid_amount = udhar.amount
    udhar.is_settled = True
    db.commit()
    db.refresh(udhar)
    attach_remaining(udhar)
    return udhar

@router.delete("/{udhar_id}")
def delete_udhar(
    udhar_id: str,
    current_user: User = Depends(get_current_user),
    db: Session = Depends(get_db)
):
    if current_user.role != "owner":
        raise HTTPException(status_code=403, detail="Only owner can delete udhar entries")

    udhar = db.query(Udhar).filter(Udhar.id == udhar_id, Udhar.deleted_at == None).first()
    if not udhar:
        raise HTTPException(status_code=404, detail="Udhar entry not found")

    udhar.deleted_at = datetime.utcnow()
    db.commit()
    return {"message": "Udhar entry soft-deleted"}