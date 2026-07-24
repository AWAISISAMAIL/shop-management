from fastapi import APIRouter, Depends, HTTPException, status, Query
from sqlalchemy.orm import Session
from typing import List, Optional
from uuid import UUID
from datetime import datetime, date
from pydantic import BaseModel, ConfigDict

from database import get_db
from models import Expense, User
from dependencies import get_current_user

router = APIRouter(prefix="/expenses", tags=["expenses"])

class ExpenseCreate(BaseModel):
    expense_type: str
    amount: float
    description: Optional[str] = None
    expense_date: Optional[date] = None
    notes: Optional[str] = None

class ExpenseOut(BaseModel):
    model_config = ConfigDict(from_attributes=True)
    id: UUID
    expense_type: str
    amount: float
    description: Optional[str] = None
    expense_date: date
    notes: Optional[str] = None
    created_by: UUID
    deleted_at: Optional[datetime] = None
    created_at: datetime

@router.post("/", response_model=ExpenseOut, status_code=status.HTTP_201_CREATED)
def create_expense(
    expense: ExpenseCreate,
    current_user: User = Depends(get_current_user),
    db: Session = Depends(get_db)
):
    expense_type_upper = expense.expense_type.upper()
    if expense_type_upper not in ["HOME", "SHOP"]:
        raise HTTPException(status_code=400, detail="Expense type must be HOME or SHOP")

    new_expense = Expense(
        expense_type=expense_type_upper,
        amount=expense.amount,
        description=expense.description,
        expense_date=expense.expense_date or datetime.utcnow().date(),
        notes=expense.notes,
        created_by=current_user.id
    )
    db.add(new_expense)
    db.commit()
    db.refresh(new_expense)
    return new_expense

@router.get("/", response_model=List[ExpenseOut])
def list_expenses(
    expense_type: Optional[str] = Query(None),
    from_date: Optional[date] = Query(None),
    to_date: Optional[date] = Query(None),
    db: Session = Depends(get_db)
):
    query = db.query(Expense).filter(Expense.deleted_at == None)

    if expense_type:
        expense_type_upper = expense_type.upper()
        if expense_type_upper not in ["HOME", "SHOP"]:
            raise HTTPException(status_code=400, detail="expense_type must be HOME or SHOP")
        query = query.filter(Expense.expense_type == expense_type_upper)
    if from_date:
        query = query.filter(Expense.expense_date >= from_date)
    if to_date:
        query = query.filter(Expense.expense_date <= to_date)

    return query.order_by(Expense.expense_date.desc()).all()

@router.get("/{expense_id}", response_model=ExpenseOut)
def get_expense(expense_id: str, db: Session = Depends(get_db)):
    expense = db.query(Expense).filter(Expense.id == expense_id, Expense.deleted_at == None).first()
    if not expense:
        raise HTTPException(status_code=404, detail="Expense not found")
    return expense

@router.delete("/{expense_id}")
def delete_expense(
    expense_id: str,
    current_user: User = Depends(get_current_user),
    db: Session = Depends(get_db)
):
    if current_user.role != "owner":
        raise HTTPException(status_code=403, detail="Only owner can delete expenses")

    expense = db.query(Expense).filter(Expense.id == expense_id, Expense.deleted_at == None).first()
    if not expense:
        raise HTTPException(status_code=404, detail="Expense not found")

    expense.deleted_at = datetime.utcnow()
    db.commit()
    return {"message": "Expense soft-deleted"}