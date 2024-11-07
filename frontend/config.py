# frontend/config.py
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
        host = os.getenv("API_HOST", "stackr-cold-violet-2349.fly.dev").rstrip("/")
        if not host.startswith("http"):
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
    method: str, endpoint: str, max_retries: int = 3, **kwargs
) -> Optional[requests.Response]:
    base_url = get_api_url()
    endpoint = endpoint.strip("/")
    url = f"{base_url}/api/{endpoint}"

    logger.info(f"Making {method} request to: {url}")

    session = requests.Session()
    headers = {
        "Accept": "application/json",
        "Content-Type": "application/json",
    }
    if "headers" in kwargs:
        headers.update(kwargs.pop("headers"))

    for attempt in range(max_retries):
        try:
            logger.info(f"Attempt {attempt + 1} of {max_retries}")
            response = session.request(
                method, url, headers=headers, timeout=30, **kwargs
            )

            logger.info(f"Response status: {response.status_code}")
            logger.info(f"Response headers: {dict(response.headers)}")
            logger.info(f"Response content: {response.content}")

            return response

        except requests.exceptions.RequestException as e:
            logger.error(f"Request failed: {str(e)}")
            if attempt == max_retries - 1:
                st.error(f"Failed to connect to server: {str(e)}")
            time.sleep(2**attempt)

    return None
