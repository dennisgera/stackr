from fastapi import FastAPI, Depends
from sqlalchemy.orm import Session
from . import models, schemas, crud
from .database import SessionLocal, engine

models.Base.metadata.create_all(bind=engine)

app = FastAPI(title="Stackr API")

def get_db():
    db = SessionLocal()
    try:
        yield db
    finally:
        db.close()

@app.post("/items/", response_model=schemas.Item)
def create_item(item: schemas.ItemCreate, db: Session = Depends(get_db)):
    return crud.create_item(db=db, item=item)

@app.get("/items/", response_model=list[schemas.Item])
def read_items(skip: int = 0, limit: int = 100, db: Session = Depends(get_db)):
    return crud.get_items(db, skip=skip, limit=limit)

@app.post("/inventory/", response_model=schemas.InventoryRecord)
def update_inventory(record: schemas.InventoryRecordCreate, db: Session = Depends(get_db)):
    return crud.create_inventory_record(db=db, record=record)

@app.get("/inventory/{item_id}", response_model=list[schemas.InventoryRecord])
def read_item_inventory(item_id: int, db: Session = Depends(get_db)):
    return crud.get_item_inventory_history(db, item_id=item_id)