import uuid
from datetime import datetime, date, time
from sqlalchemy import (
    Column, String, Integer, Float, Boolean, Date, Time, Text,
    DateTime, ForeignKey, CheckConstraint, Index
)
from sqlalchemy.dialects.postgresql import UUID, INET, JSONB
from sqlalchemy.orm import relationship
from database import Base

# 1. User
class User(Base):
    __tablename__ = "users"

    id = Column(UUID(as_uuid=True), primary_key=True, default=uuid.uuid4)
    email = Column(String(255), unique=True, nullable=False)
    password_hash = Column(String(255), nullable=False)
    role = Column(String(10), nullable=False, default="staff")
    is_active = Column(Boolean, default=True)
    created_at = Column(DateTime(timezone=True), default=datetime.utcnow)
    updated_at = Column(DateTime(timezone=True), onupdate=datetime.utcnow)

    batches = relationship("Batch", back_populates="creator")
    sales = relationship("Sale", back_populates="creator")
    expenses = relationship("Expense", back_populates="creator")
    udhars = relationship("Udhar", back_populates="creator")

# 2. Category
class Category(Base):
    __tablename__ = "categories"

    id = Column(UUID(as_uuid=True), primary_key=True, default=uuid.uuid4)
    name = Column(String(50), unique=True, nullable=False)
    description = Column(Text)

    products = relationship("Product", back_populates="category")

# 3. Product
class Product(Base):
    __tablename__ = "products"

    id = Column(UUID(as_uuid=True), primary_key=True, default=uuid.uuid4)
    category_id = Column(UUID(as_uuid=True), ForeignKey("categories.id"), nullable=False)
    brand = Column(String(100), nullable=False)
    container_type = Column(String(50))
    size = Column(String(50), nullable=False)
    custom_size = Column(String(50))
    deleted_at = Column(DateTime(timezone=True))
    created_at = Column(DateTime(timezone=True), default=datetime.utcnow)
    updated_at = Column(DateTime(timezone=True), onupdate=datetime.utcnow)

    category = relationship("Category", back_populates="products")
    batches = relationship("Batch", back_populates="product")
    sale_items = relationship("SaleItem", back_populates="product")

    __table_args__ = (
        Index("uq_product", "category_id", "brand", "container_type", "size",
              unique=True,
              postgresql_where=(deleted_at == None)),
    )

# 4. Batch
class Batch(Base):
    __tablename__ = "batches"

    id = Column(UUID(as_uuid=True), primary_key=True, default=uuid.uuid4)
    product_id = Column(UUID(as_uuid=True), ForeignKey("products.id"), nullable=False)
    batch_number = Column(String(20), unique=True, nullable=False)
    quantity = Column(Integer, CheckConstraint("quantity > 0"), nullable=False)
    remaining_quantity = Column(Integer, CheckConstraint("remaining_quantity >= 0"), nullable=False)
    packs = Column(Integer, CheckConstraint("packs >= 0"))
    units_per_pack = Column(Integer, CheckConstraint("units_per_pack >= 0"))
    purchase_price_per_unit = Column(Float, nullable=False)
    selling_price_per_unit = Column(Float, nullable=False)
    supplier = Column(String(255))
    notes = Column(Text)
    is_completed = Column(Boolean, default=False)
    date_received = Column(Date, default=datetime.utcnow().date)
    time_received = Column(Time, default=datetime.utcnow().time)
    created_by = Column(UUID(as_uuid=True), ForeignKey("users.id"), nullable=False)
    deleted_at = Column(DateTime(timezone=True))
    created_at = Column(DateTime(timezone=True), default=datetime.utcnow)
    updated_at = Column(DateTime(timezone=True), onupdate=datetime.utcnow)

    product = relationship("Product", back_populates="batches")
    creator = relationship("User", back_populates="batches")
    consumptions = relationship("BatchConsumption", back_populates="batch")

    __table_args__ = (
        CheckConstraint("remaining_quantity <= quantity", name="batch_remaining_valid"),
    )

# 5. Sale
class Sale(Base):
    __tablename__ = "sales"

    id = Column(UUID(as_uuid=True), primary_key=True, default=uuid.uuid4)
    sale_date = Column(Date, default=datetime.utcnow().date)
    sale_time = Column(Time, default=datetime.utcnow().time)
    total_amount = Column(Float, nullable=False)
    created_by = Column(UUID(as_uuid=True), ForeignKey("users.id"), nullable=False)
    deleted_at = Column(DateTime(timezone=True))
    created_at = Column(DateTime(timezone=True), default=datetime.utcnow)

    creator = relationship("User", back_populates="sales")
    items = relationship("SaleItem", back_populates="sale")

# 6. SaleItem
class SaleItem(Base):
    __tablename__ = "sale_items"

    id = Column(UUID(as_uuid=True), primary_key=True, default=uuid.uuid4)
    sale_id = Column(UUID(as_uuid=True), ForeignKey("sales.id"), nullable=False)
    product_id = Column(UUID(as_uuid=True), ForeignKey("products.id"), nullable=False)
    quantity = Column(Integer, CheckConstraint("quantity > 0"), nullable=False)
    unit_price = Column(Float, nullable=False)
    total_price = Column(Float, nullable=False)
    deleted_at = Column(DateTime(timezone=True))
    created_at = Column(DateTime(timezone=True), default=datetime.utcnow)

    sale = relationship("Sale", back_populates="items")
    product = relationship("Product", back_populates="sale_items")
    batch_consumptions = relationship("BatchConsumption", back_populates="sale_item")

# 7. BatchConsumption
class BatchConsumption(Base):
    __tablename__ = "batch_consumption"

    id = Column(UUID(as_uuid=True), primary_key=True, default=uuid.uuid4)
    sale_item_id = Column(UUID(as_uuid=True), ForeignKey("sale_items.id"), nullable=False)
    batch_id = Column(UUID(as_uuid=True), ForeignKey("batches.id"), nullable=False)
    quantity_taken = Column(Integer, CheckConstraint("quantity_taken > 0"), nullable=False)
    created_at = Column(DateTime(timezone=True), default=datetime.utcnow)

    sale_item = relationship("SaleItem", back_populates="batch_consumptions")
    batch = relationship("Batch", back_populates="consumptions")

# 8. Expense
class Expense(Base):
    __tablename__ = "expenses"

    id = Column(UUID(as_uuid=True), primary_key=True, default=uuid.uuid4)
    expense_type = Column(String(10), CheckConstraint("expense_type IN ('HOME','SHOP')"), nullable=False)
    amount = Column(Float, nullable=False)
    description = Column(Text)
    expense_date = Column(Date, default=datetime.utcnow().date)
    notes = Column(Text)
    created_by = Column(UUID(as_uuid=True), ForeignKey("users.id"), nullable=False)
    deleted_at = Column(DateTime(timezone=True))
    created_at = Column(DateTime(timezone=True), default=datetime.utcnow)

    creator = relationship("User", back_populates="expenses")

# 9. Udhar
class Udhar(Base):
    __tablename__ = "udhar"

    id = Column(UUID(as_uuid=True), primary_key=True, default=uuid.uuid4)
    customer_name = Column(String(255), nullable=False)
    amount = Column(Float, nullable=False)
    paid_amount = Column(Float, default=0.0, nullable=False)
    type = Column(String(12), CheckConstraint("type IN ('RECEIVABLE','PAYABLE')"), nullable=False)
    udhar_date = Column(Date, default=datetime.utcnow().date)
    notes = Column(Text)
    is_settled = Column(Boolean, default=False)
    created_by = Column(UUID(as_uuid=True), ForeignKey("users.id"), nullable=False)
    deleted_at = Column(DateTime(timezone=True))
    created_at = Column(DateTime(timezone=True), default=datetime.utcnow)

    creator = relationship("User", back_populates="udhars")

# 10. AuditLog
class AuditLog(Base):
    __tablename__ = "audit_logs"

    id = Column(UUID(as_uuid=True), primary_key=True, default=uuid.uuid4)
    user_id = Column(UUID(as_uuid=True), ForeignKey("users.id"))
    action = Column(String(100), nullable=False)
    details = Column(JSONB)
    ip_address = Column(INET)
    created_at = Column(DateTime(timezone=True), default=datetime.utcnow)

# 11. PasswordResetToken
class PasswordResetToken(Base):
    __tablename__ = "password_reset_tokens"

    id = Column(UUID(as_uuid=True), primary_key=True, default=uuid.uuid4)
    user_id = Column(UUID(as_uuid=True), ForeignKey("users.id"), nullable=False)
    token = Column(String(255), unique=True, nullable=False)
    expires_at = Column(DateTime(timezone=True), nullable=False)
    used = Column(Boolean, default=False)
    created_at = Column(DateTime(timezone=True), default=datetime.utcnow)