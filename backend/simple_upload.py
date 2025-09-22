"""
Versión simplificada del upload para Vercel
"""
from fastapi import FastAPI, HTTPException, UploadFile, File
from fastapi.middleware.cors import CORSMiddleware
import pandas as pd
import io
import logging

# Configurar logging
logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)

# Crear aplicación FastAPI
app = FastAPI(title="Immermex Upload API")

# Configurar CORS
app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

# Datos globales
processed_data = {
    "facturas": [],
    "cobranzas": [],
    "anticipos": [],
    "pedidos": []
}

@app.get("/")
async def root():
    return {"message": "Immermex Upload API funcionando"}

@app.get("/api/kpis")
async def get_kpis():
    """Obtener KPIs actuales"""
    facturas = processed_data["facturas"]
    
    if not facturas:
        return {
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
    
    facturacion_total = sum(f.get("monto_total", 0) for f in facturas)
    total_facturas = len(facturas)
    clientes_unicos = len(set(f.get("cliente", "") for f in facturas))
    
    return {
        "facturacion_total": facturacion_total,
        "cobranza_total": 0.0,
        "anticipos_total": 0.0,
        "porcentaje_cobrado": 0.0,
        "rotacion_inventario": 0.0,
        "total_facturas": total_facturas,
        "clientes_unicos": clientes_unicos,
        "aging_cartera": {},
        "top_clientes": {},
        "consumo_material": {}
    }

@app.post("/api/upload")
async def upload_file(file: UploadFile = File(...)):
    """Endpoint simplificado para subir archivos Excel"""
    try:
        # Validar tipo de archivo
        if not file.filename or not file.filename.endswith(('.xlsx', '.xls')):
            raise HTTPException(status_code=400, detail="Solo se permiten archivos Excel (.xlsx, .xls)")
        
        # Leer contenido del archivo
        contents = await file.read()
        logger.info(f"Archivo recibido: {file.filename} ({len(contents)} bytes)")
        
        # Validar tamaño (5MB máximo para Vercel)
        if len(contents) > 5 * 1024 * 1024:
            raise HTTPException(status_code=400, detail="El archivo es demasiado grande. Máximo 5MB")
        
        # Procesar archivo
        try:
            # Leer solo la hoja de facturación
            df = pd.read_excel(io.BytesIO(contents), sheet_name='facturacion', header=2)
            logger.info(f"Facturación leída: {len(df)} filas, {len(df.columns)} columnas")
            logger.info(f"Columnas: {list(df.columns)}")
            
            # Mapeo de columnas
            column_mapping = {
                'Fecha': 'fecha_factura',
                'Serie': 'serie_factura', 
                'Folio': 'folio_factura',
                'Razón Social': 'cliente',
                'Neto': 'monto_neto',
                'Total': 'monto_total',
                'Pendiente': 'saldo_pendiente',
                'UUID': 'uuid_factura'
            }
            
            # Renombrar columnas
            for old_col, new_col in column_mapping.items():
                if old_col in df.columns:
                    df = df.rename(columns={old_col: new_col})
            
            # Limpiar datos
            df = df.dropna(subset=['fecha_factura', 'cliente'])
            df['fecha_factura'] = pd.to_datetime(df['fecha_factura'], errors='coerce')
            df = df.dropna(subset=['fecha_factura'])
            
            # Convertir a formato esperado
            facturas = []
            for _, row in df.iterrows():
                factura = {
                    "fecha_factura": row.get("fecha_factura", "").strftime("%Y-%m-%d") if pd.notna(row.get("fecha_factura")) else "",
                    "serie": str(row.get("serie_factura", "")),
                    "folio": str(row.get("folio_factura", "")),
                    "cliente": str(row.get("cliente", "")),
                    "monto_neto": float(row.get("monto_neto", 0)) if pd.notna(row.get("monto_neto")) else 0.0,
                    "monto_total": float(row.get("monto_total", 0)) if pd.notna(row.get("monto_total")) else 0.0,
                    "saldo_pendiente": float(row.get("saldo_pendiente", 0)) if pd.notna(row.get("saldo_pendiente")) else 0.0,
                    "dias_credito": 30,
                    "agente": "",
                    "uuid": str(row.get("uuid_factura", ""))
                }
                facturas.append(factura)
            
            # Actualizar datos globales
            global processed_data
            processed_data["facturas"] = facturas
            
            logger.info(f"Facturas procesadas: {len(facturas)}")
            if facturas:
                logger.info(f"Primera factura: {facturas[0]}")
                total_montos = sum(f.get("monto_total", 0) for f in facturas[:5])
                logger.info(f"Suma de primeros 5 montos: {total_montos}")
            
            return {
                "message": "Archivo procesado exitosamente",
                "filename": file.filename,
                "processed_data": {
                    "facturas": len(facturas),
                    "cobranzas": 0,
                    "anticipos": 0,
                    "pedidos": 0
                },
                "kpis": await get_kpis()
            }
            
        except Exception as e:
            logger.error(f"Error procesando archivo: {e}")
            raise HTTPException(status_code=500, detail=f"Error procesando archivo: {str(e)}")
        
    except Exception as e:
        logger.error(f"Error general: {e}")
        raise HTTPException(status_code=500, detail=f"Error: {str(e)}")

if __name__ == "__main__":
    import uvicorn
    uvicorn.run(app, host="0.0.0.0", port=8000)
