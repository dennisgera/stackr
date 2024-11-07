from sqlalchemy import Column, Integer, String, Float, DateTime, ForeignKey, Enum, func
from sqlalchemy.ext.declarative import declarative_base
from sqlalchemy.orm import relationship

from schemas import PurchaseType

Base = declarative_base()

class Item(Base):
    __tablename__ = "items"
    
    id = Column(Integer, primary_key=True, index=True)
    name = Column(String, unique=True, index=True)
    description = Column(String, nullable=True)
    created_at = Column(DateTime(timezone=True), server_default=func.now())
    
    # Relationships
    purchases = relationship("Purchase", back_populates="item")
    inventory_records = relationship("InventoryRecord", back_populates="item")

class Purchase(Base):
    __tablename__ = "purchases"
    
    id = Column(Integer, primary_key=True, index=True)
    item_id = Column(Integer, ForeignKey("items.id"))
    quantity = Column(Float)
    purchase_date = Column(DateTime(timezone=True), server_default=func.now())
    purchase_type = Column(Enum(PurchaseType))
    supplier = Column(String)
    price_per_unit = Column(Float)
    created_by = Column(String)
    
    # Relationships
    item = relationship("Item", back_populates="purchases")
    lot = relationship("Lot", back_populates="purchase", uselist=False)

class Lot(Base):
    __tablename__ = "lots"
    
    id = Column(Integer, primary_key=True, index=True)
    purchase_id = Column(Integer, ForeignKey("purchases.id"))
    lot_number = Column(String, unique=True, index=True)
    manufacturing_date = Column(DateTime(timezone=True), nullable=True)
    expiry_date = Column(DateTime(timezone=True), nullable=True)
    remaining_quantity = Column(Float)
    
    # Relationships
    purchase = relationship("Purchase", back_populates="lot")
    inventory_records = relationship("InventoryRecord", back_populates="lot")

class InventoryRecord(Base):
    __tablename__ = "inventory_records"
    
    id = Column(Integer, primary_key=True, index=True)
    item_id = Column(Integer, ForeignKey("items.id"))
    lot_id = Column(Integer, ForeignKey("lots.id"), nullable=True)
    quantity = Column(Float)
    timestamp = Column(DateTime(timezone=True), server_default=func.now())
    updated_by = Column(String)
    
    # Relationships
    item = relationship("Item", back_populates="inventory_records")
    lot = relationship("Lot", back_populates="inventory_records")