# stackr

## Tech Stack
- Backend: FastAPI (Python) - Modern, fast, easy to use
- Frontend: Streamlit - Quick to build, Python-based UI
- Database: PostgreSQL - Reliable, good for time-series data
- Infrastructure: Docker + DigitalOcean
- CI/CD: GitHub Actions
- Monitoring: Sentry (free tier)

## Initial Setup Steps

1. Create and activate virtual environment:
```bash
python -m venv venv
source venv/bin/activate  # On Windows: venv\Scripts\activate
```

2. Install initial dependencies:
```bash
pip install fastapi uvicorn sqlalchemy psycopg2-binary streamlit pandas python-dotenv pytest
```

3. Environment variables (.env):
```
DATABASE_URL=postgresql://user:password@db:5432/inventory
ENVIRONMENT=development
SENTRY_DSN=your-sentry-dsn
```