import os
import streamlit as st
import requests
from typing import Optional
import json
import logging
import time

# Configure logging
logging.basicConfig(level=logging.DEBUG)
logger = logging.getLogger(__name__)

class APIError(Exception):
    pass

def get_api_url() -> str:
    """Get the API URL based on the environment"""
    environment = os.getenv("ENVIRONMENT", "development")
    logger.info(f"Current environment: {environment}")
    
    if environment == "production":
        host = os.getenv("API_HOST", "stackr-cold-violet-2349.fly.dev").rstrip('/')
        if not host.startswith('http'):
            host = f"https://{host}"
        base_url = f"{host}/api"
        logger.info(f"Using production API URL: {base_url}")
        return base_url
    else:
        host = os.getenv("API_HOST", "http://backend")
        port = os.getenv("API_PORT", "8000")
        base_url = f"{host}:{port}"
        logger.info(f"Using development API URL: {base_url}")
        return base_url

def make_request(
    method: str,
    endpoint: str,
    max_retries: int = 3,
    retry_delay: int = 1,
    **kwargs
) -> Optional[requests.Response]:
    """
    Make a request to the API with enhanced error handling
    """
    base_url = get_api_url()
    # Ensure consistent path handling
    endpoint = endpoint.strip('/')
    url = f"{base_url}/{endpoint}"
    
    logger.info(f"Making {method.upper()} request to: {url}")
    
    session = requests.Session()
    
    # Set default headers
    headers = {
        'Accept': 'application/json',
        'Content-Type': 'application/json',
    }
    # Update with any custom headers
    if 'headers' in kwargs:
        headers.update(kwargs.pop('headers'))
    
    for attempt in range(max_retries):
        try:
            logger.info(f"Attempt {attempt + 1}/{max_retries}")
            
            response = session.request(
                method,
                url,
                headers=headers,
                timeout=30,
                allow_redirects=True,  # Follow redirects
                **kwargs
            )
            
            logger.info(f"Response status code: {response.status_code}")
            logger.info(f"Response headers: {dict(response.headers)}")
            
            if response.history:
                logger.info(f"Request was redirected: {' -> '.join(str(r.url) for r in response.history)}")
                logger.info(f"Final URL: {response.url}")
            
            # Check content type
            content_type = response.headers.get('content-type', '')
            if 'json' not in content_type:
                logger.error(f"Unexpected content type: {content_type}")
                logger.error(f"Response content: {response.content[:200]}")
                if attempt < max_retries - 1:
                    time.sleep(retry_delay * (attempt + 1))
                    continue
                raise APIError(f"Expected JSON response, got {content_type}")
            
            # Try to parse response
            try:
                response.json()
                return response
            except json.JSONDecodeError as e:
                logger.error(f"Failed to parse JSON: {str(e)}")
                logger.error(f"Response content: {response.content[:200]}")
                if attempt < max_retries - 1:
                    time.sleep(retry_delay * (attempt + 1))
                    continue
                raise APIError("Invalid JSON response from server")
            
        except requests.exceptions.RequestException as e:
            logger.error(f"Request failed: {str(e)}")
            if attempt < max_retries - 1:
                time.sleep(retry_delay * (attempt + 1))
                continue
            st.error("Failed to connect to the server. Please try again later.")
            return None
        
        except APIError as e:
            logger.error(f"API Error: {str(e)}")
            st.error(str(e))
            return None
        
        except Exception as e:
            logger.error(f"Unexpected error: {str(e)}")
            if attempt < max_retries - 1:
                time.sleep(retry_delay * (attempt + 1))
                continue
            st.error(f"An unexpected error occurred: {str(e)}")
            return None
    
    return None