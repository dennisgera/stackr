# backend/app/main.py
from fastapi import FastAPI, Depends, HTTPException, APIRouter
from fastapi.middleware.cors import CORSMiddleware
from datetime import datetime
from requests import Request
from sqlalchemy.orm import Session
from sqlalchemy import text
import logging
import os
from . import schemas, crud
from .database import SessionLocal
from typing import List, Optional

# Configure logging
logging.basicConfig(
    level=logging.DEBUG,
    format='%(asctime)s - %(name)s - %(levelname)s - %(message)s'
)
logger = logging.getLogger(__name__)

# Create an API router
api_router = APIRouter()

def get_db():
    db = SessionLocal()
    try:
        yield db
    finally:
        db.close()

@api_router.get("/items/", response_model=List[schemas.Item])
async def read_items(skip: int = 0, limit: int = 100, db: Session = Depends(get_db)):
    logger.info("Handling GET /items/ request")
    try:
        return crud.get_items(db, skip=skip, limit=limit)
    except Exception as e:
        logger.error(f"Error in /items/: {str(e)}", exc_info=True)
        raise HTTPException(status_code=500, detail=str(e))

@api_router.post("/items/", response_model=schemas.Item)
def create_item(item: schemas.ItemCreate, db: Session = Depends(get_db)):
    try:
        return crud.create_item(db=db, item=item)
    except HTTPException as he:
        raise he
    except Exception as e:
        logger.error(f"Error creating item: {str(e)}")
        raise HTTPException(status_code=500, detail=str(e))

@api_router.get("/inventory/{item_id}", response_model=List[schemas.InventoryRecord])
def read_item_inventory(item_id: int, db: Session = Depends(get_db)):
    try:
        return crud.get_item_inventory_history(db, item_id=item_id)
    except HTTPException as he:
        raise he
    except Exception as e:
        logger.error(f"Error fetching inventory history: {str(e)}")
        raise HTTPException(status_code=500, detail=str(e))

@api_router.post("/inventory/", response_model=schemas.InventoryRecord)
def update_inventory(record: schemas.InventoryRecordCreate, db: Session = Depends(get_db)):
    try:
        return crud.create_inventory_record(db=db, record=record)
    except HTTPException as he:
        raise he
    except Exception as e:
        logger.error(f"Error updating inventory: {str(e)}")
        raise HTTPException(status_code=500, detail=str(e))
    

@api_router.post("/purchases/", response_model=schemas.Purchase)
def create_purchase(
    purchase: schemas.PurchaseCreate,
    db: Session = Depends(get_db)
):
    """Create a new purchase with optional lot information"""
    try:
        return crud.create_purchase(db=db, purchase=purchase)
    except HTTPException as he:
        raise he
    except Exception as e:
        logger.error(f"Error creating purchase: {str(e)}")
        raise HTTPException(status_code=500, detail=str(e))

@api_router.get("/purchases/", response_model=List[schemas.Purchase])
def read_purchases(
    skip: int = 0,
    limit: int = 100,
    item_id: Optional[int] = None,
    db: Session = Depends(get_db)
):
    """Get all purchases with optional item filtering"""
    try:
        return crud.get_purchases(db, skip=skip, limit=limit, item_id=item_id)
    except Exception as e:
        logger.error(f"Error fetching purchases: {str(e)}")
        raise HTTPException(status_code=500, detail=str(e))

@api_router.get("/purchases/{purchase_id}", response_model=schemas.Purchase)
def read_purchase(purchase_id: int, db: Session = Depends(get_db)):
    """Get a specific purchase by ID"""
    purchase = crud.get_purchase(db, purchase_id=purchase_id)
    if purchase is None:
        raise HTTPException(status_code=404, detail="Purchase not found")
    return purchase

@api_router.get("/lots/", response_model=List[schemas.Lot])
def read_lots(
    skip: int = 0,
    limit: int = 100,
    item_id: Optional[int] = None,
    db: Session = Depends(get_db)
):
    """Get all lots with optional item filtering"""
    try:
        return crud.get_lots(db, item_id=item_id, skip=skip, limit=limit)
    except Exception as e:
        logger.error(f"Error fetching lots: {str(e)}")
        raise HTTPException(status_code=500, detail=str(e))

@api_router.get("/lots/{lot_id}", response_model=schemas.Lot)
def read_lot(lot_id: int, db: Session = Depends(get_db)):
    """Get a specific lot by ID"""
    lot = crud.get_lot(db, lot_id=lot_id)
    if lot is None:
        raise HTTPException(status_code=404, detail="Lot not found")
    return lot

@api_router.get("/items/{item_id}/lots", response_model=List[schemas.Lot])
def read_item_lots(
    item_id: int,
    exclude_empty: bool = True,
    db: Session = Depends(get_db)
):
    """Get available lots for a specific item"""
    try:
        return crud.get_available_lots(db, item_id=item_id, exclude_empty=exclude_empty)
    except Exception as e:
        logger.error(f"Error fetching item lots: {str(e)}")
        raise HTTPException(status_code=500, detail=str(e))

# Create the FastAPI application
app = FastAPI(
    title="Stackr API",
    docs_url="/docs",
    openapi_url="/openapi.json"
)

# Add health check endpoints that don't use the /api prefix
@app.get("/health")
async def health_check():
    try:
        db = SessionLocal()
        try:
            logger.info("Running health check...")
            result = db.execute(text("SELECT 1")).scalar()
            db.commit()
            response = {
                "status": "healthy",
                "timestamp": datetime.now().isoformat(),
                "database": "connected",
                "check_value": result
            }
            logger.info(f"Health check response: {response}")
            return response
        finally:
            db.close()
    except Exception as e:
        logger.error(f"Health check failed: {str(e)}")
        raise HTTPException(status_code=500, detail=str(e))
    
@app.middleware("http")
async def log_requests(request: Request, call_next):
    logger.info("====== Request Start ======")
    logger.info(f"Method: {request.method}")
    logger.info(f"URL: {request.url}")
    logger.info(f"Path: {request.url.path}")
    logger.info(f"Headers: {dict(request.headers)}")
    logger.info(f"Query Params: {dict(request.query_params)}")
    
    response = await call_next(request)
    
    logger.info(f"Response Status: {response.status_code}")
    logger.info("====== Request End ======")
    return response

# Configure CORS
origins = []
if os.getenv("ENVIRONMENT") == "development":
    origins = [
        "http://localhost",
        "http://localhost:8501",
        "http://127.0.0.1:8501",
    ]
else:
    origins = [
        "https://stackr-cold-violet-2349.fly.dev",
        os.getenv("API_HOST", "https://stackr-cold-violet-2349.fly.dev"),
    ]

app.add_middleware(
    CORSMiddleware,
    allow_origins=origins,
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

# Include the API router
app.include_router(api_router, prefix="/api")