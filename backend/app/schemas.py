# backend/app/schemas.py
from pydantic import BaseModel, ConfigDict
from datetime import datetime
from typing import Optional

class ItemBase(BaseModel):
    name: str
    description: Optional[str] = None

class ItemCreate(ItemBase):
    pass

class Item(ItemBase):
    id: int
    created_at: datetime
    
    model_config = ConfigDict(from_attributes=True)

class InventoryRecordBase(BaseModel):
    item_id: int
    quantity: float
    updated_by: str

class InventoryRecordCreate(InventoryRecordBase):
    pass

class InventoryRecord(InventoryRecordBase):
    id: int
    timestamp: datetime
    
    model_config = ConfigDict(from_attributes=True)