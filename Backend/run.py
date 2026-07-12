"""
Development entrypoint. Use this for running locally.
For production, use: uvicorn app.main:app --host 0.0.0.0 --port 8000
"""
import uvicorn
from app.config import settings

if __name__ == "__main__":
    uvicorn.run(
        "app.main:app",
        host=settings.APP_HOST,
        port=settings.APP_PORT,
        reload=(settings.APP_ENV == "development"),
        log_level="info",
    )
