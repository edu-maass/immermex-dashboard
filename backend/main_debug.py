"""
API mínima para debug de deployment en Vercel
"""

from fastapi import FastAPI
from datetime import datetime
import os

app = FastAPI(title="Debug API")

@app.get("/")
async def root():
    return {
        "message": "Debug API funcionando",
        "timestamp": datetime.now().isoformat(),
        "environment": os.getenv("ENVIRONMENT", "unknown")
    }

@app.get("/test")
async def test():
    return {"test": "OK"}
