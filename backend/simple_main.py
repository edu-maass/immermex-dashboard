"""
API REST simplificada para Immermex Dashboard (sin pandas)
"""

from fastapi import FastAPI, HTTPException, UploadFile, File
from fastapi.middleware.cors import CORSMiddleware
from fastapi.responses import JSONResponse
import json
import os
from datetime import datetime
import logging
import pandas as pd
import io

# Configurar logging
logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)

# Crear aplicación FastAPI
app = FastAPI(
    title="Immermex Dashboard API (Simple)",
    description="API REST simplificada para dashboard de indicadores financieros",
    version="1.0.0"
)

# Configurar CORS
app.add_middleware(
    CORSMiddleware,
    allow_origins=[
        "http://localhost:3000", 
        "http://127.0.0.1:3000",
        "https://edu-maass.github.io",
        "https://immermex-dashboard.vercel.app"
    ],
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

# Almacenamiento en memoria de datos procesados
processed_data = {
    "facturas": [],
    "anticipos": [],
    "inventario": []
}

# Datos de prueba por defecto
default_kpis = {
    "facturacion_total": 0.0,
    "cobranza_total": 0.0,
    "anticipos_total": 0.0,
    "porcentaje_cobrado": 0.0,
    "rotacion_inventario": 0.0,
    "total_facturas": 0,
    "clientes_unicos": 0,
    "aging_cartera": {},
    "top_clientes": {},
    "consumo_material": {}
}

def calculate_kpis():
    """Calcula KPIs basados en los datos procesados"""
    facturas = processed_data["facturas"]
    anticipos = processed_data["anticipos"]
    inventario = processed_data["inventario"]
    
    if not facturas:
        return default_kpis
    
    # Cálculos básicos
    facturacion_total = sum(f.get("total", 0) for f in facturas)
    cobranza_total = sum(f.get("cobrado", 0) for f in facturas)
    anticipos_total = sum(a.get("monto", 0) for a in anticipos)
    total_facturas = len(facturas)
    clientes_unicos = len(set(f.get("cliente", "") for f in facturas))
    
    # Porcentaje cobrado
    porcentaje_cobrado = (cobranza_total / facturacion_total * 100) if facturacion_total > 0 else 0
    
    # Aging de cartera (simulado basado en fechas)
    aging_cartera = {
        "0-30 días": len([f for f in facturas if f.get("dias_vencimiento", 0) <= 30]),
        "31-60 días": len([f for f in facturas if 31 <= f.get("dias_vencimiento", 0) <= 60]),
        "61-90 días": len([f for f in facturas if 61 <= f.get("dias_vencimiento", 0) <= 90]),
        "90+ días": len([f for f in facturas if f.get("dias_vencimiento", 0) > 90])
    }
    
    # Top clientes
    clientes_totales = {}
    for f in facturas:
        cliente = f.get("cliente", "")
        if cliente:
            clientes_totales[cliente] = clientes_totales.get(cliente, 0) + f.get("total", 0)
    
    top_clientes = dict(sorted(clientes_totales.items(), key=lambda x: x[1], reverse=True)[:5])
    
    # Consumo de material (simulado)
    consumo_material = {
        "Acero Inoxidable 304": sum(f.get("total", 0) * 0.3 for f in facturas),
        "Aluminio 6061": sum(f.get("total", 0) * 0.25 for f in facturas),
        "Cobre C11000": sum(f.get("total", 0) * 0.2 for f in facturas),
        "Bronce C83600": sum(f.get("total", 0) * 0.15 for f in facturas),
        "Titanio Grade 2": sum(f.get("total", 0) * 0.1 for f in facturas)
    }
    
    # Rotación de inventario (simulado)
    rotacion_inventario = (facturacion_total / 100000) if facturacion_total > 0 else 0
    
    return {
        "facturacion_total": round(facturacion_total, 2),
        "cobranza_total": round(cobranza_total, 2),
        "anticipos_total": round(anticipos_total, 2),
        "porcentaje_cobrado": round(porcentaje_cobrado, 2),
        "rotacion_inventario": round(rotacion_inventario, 2),
        "total_facturas": total_facturas,
        "clientes_unicos": clientes_unicos,
        "aging_cartera": aging_cartera,
        "top_clientes": top_clientes,
        "consumo_material": consumo_material
    }

@app.on_event("startup")
async def startup_event():
    logger.info("API simplificada iniciada correctamente")

@app.get("/")
async def root():
    """Endpoint de salud de la API"""
    return {"message": "Immermex Dashboard API (Simple)", "status": "active"}

@app.get("/api/health")
async def health_check():
    """Endpoint de verificación de salud"""
    return {"status": "healthy", "timestamp": datetime.now().isoformat()}

@app.get("/api/kpis")
async def get_kpis():
    """Obtiene KPIs principales del dashboard"""
    try:
        return calculate_kpis()
    except Exception as e:
        logger.error(f"Error obteniendo KPIs: {str(e)}")
        raise HTTPException(status_code=500, detail=str(e))

@app.get("/api/graficos/aging")
async def get_grafico_aging():
    """Obtiene datos para gráfico de aging de cartera"""
    try:
        kpis = calculate_kpis()
        aging = kpis["aging_cartera"]
        return {
            "labels": list(aging.keys()),
            "data": list(aging.values()),
            "titulo": "Aging de Cartera"
        }
    except Exception as e:
        logger.error(f"Error obteniendo gráfico de aging: {str(e)}")
        raise HTTPException(status_code=500, detail=str(e))

@app.get("/api/graficos/top-clientes")
async def get_grafico_top_clientes(limite: int = 10):
    """Obtiene datos para gráfico de top clientes"""
    try:
        kpis = calculate_kpis()
        clientes = kpis["top_clientes"]
        labels = list(clientes.keys())[:limite]
        data = list(clientes.values())[:limite]
        return {
            "labels": labels,
            "data": data,
            "titulo": f"Top {limite} Clientes por Facturación"
        }
    except Exception as e:
        logger.error(f"Error obteniendo gráfico de top clientes: {str(e)}")
        raise HTTPException(status_code=500, detail=str(e))

@app.get("/api/graficos/consumo-material")
async def get_grafico_consumo_material(limite: int = 10):
    """Obtiene datos para gráfico de consumo por material"""
    try:
        kpis = calculate_kpis()
        materiales = kpis["consumo_material"]
        labels = list(materiales.keys())[:limite]
        data = list(materiales.values())[:limite]
        return {
            "labels": labels,
            "data": data,
            "titulo": f"Top {limite} Materiales por Consumo"
        }
    except Exception as e:
        logger.error(f"Error obteniendo gráfico de consumo de material: {str(e)}")
        raise HTTPException(status_code=500, detail=str(e))

@app.get("/api/archivos")
async def get_archivos_procesados():
    """Obtiene lista de archivos procesados (simulado)"""
    try:
        return [
            {
                "id": 1,
                "nombre_archivo": "datos_prueba_immermex.xlsx",
                "fecha_procesamiento": "2024-01-15T10:30:00",
                "registros_procesados": 100,
                "estado": "procesado",
                "mes": 1,
                "año": 2024
            }
        ]
    except Exception as e:
        logger.error(f"Error obteniendo archivos: {str(e)}")
        raise HTTPException(status_code=500, detail=str(e))

@app.post("/api/upload")
async def upload_file(file: UploadFile = File(...)):
    """Endpoint para subir archivos Excel"""
    try:
        # Validar tipo de archivo
        if not file.filename.endswith(('.xlsx', '.xls')):
            raise HTTPException(status_code=400, detail="Solo se permiten archivos Excel (.xlsx, .xls)")
        
        logger.info(f"Procesando archivo: {file.filename}")
        
        # Leer contenido del archivo
        contents = await file.read()
        
        # Procesar con pandas
        df = pd.read_excel(io.BytesIO(contents))
        
        # Limpiar datos procesados anteriores
        processed_data["facturas"] = []
        processed_data["anticipos"] = []
        processed_data["inventario"] = []
        
        registros_procesados = 0
        
        # Procesar cada fila del Excel
        for index, row in df.iterrows():
            try:
                # Mapear columnas comunes (ajustar según tu estructura de Excel)
                factura = {
                    "numero_pedido": str(row.get("Número de Pedido", f"PED-{index+1}")),
                    "cliente": str(row.get("Cliente", f"Cliente {index+1}")),
                    "agente": str(row.get("Agente", "N/A")),
                    "fecha_factura": str(row.get("Fecha Factura", datetime.now().strftime("%Y-%m-%d"))),
                    "total": float(row.get("Total", 0)),
                    "cobrado": float(row.get("Cobrado", 0)),
                    "dias_vencimiento": int(row.get("Días Vencimiento", 30))
                }
                
                processed_data["facturas"].append(factura)
                registros_procesados += 1
                
                # Procesar anticipos si existe la columna
                if "Anticipo" in row and pd.notna(row["Anticipo"]) and row["Anticipo"] > 0:
                    anticipo = {
                        "numero_pedido": factura["numero_pedido"],
                        "monto": float(row["Anticipo"]),
                        "fecha": factura["fecha_factura"]
                    }
                    processed_data["anticipos"].append(anticipo)
                
            except Exception as e:
                logger.warning(f"Error procesando fila {index}: {str(e)}")
                continue
        
        logger.info(f"Procesados {registros_procesados} registros de {file.filename}")
        
        return {
            "mensaje": "Archivo procesado exitosamente",
            "nombre_archivo": file.filename,
            "registros_procesados": registros_procesados,
            "fecha_procesamiento": datetime.now().isoformat(),
            "estado": "procesado"
        }
    except Exception as e:
        logger.error(f"Error procesando archivo: {str(e)}")
        raise HTTPException(status_code=500, detail=str(e))

if __name__ == "__main__":
    import uvicorn
    print("🚀 Iniciando servidor Immermex Dashboard (Simple)")
    print("📊 Backend: http://localhost:8000")
    print("📚 API Docs: http://localhost:8000/docs")
    print("🔄 Frontend: http://localhost:3000")
    print("=" * 50)
    
    uvicorn.run(
        "simple_main:app",
        host="0.0.0.0",
        port=8000,
        reload=True,
        log_level="info"
    )
