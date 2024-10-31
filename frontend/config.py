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


def get_api_url() -> str:
    """Get the API URL based on the environment"""
    environment = os.getenv("ENVIRONMENT", "development")
    logger.info(f"Current environment: {environment}")

    if environment == "production":
        # Always use the /api prefix in production
        api_host = os.getenv("API_HOST", "https://stackr-cold-violet-2349.fly.dev")
        base_url = f"{api_host}/api"
        logger.info(f"Using production API URL: {base_url}")
        return base_url
    else:
        # Development environment
        host = os.getenv("API_HOST", "http://backend")
        port = os.getenv("API_PORT", "8000")
        base_url = f"{host}:{port}"
        logger.info(f"Using development API URL: {base_url}")
        return base_url


def make_request(
    method: str, endpoint: str, max_retries: int = 3, retry_delay: int = 1, **kwargs
) -> Optional[requests.Response]:
    """
    Make a request to the API with enhanced error handling
    """
    base_url = get_api_url()

    # Ensure endpoint doesn't start with slash
    endpoint = endpoint.lstrip("/")

    # Construct full URL
    url = f"{base_url}/{endpoint}"
    logger.info(f"Making {method.upper()} request to: {url}")

    for attempt in range(max_retries):
        try:
            logger.info(f"Attempt {attempt + 1}/{max_retries}")
            response = requests.request(method, url, timeout=30, **kwargs)

            # Log response details
            logger.info(f"Response status code: {response.status_code}")
            logger.info(f"Response headers: {dict(response.headers)}")

            try:
                # If response is JSON, log it
                if "application/json" in response.headers.get("content-type", ""):
                    logger.info(f"JSON Response: {response.json()}")
                else:
                    logger.warning(
                        f"Non-JSON response received: {response.content[:200]}"
                    )
            except Exception as e:
                logger.error(f"Error parsing response: {str(e)}")

            # Handle redirect
            if response.history:
                logger.info(
                    f"Request was redirected: {[r.status_code for r in response.history]}"
                )

            # Check for successful response
            if response.status_code in (200, 201):
                if not response.content:
                    logger.warning("Empty response content")
                    return response

                try:
                    response.json()  # Validate JSON
                    return response
                except json.JSONDecodeError as e:
                    logger.error(f"Invalid JSON response: {str(e)}")
                    if attempt < max_retries - 1:
                        time.sleep(retry_delay * (attempt + 1))
                        continue
            else:
                logger.error(f"Request failed with status code: {response.status_code}")
                logger.error(f"Response content: {response.content[:200]}")
                st.error(f"API request failed: {response.status_code}")
                return None

        except requests.exceptions.RequestException as e:
            logger.error(f"Request failed: {str(e)}")
            if attempt < max_retries - 1:
                time.sleep(retry_delay * (attempt + 1))
                continue
            st.error("Failed to connect to the server")
            return None

    return None
