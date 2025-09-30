"""
API mínima para testing de deployment en Vercel
"""
from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware
from datetime import datetime

app = FastAPI(title="Immermex Dashboard - Minimal API", version="1.0.0")

# Configurar CORS
app.add_middleware(
    CORSMiddleware,
    allow_origins=[
        "http://localhost:3000",
        "http://127.0.0.1:3000", 
        "https://edu-maass.github.io"
    ],
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

@app.get("/")
async def root():
    """Endpoint raíz"""
    return {
        "message": "Immermex Dashboard API - Minimal Version",
        "status": "running",
        "timestamp": datetime.utcnow().isoformat(),
        "version": "1.0.0"
    }

@app.get("/api/health")
async def health_check():
    """Health check básico"""
    return {
        "status": "healthy",
        "timestamp": datetime.utcnow().isoformat(),
        "database": "not_connected",  # Sin base de datos por ahora
        "version": "1.0.0"
    }

@app.get("/api/test")
async def test_endpoint():
    """Endpoint de prueba"""
    return {
        "success": True,
        "message": "Test endpoint working",
        "timestamp": datetime.utcnow().isoformat(),
        "data": {
            "test_value": "Hello from Vercel!",
            "environment": "production"
        }
    }

if __name__ == "__main__":
    import uvicorn
    uvicorn.run(app, host="0.0.0.0", port=8000)
