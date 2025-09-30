"""
API Ultra-Minimal para Debug de Deployment
"""
from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware
from datetime import datetime

# Crear aplicación FastAPI
app = FastAPI(title="Immermex API - Minimal", version="1.0.0")

# CORS básico
app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

@app.get("/")
async def root():
    """Endpoint raíz"""
    return {
        "message": "Immermex API - Minimal Version",
        "status": "running",
        "timestamp": datetime.utcnow().isoformat()
    }

@app.get("/api/health")
async def health():
    """Health check"""
    return {
        "status": "healthy",
        "timestamp": datetime.utcnow().isoformat()
    }

@app.get("/api/test")
async def test():
    """Test endpoint"""
    return {
        "success": True,
        "message": "Test OK",
        "timestamp": datetime.utcnow().isoformat()
    }

if __name__ == "__main__":
    import uvicorn
    uvicorn.run(app, host="0.0.0.0", port=8000)
