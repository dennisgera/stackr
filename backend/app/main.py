# backend/app/main.py
from fastapi import FastAPI, Depends, HTTPException, APIRouter
from fastapi.middleware.cors import CORSMiddleware
from fastapi.responses import JSONResponse
from fastapi.encoders import jsonable_encoder
from datetime import datetime
from requests import Request
from sqlalchemy.orm import Session
from sqlalchemy import text
import logging
import os
from . import schemas, crud
from .database import SessionLocal
from typing import List, Type, TypeVar

# Configure logging
logging.basicConfig(
    level=logging.DEBUG,
    format='%(asctime)s - %(name)s - %(levelname)s - %(message)s'
)
logger = logging.getLogger(__name__)

# Create type variables for generic type hints
SchemaType = TypeVar("SchemaType")

def serialize_sqlalchemy(db_model: any, schema_model: Type[SchemaType]) -> dict:
    """
    Generic function to convert SQLAlchemy model to Pydantic model and then to dict
    """
    # First convert to Pydantic model
    pydantic_model = schema_model.model_validate(db_model)
    
    # Then convert to dict with datetime handling
    return jsonable_encoder(pydantic_model)

def create_json_response(content: any, status_code: int = 200) -> JSONResponse:
    """
    Create a consistent JSON response with proper datetime handling
    """
    return JSONResponse(
        content=jsonable_encoder(content),
        status_code=status_code,
        media_type="application/json"
    )

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
    logger.info(f"Handling GET /items/ request with skip={skip}, limit={limit}")
    try:
        items = crud.get_items(db, skip=skip, limit=limit)
        result = [serialize_sqlalchemy(item, schemas.Item) for item in items]
        logger.info(f"Successfully retrieved {len(items)} items")
        logger.info(f"Returning items: {result}")  # Add this for debugging
        return create_json_response(result)
    except Exception as e:
        logger.error(f"Error fetching items: {str(e)}")
        return create_json_response(
            {"detail": str(e)},
            status_code=500
        )

@api_router.post("/items/", response_model=schemas.Item)
def create_item(item: schemas.ItemCreate, db: Session = Depends(get_db)):
    try:
        db_item = crud.create_item(db=db, item=item)
        return create_json_response(
            serialize_sqlalchemy(db_item, schemas.Item)
        )
    except HTTPException as he:
        raise he
    except Exception as e:
        logger.error(f"Error creating item: {str(e)}")
        raise HTTPException(status_code=500, detail=str(e))

@api_router.get("/inventory/{item_id}", response_model=List[schemas.InventoryRecord])
def read_item_inventory(item_id: int, db: Session = Depends(get_db)):
    try:
        records = crud.get_item_inventory_history(db, item_id=item_id)
        return create_json_response([
            serialize_sqlalchemy(record, schemas.InventoryRecord)
            for record in records
        ])
    except HTTPException as he:
        raise he
    except Exception as e:
        logger.error(f"Error fetching inventory history: {str(e)}")
        raise HTTPException(status_code=500, detail=str(e))

@api_router.post("/inventory/", response_model=schemas.InventoryRecord)
def update_inventory(record: schemas.InventoryRecordCreate, db: Session = Depends(get_db)):
    try:
        db_record = crud.create_inventory_record(db=db, record=record)
        return create_json_response(
            serialize_sqlalchemy(db_record, schemas.InventoryRecord)
        )
    except HTTPException as he:
        raise he
    except Exception as e:
        logger.error(f"Error updating inventory: {str(e)}")
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
            return create_json_response(response)
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
app.include_router(api_router)