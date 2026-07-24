from fastapi import APIRouter, Depends, Query, HTTPException
from sqlalchemy.orm import Session
from sqlalchemy import func
from typing import Optional, List
from datetime import date
from pydantic import BaseModel
from uuid import UUID

from database import get_db
from models import (
    Sale, SaleItem, Batch, BatchConsumption,
    Product, Category, Expense
)

router = APIRouter(prefix="/reports", tags=["reports"])

# ---------- Response Schemas ----------
class SalesSummaryOut(BaseModel):
    total_sales: int
    total_revenue: float
    total_items_sold: int

class BrandWiseSalesOut(BaseModel):
    brand: str
    total_quantity: int
    total_revenue: float

class CategoryWiseSalesOut(BaseModel):
    category_name: str
    total_quantity: int
    total_revenue: float

class BatchWiseSalesOut(BaseModel):
    batch_number: str
    product_name: str
    quantity_sold: int
    revenue: float
    cost: float
    profit: float

class RevenueOut(BaseModel):
    total_revenue: float

class ExpenseOut(BaseModel):
    total_home: float
    total_shop: float
    total_expenses: float

class ProfitLossOut(BaseModel):
    revenue: float
    cost_of_goods_sold: float
    gross_profit: float
    total_expenses: float
    net_profit: float

class RemainingInventoryItem(BaseModel):
    product_id: UUID
    brand: str
    size: str
    remaining_quantity: int
    batch_count: int
    total_value: float

class CurrentInventoryValueOut(BaseModel):
    total_value: float

# ---------- Helper ----------
def get_date_range(from_date: date, to_date: date):
    if from_date > to_date:
        raise HTTPException(status_code=400, detail="from_date cannot be after to_date")
    return from_date, to_date

# ---------- Endpoints ----------

@router.get("/sales-summary", response_model=SalesSummaryOut)
def sales_summary(
    from_date: date = Query(...),
    to_date: date = Query(...),
    db: Session = Depends(get_db)
):
    from_d, to_d = get_date_range(from_date, to_date)
    sales = db.query(Sale).filter(
        Sale.sale_date.between(from_d, to_d),
        Sale.deleted_at == None
    ).all()
    total_sales = len(sales)
    total_revenue = sum(s.total_amount for s in sales)
    total_items_sold = db.query(func.sum(SaleItem.quantity)).join(Sale).filter(
        Sale.sale_date.between(from_d, to_d),
        Sale.deleted_at == None,
        SaleItem.deleted_at == None
    ).scalar() or 0
    return SalesSummaryOut(
        total_sales=total_sales,
        total_revenue=round(total_revenue, 2),
        total_items_sold=int(total_items_sold)
    )

@router.get("/brand-wise-sales", response_model=List[BrandWiseSalesOut])
def brand_wise_sales(
    from_date: date = Query(...),
    to_date: date = Query(...),
    db: Session = Depends(get_db)
):
    from_d, to_d = get_date_range(from_date, to_date)
    results = db.query(
        Product.brand,
        func.sum(SaleItem.quantity).label("qty"),
        func.sum(SaleItem.total_price).label("rev")
    ).join(SaleItem, SaleItem.product_id == Product.id)\
     .join(Sale, SaleItem.sale_id == Sale.id)\
     .filter(
        Sale.sale_date.between(from_d, to_d),
        Sale.deleted_at == None,
        SaleItem.deleted_at == None,
        Product.deleted_at == None
    ).group_by(Product.brand).order_by(func.sum(SaleItem.total_price).desc()).all()
    return [BrandWiseSalesOut(brand=r.brand, total_quantity=int(r.qty), total_revenue=round(r.rev,2)) for r in results]

@router.get("/category-wise-sales", response_model=List[CategoryWiseSalesOut])
def category_wise_sales(
    from_date: date = Query(...),
    to_date: date = Query(...),
    db: Session = Depends(get_db)
):
    from_d, to_d = get_date_range(from_date, to_date)
    results = db.query(
        Category.name,
        func.sum(SaleItem.quantity).label("qty"),
        func.sum(SaleItem.total_price).label("rev")
    ).select_from(SaleItem)\
     .join(Product, SaleItem.product_id == Product.id)\
     .join(Category, Product.category_id == Category.id)\
     .join(Sale, SaleItem.sale_id == Sale.id)\
     .filter(
        Sale.sale_date.between(from_d, to_d),
        Sale.deleted_at == None,
        SaleItem.deleted_at == None,
        Product.deleted_at == None
    ).group_by(Category.name).order_by(func.sum(SaleItem.total_price).desc()).all()
    return [CategoryWiseSalesOut(category_name=r.name, total_quantity=int(r.qty), total_revenue=round(r.rev,2)) for r in results]

@router.get("/batch-wise-sales", response_model=List[BatchWiseSalesOut])
def batch_wise_sales(
    from_date: date = Query(...),
    to_date: date = Query(...),
    db: Session = Depends(get_db)
):
    from_d, to_d = get_date_range(from_date, to_date)
    results = db.query(
        Batch.batch_number,
        Product.brand,
        Product.size,
        func.sum(BatchConsumption.quantity_taken).label("qty"),
        func.sum(BatchConsumption.quantity_taken * SaleItem.unit_price).label("revenue"),
        func.sum(BatchConsumption.quantity_taken * Batch.purchase_price_per_unit).label("cost")
    ).select_from(BatchConsumption)\
     .join(SaleItem, BatchConsumption.sale_item_id == SaleItem.id)\
     .join(Sale, SaleItem.sale_id == Sale.id)\
     .join(Batch, BatchConsumption.batch_id == Batch.id)\
     .join(Product, Batch.product_id == Product.id)\
     .filter(
        Sale.sale_date.between(from_d, to_d),
        Sale.deleted_at == None,
        SaleItem.deleted_at == None,
        Batch.deleted_at == None
    ).group_by(Batch.batch_number, Product.brand, Product.size).order_by(Batch.batch_number).all()
    out = []
    for r in results:
        profit = (r.revenue or 0) - (r.cost or 0)
        out.append(BatchWiseSalesOut(
            batch_number=r.batch_number,
            product_name=f"{r.brand} {r.size or ''}".strip(),
            quantity_sold=int(r.qty or 0),
            revenue=round(r.revenue or 0, 2),
            cost=round(r.cost or 0, 2),
            profit=round(profit, 2)
        ))
    return out

@router.get("/revenue", response_model=RevenueOut)
def revenue(
    from_date: date = Query(...),
    to_date: date = Query(...),
    db: Session = Depends(get_db)
):
    from_d, to_d = get_date_range(from_date, to_date)
    total_rev = db.query(func.sum(Sale.total_amount)).filter(
        Sale.sale_date.between(from_d, to_d),
        Sale.deleted_at == None
    ).scalar() or 0.0
    return RevenueOut(total_revenue=round(total_rev, 2))

@router.get("/expenses", response_model=ExpenseOut)
def expenses_report(
    from_date: date = Query(...),
    to_date: date = Query(...),
    db: Session = Depends(get_db)
):
    from_d, to_d = get_date_range(from_date, to_date)
    home_exp = db.query(func.sum(Expense.amount)).filter(
        Expense.expense_date.between(from_d, to_d),
        Expense.expense_type == 'HOME',
        Expense.deleted_at == None
    ).scalar() or 0.0
    shop_exp = db.query(func.sum(Expense.amount)).filter(
        Expense.expense_date.between(from_d, to_d),
        Expense.expense_type == 'SHOP',
        Expense.deleted_at == None
    ).scalar() or 0.0
    return ExpenseOut(total_home=round(home_exp,2), total_shop=round(shop_exp,2), total_expenses=round(home_exp+shop_exp,2))

@router.get("/profit-loss", response_model=ProfitLossOut)
def profit_loss(
    from_date: date = Query(...),
    to_date: date = Query(...),
    db: Session = Depends(get_db)
):
    from_d, to_d = get_date_range(from_date, to_date)
    total_revenue = db.query(func.sum(Sale.total_amount)).filter(
        Sale.sale_date.between(from_d, to_d),
        Sale.deleted_at == None
    ).scalar() or 0.0
    cogs = db.query(
        func.sum(BatchConsumption.quantity_taken * Batch.purchase_price_per_unit)
    ).select_from(BatchConsumption)\
     .join(SaleItem, BatchConsumption.sale_item_id == SaleItem.id)\
     .join(Sale, SaleItem.sale_id == Sale.id)\
     .join(Batch, BatchConsumption.batch_id == Batch.id)\
     .filter(
        Sale.sale_date.between(from_d, to_d),
        Sale.deleted_at == None,
        SaleItem.deleted_at == None
    ).scalar() or 0.0
    gross_profit = total_revenue - cogs
    home_exp = db.query(func.sum(Expense.amount)).filter(
        Expense.expense_date.between(from_d, to_d),
        Expense.expense_type == 'HOME',
        Expense.deleted_at == None
    ).scalar() or 0.0
    shop_exp = db.query(func.sum(Expense.amount)).filter(
        Expense.expense_date.between(from_d, to_d),
        Expense.expense_type == 'SHOP',
        Expense.deleted_at == None
    ).scalar() or 0.0
    total_expenses = home_exp + shop_exp
    net_profit = gross_profit - total_expenses
    return ProfitLossOut(
        revenue=round(total_revenue, 2),
        cost_of_goods_sold=round(cogs, 2),
        gross_profit=round(gross_profit, 2),
        total_expenses=round(total_expenses, 2),
        net_profit=round(net_profit, 2)
    )

@router.get("/remaining-inventory", response_model=List[RemainingInventoryItem])
def remaining_inventory(
    category_id: Optional[str] = Query(None),
    search: Optional[str] = Query(None),
    db: Session = Depends(get_db)
):
    query = db.query(
        Product.id,
        Product.brand,
        Product.size,
        func.sum(Batch.remaining_quantity).label("total_qty"),
        func.count(Batch.id).label("batch_count"),
        func.sum(Batch.remaining_quantity * Batch.purchase_price_per_unit).label("total_val")
    ).join(Batch, Batch.product_id == Product.id)\
     .filter(
        Batch.remaining_quantity > 0,
        Batch.deleted_at == None,
        Product.deleted_at == None
    )
    if category_id:
        query = query.filter(Product.category_id == category_id)
    if search:
        query = query.filter(Product.brand.ilike(f"%{search}%"))

    query = query.group_by(Product.id, Product.brand, Product.size)\
                 .order_by(Product.brand)

    results = query.all()
    return [
        RemainingInventoryItem(
            product_id=r.id,
            brand=r.brand,
            size=r.size,
            remaining_quantity=int(r.total_qty),
            batch_count=r.batch_count,
            total_value=round(r.total_val, 2)
        ) for r in results
    ]

@router.get("/current-inventory-value", response_model=CurrentInventoryValueOut)
def current_inventory_value(db: Session = Depends(get_db)):
    total_val = db.query(
        func.sum(Batch.remaining_quantity * Batch.purchase_price_per_unit)
    ).filter(
        Batch.remaining_quantity > 0,
        Batch.deleted_at == None
    ).scalar() or 0.0
    return CurrentInventoryValueOut(total_value=round(total_val, 2))