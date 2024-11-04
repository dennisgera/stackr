# frontend/config.py
import json
import os
import streamlit as st
import requests
from typing import Optional
import logging
import time

# Configure logging
logging.basicConfig(level=logging.DEBUG)
logger = logging.getLogger(__name__)

class APIError(Exception):
    pass

# frontend/config.py
def get_api_url() -> str:
    environment = os.getenv("ENVIRONMENT", "development")
    logger.info(f"Current environment: {environment}")
    
    if environment == "production":
        host = os.getenv("API_HOST", "stackr-cold-violet-2349.fly.dev").rstrip('/')
        if not host.startswith('http'):
            host = f"https://{host}"
        logger.info(f"Using production API URL: {host}")
        return host
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
    base_url = get_api_url().rstrip('/')
    endpoint = endpoint.strip('/')
    
    url = f"{base_url}/api/{endpoint}"
    
    session = requests.Session()
    headers = {
        'Accept': 'application/json',
        'Content-Type': 'application/json',
    }
    if 'headers' in kwargs:
        headers.update(kwargs.pop('headers'))
    
    last_error = None
    logger.info(f"Making {method} request to {url}")
    for attempt in range(max_retries):
        try:
            logger.info(f"Attempt {attempt + 1}/{max_retries}")
            
            response = session.request(
                method,
                url,
                headers=headers,
                timeout=30,
                allow_redirects=True,
                **kwargs
            )
            
            logger.info(f"Response status code: {response.status_code}")
            logger.info(f"Response headers: {dict(response.headers)}")
            logger.info(f"Response content type: {response.headers.get('content-type', '')}")
            
            if response.status_code == 404:
                logger.warning(f"404 Not Found for URL: {url}")
                continue
            
            # Try to parse JSON
            try:
                response.json()
                return response
            except json.JSONDecodeError as e:
                logger.error(f"Failed to parse JSON: {str(e)}")
                last_error = e
                continue
            
        except requests.exceptions.RequestException as e:
            logger.error(f"Request failed: {str(e)}")
            last_error = e
            if attempt < max_retries - 1:
                time.sleep(retry_delay * (attempt + 1))
                continue

    # If we get here, all attempts failed
    error_message = str(last_error) if last_error else "Failed to reach the server"
    st.error(f"Failed to connect to the server: {error_message}")
    return None