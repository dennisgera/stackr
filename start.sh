#!/bin/bash
# start.sh
set -e

# Create required directories
mkdir -p /var/log/nginx
mkdir -p /var/log/supervisor
mkdir -p /run/nginx
mkdir -p /var/run/supervisor
chmod 755 /var/run/supervisor

# Debug: Print environment variables (excluding sensitive data)
echo "Environment Configuration:"
env | grep -v "DATABASE_URL" | grep -v "PASSWORD"

# Debug: Test database connection
echo "Testing database connection..."
python3 << EOF
import os
import psycopg2
import time
import sys
import logging

logging.basicConfig(level=logging.DEBUG)
logger = logging.getLogger()

def test_db_connection(max_retries=5):
    url = os.getenv("DATABASE_URL")
    if not url:
        logger.error("DATABASE_URL not set")
        sys.exit(1)
    
    # Convert postgres:// to postgresql:// if necessary
    if url.startswith("postgres://"):
        url = url.replace("postgres://", "postgresql://")
    
    retry_count = 0
    while retry_count < max_retries:
        try:
            logger.info(f"Attempting connection (attempt {retry_count + 1})")
            conn = psycopg2.connect(url)
            cur = conn.cursor()
            cur.execute('SELECT version()')
            version = cur.fetchone()[0]
            logger.info(f"Connected to PostgreSQL: {version}")
            conn.close()
            return True
        except Exception as e:
            retry_count += 1
            logger.error(f"Connection attempt {retry_count} failed: {str(e)}")
            if retry_count < max_retries:
                time.sleep(2 ** retry_count)
            else:
                return False
    return False

if not test_db_connection():
    logger.error("Database connection failed after all retries")
    sys.exit(1)
EOF

# Start supervisord with debug output
echo "Starting supervisord..."
/usr/bin/supervisord -n -c /etc/supervisor/conf.d/supervisord.conf

# Note: The container will be kept running by supervisord