from datetime import datetime
from contextlib import asynccontextmanager
from fastapi import FastAPI, Depends, HTTPException
from fastapi.middleware.cors import CORSMiddleware
from fastapi.responses import JSONResponse
from sqlalchemy.orm import Session
from sqlalchemy import text
import logging
import os
from . import schemas, crud
from .database import SessionLocal, init_db

# Configure logging
logging.basicConfig(
    level=logging.DEBUG,
    format='%(asctime)s - %(name)s - %(levelname)s - %(message)s'
)
logger = logging.getLogger(__name__)

@asynccontextmanager
async def lifespan(app: FastAPI):
    """
    Lifespan context manager for startup and shutdown events
    """
    try:
        # Startup
        logger.info("Starting up FastAPI application...")
        init_db()  # Initialize database tables
        logger.info("Database initialized successfully")
        yield
    except Exception as e:
        logger.error(f"Startup failed: {str(e)}")
        raise
    finally:
        logger.info("Shutting down FastAPI application...")

app = FastAPI(
    title="Stackr API",
    lifespan=lifespan
)

def get_db():
    db = SessionLocal()
    try:
        yield db
    finally:
        db.close()

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

# Add error handler for all exceptions
@app.exception_handler(Exception)
async def global_exception_handler(request, exc):
    logger.error(f"Global error handler caught: {str(exc)}")
    return JSONResponse(
        status_code=500,
        content={"detail": str(exc)}
    )

@app.get("/health")
async def health_check():
    """
    Health check endpoint with database connection test
    """
    try:
        db = SessionLocal()
        try:
            # Test database connection using text()
            result = db.execute(text("SELECT 1")).scalar()
            db.commit()
            
            return {
                "status": "healthy",
                "timestamp": datetime.now().isoformat(),
                "database": "connected",
                "check_value": result
            }
        finally:
            db.close()
    except Exception as e:
        logger.error(f"Health check failed: {str(e)}")
        raise HTTPException(
            status_code=500,
            detail=f"Service unhealthy: {str(e)}"
        )


# Update the items endpoint to always return JSON
@app.get("/items/")
async def read_items(skip: int = 0, limit: int = 100, db: Session = Depends(get_db)):
    try:
        items = crud.get_items(db, skip=skip, limit=limit)
        return JSONResponse(
            content=[item.dict() for item in items],
            status_code=200
        )
    except Exception as e:
        logger.error(f"Error fetching items: {str(e)}")
        return JSONResponse(
            content={"detail": str(e)},
            status_code=500
        )

@app.post("/items/", response_model=schemas.Item)
def create_item(item: schemas.ItemCreate, db: Session = Depends(get_db)):
    try:
        return crud.create_item(db=db, item=item)
    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"Error creating item: {str(e)}")
        raise HTTPException(status_code=500, detail=str(e))

@app.get("/inventory/{item_id}", response_model=list[schemas.InventoryRecord])
def read_item_inventory(item_id: int, db: Session = Depends(get_db)):
    try:
        return crud.get_item_inventory_history(db, item_id=item_id)
    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"Error fetching inventory history: {str(e)}")
        raise HTTPException(status_code=500, detail=str(e))

@app.post("/inventory/", response_model=schemas.InventoryRecord)
def update_inventory(record: schemas.InventoryRecordCreate, db: Session = Depends(get_db)):
    try:
        return crud.create_inventory_record(db=db, record=record)
    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"Error updating inventory: {str(e)}")
        raise HTTPException(status_code=500, detail=str(e))