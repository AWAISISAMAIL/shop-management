from fastapi import APIRouter, Depends
from sqlalchemy.orm import Session
from sqlalchemy import func, desc
from datetime import date, datetime
from typing import List, Optional
from pydantic import BaseModel
from uuid import UUID

from database import get_db
from models import (
    Sale, SaleItem, Batch, BatchConsumption,
    Product, Expense, Udhar, User
)
from dependencies import get_current_user

router = APIRouter(prefix="/dashboard", tags=["dashboard"])

class LowStockItem(BaseModel):
    product_id: UUID
    brand: str
    size: str
    remaining_quantity: int

class BatchAlertItem(BaseModel):
    batch_number: str
    product_name: str
    completed_at: Optional[datetime] = None

class DashboardOut(BaseModel):
    today_sales: float
    today_profit_loss: float
    top_selling_product: Optional[str] = None
    most_sold_product: Optional[str] = None
    low_stock_alerts: List[LowStockItem] = []
    last_sale: Optional[dict] = None
    total_receivables: float
    total_payables: float
    current_inventory_value: float
    batch_alerts: List[BatchAlertItem] = []

def get_today_range():
    today = date.today()
    return today, today

@router.get("/", response_model=DashboardOut)
def get_dashboard(
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_user)
):
    today, _ = get_today_range()

    today_sales = db.query(func.sum(Sale.total_amount)).filter(
        Sale.sale_date == today,
        Sale.deleted_at == None
    ).scalar() or 0.0

    today_cogs = db.query(
        func.sum(BatchConsumption.quantity_taken * Batch.purchase_price_per_unit)
    ).select_from(BatchConsumption)\
     .join(SaleItem, BatchConsumption.sale_item_id == SaleItem.id)\
     .join(Sale, SaleItem.sale_id == Sale.id)\
     .join(Batch, BatchConsumption.batch_id == Batch.id)\
     .filter(
        Sale.sale_date == today,
        Sale.deleted_at == None,
        SaleItem.deleted_at == None
    ).scalar() or 0.0
    today_profit_loss = today_sales - today_cogs

    top = db.query(
        Product.brand, Product.size,
        func.sum(SaleItem.quantity).label("qty")
    ).join(SaleItem, SaleItem.product_id == Product.id)\
     .join(Sale, SaleItem.sale_id == Sale.id)\
     .filter(
        Sale.sale_date == today,
        Sale.deleted_at == None,
        SaleItem.deleted_at == None,
        Product.deleted_at == None
    ).group_by(Product.id, Product.brand, Product.size)\
     .order_by(desc("qty")).first()
    top_selling = f"{top.brand} {top.size or ''}".strip() if top else None

    most = db.query(
        Product.brand, Product.size,
        func.sum(SaleItem.quantity).label("qty")
    ).join(SaleItem, SaleItem.product_id == Product.id)\
     .join(Sale, SaleItem.sale_id == Sale.id)\
     .filter(
        Sale.deleted_at == None,
        SaleItem.deleted_at == None,
        Product.deleted_at == None
    ).group_by(Product.id, Product.brand, Product.size)\
     .order_by(desc("qty")).first()
    most_sold = f"{most.brand} {most.size or ''}".strip() if most else None

    low_rows = db.query(
        Product.id, Product.brand, Product.size,
        func.sum(Batch.remaining_quantity).label("total")
    ).join(Batch, Batch.product_id == Product.id)\
     .filter(
        Batch.remaining_quantity > 0,
        Batch.deleted_at == None,
        Product.deleted_at == None
    ).group_by(Product.id, Product.brand, Product.size)\
     .having(func.sum(Batch.remaining_quantity) < 5).all()
    low_stock = [LowStockItem(product_id=r.id, brand=r.brand, size=r.size, remaining_quantity=int(r.total)) for r in low_rows]

    last = db.query(Sale).filter(Sale.deleted_at == None)\
        .order_by(desc(Sale.sale_date), desc(Sale.sale_time)).first()
    last_sale = None
    if last:
        last_sale = {
            "sale_id": str(last.id),
            "date": last.sale_date.isoformat(),
            "time": last.sale_time.strftime("%H:%M:%S"),
            "total_amount": last.total_amount
        }

    receivables = db.query(func.sum(Udhar.amount - Udhar.paid_amount)).filter(
        Udhar.type == 'RECEIVABLE',
        Udhar.is_settled == False,
        Udhar.deleted_at == None
    ).scalar() or 0.0

    payables = db.query(func.sum(Udhar.amount - Udhar.paid_amount)).filter(
        Udhar.type == 'PAYABLE',
        Udhar.is_settled == False,
        Udhar.deleted_at == None
    ).scalar() or 0.0

    inv_value = db.query(
        func.sum(Batch.remaining_quantity * Batch.purchase_price_per_unit)
    ).filter(
        Batch.remaining_quantity > 0,
        Batch.deleted_at == None
    ).scalar() or 0.0

    completed = db.query(
        Batch.batch_number,
        Product.brand,
        Product.size,
        Batch.updated_at
    ).join(Product, Batch.product_id == Product.id)\
     .filter(
        Batch.is_completed == True,
        Batch.deleted_at == None
    ).order_by(desc(Batch.updated_at)).limit(5).all()
    batch_alerts = [BatchAlertItem(batch_number=r.batch_number, product_name=f"{r.brand} {r.size or ''}".strip(), completed_at=r.updated_at) for r in completed]

    return DashboardOut(
        today_sales=round(today_sales, 2),
        today_profit_loss=round(today_profit_loss, 2),
        top_selling_product=top_selling,
        most_sold_product=most_sold,
        low_stock_alerts=low_stock,
        last_sale=last_sale,
        total_receivables=round(receivables, 2),
        total_payables=round(payables, 2),
        current_inventory_value=round(inv_value, 2),
        batch_alerts=batch_alerts
    )