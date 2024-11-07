# backend/app/crud.py
from typing import List, Optional
from sqlalchemy import desc
from sqlalchemy.orm import Session
import models
import schemas
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

def create_purchase(db: Session, purchase: schemas.PurchaseCreate) -> models.Purchase:
    """Create a new purchase and its associated lot if needed"""
    # Verify item exists
    item = get_item(db, purchase.item_id)
    if not item:
        raise HTTPException(status_code=404, detail="Item not found")
    
    # Create purchase record
    db_purchase = models.Purchase(
        item_id=purchase.item_id,
        quantity=purchase.quantity,
        purchase_type=purchase.purchase_type,
        supplier=purchase.supplier,
        price_per_unit=purchase.price_per_unit,
        created_by=purchase.created_by
    )
    db.add(db_purchase)
    db.flush()  # Flush to get the purchase ID
    
    # Create lot for imported items or if lot number is provided
    if purchase.purchase_type == models.PurchaseType.IMPORTED or purchase.lot_number:
        lot_number = purchase.lot_number or f"LOT-{db_purchase.id}"
        db_lot = models.Lot(
            purchase_id=db_purchase.id,
            lot_number=lot_number,
            manufacturing_date=purchase.manufacturing_date,
            expiry_date=purchase.expiry_date,
            remaining_quantity=purchase.quantity
        )
        db.add(db_lot)
    
    db.commit()
    db.refresh(db_purchase)
    return db_purchase

def get_purchase(db: Session, purchase_id: int) -> Optional[models.Purchase]:
    """Get a specific purchase by ID"""
    return db.query(models.Purchase).filter(models.Purchase.id == purchase_id).first()

def get_purchases(
    db: Session, 
    skip: int = 0, 
    limit: int = 100,
    item_id: Optional[int] = None
) -> List[models.Purchase]:
    """Get all purchases with optional filtering by item"""
    query = db.query(models.Purchase)
    if item_id is not None:
        query = query.filter(models.Purchase.item_id == item_id)
    return query.order_by(desc(models.Purchase.purchase_date)).offset(skip).limit(limit).all()

def get_available_lots(
    db: Session, 
    item_id: int,
    exclude_empty: bool = True
) -> List[models.Lot]:
    """Get available lots for an item, ordered by creation date (FIFO)"""
    query = (
        db.query(models.Lot)
        .join(models.Purchase)
        .filter(models.Purchase.item_id == item_id)
    )
    
    if exclude_empty:
        query = query.filter(models.Lot.remaining_quantity > 0)
    
    return query.order_by(models.Lot.id).all()

def create_inventory_record_with_lot(
    db: Session, 
    record: schemas.InventoryRecordCreate
) -> models.InventoryRecord:
    """Create inventory record with automatic or manual lot selection"""
    # Verify item exists
    item = get_item(db, record.item_id)
    if not item:
        raise HTTPException(status_code=404, detail="Item not found")
    
    # If lot_id is provided, verify it exists and has enough quantity
    if record.lot_id:
        lot = db.query(models.Lot).filter(models.Lot.id == record.lot_id).first()
        if not lot:
            raise HTTPException(status_code=404, detail="Lot not found")
        if lot.remaining_quantity < abs(record.quantity):
            raise HTTPException(
                status_code=400, 
                detail=f"Insufficient quantity in lot. Available: {lot.remaining_quantity}"
            )
        
        # Update lot quantity
        lot.remaining_quantity -= abs(record.quantity)
        lots_used = [(lot, abs(record.quantity))]
        
    # If no lot_id provided and quantity is negative (reduction)
    elif record.quantity < 0:
        lots_used = []
        remaining_quantity = abs(record.quantity)
        
        # Get available lots in FIFO order
        available_lots = get_available_lots(db, record.item_id)
        
        for lot in available_lots:
            if remaining_quantity <= 0:
                break
                
            quantity_from_lot = min(lot.remaining_quantity, remaining_quantity)
            lot.remaining_quantity -= quantity_from_lot
            remaining_quantity -= quantity_from_lot
            lots_used.append((lot, quantity_from_lot))
        
        if remaining_quantity > 0:
            raise HTTPException(
                status_code=400,
                detail=f"Insufficient quantity across all lots. Missing: {remaining_quantity}"
            )
    
    # Create inventory record
    db_record = models.InventoryRecord(
        item_id=record.item_id,
        quantity=record.quantity,
        updated_by=record.updated_by,
        lot_id=record.lot_id if record.lot_id else lots_used[0][0].id if lots_used else None
    )
    
    db.add(db_record)
    db.commit()
    db.refresh(db_record)
    return db_record

def get_lot(db: Session, lot_id: int) -> Optional[models.Lot]:
    """Get a specific lot by ID"""
    return db.query(models.Lot).filter(models.Lot.id == lot_id).first()

def get_lots(
    db: Session, 
    item_id: Optional[int] = None,
    skip: int = 0, 
    limit: int = 100
) -> List[models.Lot]:
    """Get all lots with optional filtering by item"""
    query = db.query(models.Lot).join(models.Purchase)
    if item_id is not None:
        query = query.filter(models.Purchase.item_id == item_id)
    return query.offset(skip).limit(limit).all()