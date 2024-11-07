from pydantic import BaseModel, ConfigDict
from datetime import datetime
from typing import Optional
from enum import Enum

class PurchaseType(str, Enum):
    DOMESTIC = "domestic"
    IMPORTED = "imported"

class ItemBase(BaseModel):
    name: str
    description: Optional[str] = None

class ItemCreate(ItemBase):
    pass

class Item(ItemBase):
    id: int
    created_at: datetime
    
    model_config = ConfigDict(from_attributes=True)

class PurchaseBase(BaseModel):
    item_id: int
    quantity: float
    purchase_type: PurchaseType
    supplier: str
    price_per_unit: float
    created_by: str

class PurchaseCreate(PurchaseBase):
    lot_number: Optional[str] = None
    manufacturing_date: Optional[datetime] = None
    expiry_date: Optional[datetime] = None

class Purchase(PurchaseBase):
    id: int
    purchase_date: datetime
    
    model_config = ConfigDict(from_attributes=True)

class LotBase(BaseModel):
    purchase_id: int
    lot_number: str
    manufacturing_date: Optional[datetime] = None
    expiry_date: Optional[datetime] = None
    remaining_quantity: float

class LotCreate(LotBase):
    pass

class Lot(LotBase):
    id: int
    
    model_config = ConfigDict(from_attributes=True)

class InventoryRecordBase(BaseModel):
    item_id: int
    quantity: float
    updated_by: str
    lot_id: Optional[int] = None  # Optional for domestic products

class InventoryRecordCreate(InventoryRecordBase):
    pass

class InventoryRecord(InventoryRecordBase):
    id: int
    timestamp: datetime
    
    model_config = ConfigDict(from_attributes=True)