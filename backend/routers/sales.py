from fastapi import APIRouter, Depends, HTTPException, status, Query
from sqlalchemy.orm import Session
from typing import List, Optional
from uuid import UUID
from datetime import datetime, date, time
from pydantic import BaseModel, ConfigDict

from database import get_db
from models import Sale, SaleItem, Batch, BatchConsumption, Product, User
from dependencies import get_current_user

router = APIRouter(prefix="/sales", tags=["sales"])

class SaleItemCreate(BaseModel):
    product_id: str
    quantity: int

class SaleCreate(BaseModel):
    items: List[SaleItemCreate]

class SaleItemOut(BaseModel):
    model_config = ConfigDict(from_attributes=True)
    id: UUID
    product_id: UUID
    product_name: str = ""
    quantity: int
    unit_price: float
    total_price: float

class SaleOut(BaseModel):
    model_config = ConfigDict(from_attributes=True)
    id: UUID
    sale_date: date
    sale_time: time
    total_amount: float
    created_by: UUID
    created_at: datetime
    items: List[SaleItemOut] = []

@router.post("/", response_model=SaleOut, status_code=status.HTTP_201_CREATED)
def create_sale(
    sale_data: SaleCreate,
    current_user: User = Depends(get_current_user),
    db: Session = Depends(get_db)
):
    if not sale_data.items:
        raise HTTPException(status_code=400, detail="At least one item required")

    try:
        new_sale = Sale(
            sale_date=datetime.utcnow().date(),
            sale_time=datetime.utcnow().time(),
            total_amount=0.0,
            created_by=current_user.id
        )
        db.add(new_sale)
        db.flush()

        total_sale_amount = 0.0
        created_sale_items = []

        for requested in sale_data.items:
            product = db.query(Product).filter(
                Product.id == requested.product_id,
                Product.deleted_at == None
            ).first()
            if not product:
                raise HTTPException(status_code=404, detail=f"Product not found")

            batches = db.query(Batch).filter(
                Batch.product_id == requested.product_id,
                Batch.remaining_quantity > 0,
                Batch.deleted_at == None
            ).order_by(Batch.date_received.asc(), Batch.time_received.asc()).with_for_update().all()

            total_stock = sum(b.remaining_quantity for b in batches)
            if total_stock < requested.quantity:
                raise HTTPException(
                    status_code=400,
                    detail=f"Insufficient stock for {product.brand}. Need {requested.quantity}, have {total_stock}"
                )

            remaining_qty = requested.quantity

            for batch in batches:
                if remaining_qty <= 0:
                    break
                take = min(batch.remaining_quantity, remaining_qty)
                unit_price = batch.selling_price_per_unit
                item_total = unit_price * take

                sale_item = SaleItem(
                    sale_id=new_sale.id,
                    product_id=product.id,
                    quantity=take,
                    unit_price=unit_price,
                    total_price=item_total
                )
                db.add(sale_item)
                db.flush()

                batch.remaining_quantity -= take
                if batch.remaining_quantity == 0:
                    batch.is_completed = True

                consumption = BatchConsumption(
                    sale_item_id=sale_item.id,
                    batch_id=batch.id,
                    quantity_taken=take
                )
                db.add(consumption)

                created_sale_items.append(SaleItemOut(
                    id=sale_item.id,
                    product_id=product.id,
                    product_name=f"{product.brand} {product.size or ''}".strip(),
                    quantity=take,
                    unit_price=unit_price,
                    total_price=item_total
                ))

                remaining_qty -= take
                total_sale_amount += item_total

            if remaining_qty > 0:
                raise Exception("FIFO allocation failed")

        new_sale.total_amount = total_sale_amount
        db.commit()

        return SaleOut(
            id=new_sale.id,
            sale_date=new_sale.sale_date,
            sale_time=new_sale.sale_time,
            total_amount=new_sale.total_amount,
            created_by=new_sale.created_by,
            created_at=new_sale.created_at,
            items=created_sale_items
        )

    except HTTPException:
        db.rollback()
        raise
    except Exception as e:
        db.rollback()
        raise HTTPException(status_code=500, detail=f"Sale failed: {str(e)}")

@router.get("/", response_model=List[SaleOut])
def list_sales(
    from_date: Optional[date] = Query(None),
    to_date: Optional[date] = Query(None),
    db: Session = Depends(get_db)
):
    query = db.query(Sale).filter(Sale.deleted_at == None)
    if from_date:
        query = query.filter(Sale.sale_date >= from_date)
    if to_date:
        query = query.filter(Sale.sale_date <= to_date)
    sales = query.order_by(Sale.sale_date.desc(), Sale.sale_time.desc()).all()

    result = []
    for s in sales:
        items_out = []
        for si in s.items:
            product = si.product
            product_name = f"{product.brand} {product.size or ''}".strip() if product else "Unknown"
            items_out.append(SaleItemOut(
                id=si.id,
                product_id=si.product_id,
                product_name=product_name,
                quantity=si.quantity,
                unit_price=si.unit_price,
                total_price=si.total_price
            ))
        result.append(SaleOut(
            id=s.id,
            sale_date=s.sale_date,
            sale_time=s.sale_time,
            total_amount=s.total_amount,
            created_by=s.created_by,
            created_at=s.created_at,
            items=items_out
        ))
    return result