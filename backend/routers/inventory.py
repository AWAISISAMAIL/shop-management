from fastapi import APIRouter, Depends, HTTPException, status, Query
from sqlalchemy.orm import Session
from typing import List, Optional
from uuid import UUID
from datetime import datetime, date, time
from pydantic import BaseModel, ConfigDict

from database import get_db
from models import Category, Product, Batch, User
from dependencies import get_current_user

router = APIRouter(prefix="/inventory", tags=["inventory"])

# ---------- Pydantic Schemas ----------
class ProductCreate(BaseModel):
    category_id: str
    brand: str
    container_type: Optional[str] = None
    size: str
    custom_size: Optional[str] = None

class ProductUpdate(BaseModel):
    brand: Optional[str] = None
    container_type: Optional[str] = None
    size: Optional[str] = None
    custom_size: Optional[str] = None

class BatchCreate(BaseModel):
    product_id: str
    quantity: int
    packs: Optional[int] = None
    units_per_pack: Optional[int] = None
    purchase_price_per_unit: float
    selling_price_per_unit: float
    supplier: Optional[str] = None
    notes: Optional[str] = None

class CategoryOut(BaseModel):
    model_config = ConfigDict(from_attributes=True)
    id: UUID
    name: str
    description: Optional[str] = None

class ProductOut(BaseModel):
    model_config = ConfigDict(from_attributes=True)
    id: UUID
    category_id: UUID
    category_name: str = ""
    brand: str
    container_type: Optional[str] = None
    size: str
    custom_size: Optional[str] = None
    deleted_at: Optional[datetime] = None
    created_at: datetime

class BatchOut(BaseModel):
    model_config = ConfigDict(from_attributes=True)
    id: UUID
    batch_number: str
    product_id: UUID
    quantity: int
    remaining_quantity: int
    purchase_price_per_unit: float
    selling_price_per_unit: float
    supplier: Optional[str] = None
    is_completed: bool
    date_received: date
    time_received: time
    created_at: datetime

# ---------- Category Endpoints ----------
@router.get("/categories", response_model=List[CategoryOut])
def list_categories(db: Session = Depends(get_db)):
    return db.query(Category).all()

# ---------- Product CRUD ----------
@router.post("/products", response_model=ProductOut, status_code=status.HTTP_201_CREATED)
def create_product(
    product: ProductCreate,
    current_user: User = Depends(get_current_user),
    db: Session = Depends(get_db)
):
    cat = db.query(Category).filter(Category.id == product.category_id).first()
    if not cat:
        raise HTTPException(status_code=404, detail="Category not found")

    existing = db.query(Product).filter(
        Product.category_id == product.category_id,
        Product.brand == product.brand,
        Product.container_type == product.container_type,
        Product.size == product.size,
        Product.deleted_at == None
    ).first()
    if existing:
        raise HTTPException(status_code=400, detail="Product already exists")

    new_product = Product(
        category_id=product.category_id,
        brand=product.brand,
        container_type=product.container_type,
        size=product.size,
        custom_size=product.custom_size
    )
    db.add(new_product)
    db.commit()
    db.refresh(new_product)
    new_product.category_name = cat.name
    return new_product

@router.get("/products", response_model=List[ProductOut])
def list_products(
    category_id: Optional[str] = Query(None),
    search: Optional[str] = Query(None),
    db: Session = Depends(get_db)
):
    query = db.query(Product).filter(Product.deleted_at == None)
    if category_id:
        query = query.filter(Product.category_id == category_id)
    if search:
        query = query.filter(Product.brand.ilike(f"%{search}%"))
    products = query.all()
    for p in products:
        p.category_name = p.category.name if p.category else ""
    return products

@router.get("/products/{product_id}", response_model=ProductOut)
def get_product(product_id: str, db: Session = Depends(get_db)):
    product = db.query(Product).filter(Product.id == product_id, Product.deleted_at == None).first()
    if not product:
        raise HTTPException(status_code=404, detail="Product not found")
    product.category_name = product.category.name if product.category else ""
    return product

@router.put("/products/{product_id}", response_model=ProductOut)
def update_product(
    product_id: str,
    updates: ProductUpdate,
    current_user: User = Depends(get_current_user),
    db: Session = Depends(get_db)
):
    product = db.query(Product).filter(Product.id == product_id, Product.deleted_at == None).first()
    if not product:
        raise HTTPException(status_code=404, detail="Product not found")

    if updates.brand is not None:
        product.brand = updates.brand
    if updates.container_type is not None:
        product.container_type = updates.container_type
    if updates.size is not None:
        product.size = updates.size
    if updates.custom_size is not None:
        product.custom_size = updates.custom_size

    db.commit()
    db.refresh(product)
    product.category_name = product.category.name if product.category else ""
    return product

@router.delete("/products/{product_id}")
def soft_delete_product(
    product_id: str,
    current_user: User = Depends(get_current_user),
    db: Session = Depends(get_db)
):
    if current_user.role != "owner":
        raise HTTPException(status_code=403, detail="Only owner can delete products")

    product = db.query(Product).filter(Product.id == product_id, Product.deleted_at == None).first()
    if not product:
        raise HTTPException(status_code=404, detail="Product not found")

    product.deleted_at = datetime.utcnow()
    db.commit()
    return {"message": "Product soft-deleted"}

# ---------- Batch Entry ----------
@router.post("/batches", response_model=BatchOut, status_code=status.HTTP_201_CREATED)
def create_batch(
    batch: BatchCreate,
    current_user: User = Depends(get_current_user),
    db: Session = Depends(get_db)
):
    product = db.query(Product).filter(Product.id == batch.product_id, Product.deleted_at == None).first()
    if not product:
        raise HTTPException(status_code=404, detail="Product not found")

    new_batch = Batch(
        product_id=batch.product_id,
        batch_number=None,
        quantity=batch.quantity,
        remaining_quantity=batch.quantity,
        packs=batch.packs,
        units_per_pack=batch.units_per_pack,
        purchase_price_per_unit=batch.purchase_price_per_unit,
        selling_price_per_unit=batch.selling_price_per_unit,
        supplier=batch.supplier,
        notes=batch.notes,
        created_by=current_user.id
    )
    db.add(new_batch)
    db.commit()
    db.refresh(new_batch)
    return new_batch

@router.get("/batches", response_model=List[BatchOut])
def list_batches(
    product_id: Optional[str] = Query(None),
    db: Session = Depends(get_db)
):
    query = db.query(Batch).filter(Batch.deleted_at == None)
    if product_id:
        query = query.filter(Batch.product_id == product_id)
    batches = query.order_by(Batch.date_received.desc(), Batch.time_received.desc()).all()
    return batches