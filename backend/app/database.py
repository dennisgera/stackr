# backend/app/database.py
from sqlalchemy import create_engine, text
from sqlalchemy.orm import sessionmaker
import os
from dotenv import load_dotenv
import logging
import time
from urllib.parse import urlparse
import models

# Configure logging
logging.basicConfig(level=logging.DEBUG)
logger = logging.getLogger(__name__)

load_dotenv()

def get_database_url():
    """Get database URL with proper formatting for SQLAlchemy"""
    url = os.getenv("DATABASE_URL")
    if not url:
        raise ValueError("DATABASE_URL environment variable is not set")
    
    logger.info("Original DATABASE_URL retrieved")
    
    # Handle different URL formats
    if url.startswith("postgres://"):
        url = url.replace("postgres://", "postgresql://")
        logger.info("Converted postgres:// to postgresql://")
    
    # Parse the URL for debugging (mask password)
    parsed = urlparse(url)
    debug_url = f"{parsed.scheme}://{parsed.username}:****@{parsed.hostname}:{parsed.port}{parsed.path}"
    logger.info(f"Configured database URL (masked): {debug_url}")
    
    return url

def create_db_engine(max_retries=5):
    """Create database engine with enhanced error handling"""
    retry_count = 0
    last_exception = None
    
    while retry_count < max_retries:
        try:
            logger.info(f"Attempting to create database engine (attempt {retry_count + 1})")
            url = get_database_url()
            
            # Configure engine with minimal connection pooling for Fly.io
            engine = create_engine(
                url,
                pool_size=5,
                max_overflow=2,
                pool_timeout=30,
                pool_recycle=1800,
                pool_pre_ping=True,
                connect_args={
                    "application_name": "stackr_app",
                    "connect_timeout": 10,
                    "keepalives": 1,
                    "keepalives_idle": 30,
                    "keepalives_interval": 10,
                    "keepalives_count": 5
                }
            )
            
            # Test the connection
            logger.info("Testing database connection...")
            with engine.connect() as conn:
                conn.execute(text("SELECT 1"))
                conn.commit()
                logger.info("Database connection test successful")
            
            return engine
            
        except Exception as e:
            retry_count += 1
            last_exception = e
            logger.error(f"Database connection attempt {retry_count} failed: {str(e)}")
            
            if retry_count < max_retries:
                wait_time = 2 ** retry_count
                logger.info(f"Waiting {wait_time} seconds before retry...")
                time.sleep(wait_time)
    
    logger.error("All database connection attempts failed")
    raise Exception(f"Failed to connect to database after {max_retries} attempts. Last error: {str(last_exception)}")

# Initialize database engine and session factory
engine = create_db_engine()
SessionLocal = sessionmaker(autocommit=False, autoflush=False, bind=engine)

def init_db():
    """Initialize database tables"""
    try:
        logger.info("Creating database tables...")
        models.Base.metadata.create_all(bind=engine)
        logger.info("Database tables created successfully")
    except Exception as e:
        logger.error(f"Failed to create database tables: {str(e)}")
        raise