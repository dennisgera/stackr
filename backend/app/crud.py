# backend/app/crud.py
from sqlalchemy.orm import Session
from . import models, schemas
from fastapi import HTTPException

def get_item(db: Session, item_id: int):
    return db.query(models.Item).filter(models.Item.id == item_id).first()

def get_item_by_name(db: Session, name: str):
    return db.query(models.Item).filter(models.Item.name == name).first()

def get_items(db: Session, skip: int = 0, limit: int = 100):
    return db.query(models.Item).offset(skip).limit(limit).all()

def create_item(db: Session, item: schemas.ItemCreate):
    # Check if item with same name already exists
    db_item = get_item_by_name(db, name=item.name)
    if db_item:
        raise HTTPException(status_code=400, detail="Item with this name already exists")
    
    db_item = models.Item(**item.model_dump())
    db.add(db_item)
    db.commit()
    db.refresh(db_item)
    return db_item

def get_item_inventory_history(db: Session, item_id: int):
    # First check if item exists
    item = get_item(db, item_id)
    if not item:
        raise HTTPException(status_code=404, detail="Item not found")
    
    return (db.query(models.InventoryRecord)
            .filter(models.InventoryRecord.item_id == item_id)
            .order_by(models.InventoryRecord.timestamp.desc())
            .all())

def create_inventory_record(db: Session, record: schemas.InventoryRecordCreate):
    # Check if item exists
    item = get_item(db, item_id=record.item_id)
    if not item:
        raise HTTPException(status_code=404, detail="Item not found")
    
    db_record = models.InventoryRecord(**record.model_dump())
    db.add(db_record)
    db.commit()
    db.refresh(db_record)
    return db_record