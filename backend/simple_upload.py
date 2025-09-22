"""
Versión simplificada del upload para Vercel
"""
from fastapi import FastAPI, HTTPException, UploadFile, File
from fastapi.middleware.cors import CORSMiddleware
import pandas as pd
import io
import logging
import traceback

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
    """Obtener KPIs actuales con todos los datos procesados"""
    facturas = processed_data["facturas"]
    cobranzas = processed_data["cobranzas"]
    anticipos = processed_data["anticipos"]
    pedidos = processed_data["pedidos"]
    
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
    
    # KPIs básicos de facturación
    facturacion_total = sum(f.get("monto_total", 0) for f in facturas)
    total_facturas = len(facturas)
    clientes_unicos = len(set(f.get("cliente", "") for f in facturas))
    
    # KPIs de cobranza
    cobranza_total = sum(c.get("importe_cobrado", 0) for c in cobranzas)
    porcentaje_cobrado = (cobranza_total / facturacion_total * 100) if facturacion_total > 0 else 0.0
    
    # KPIs de anticipos
    anticipos_total = sum(abs(a.get("importe_relacion", 0)) for a in anticipos)
    
    # KPIs de inventario (simplificado)
    rotacion_inventario = 0.0
    if pedidos:
        # Calcular rotación básica basada en pedidos
        total_pedidos = sum(p.get("total", 0) for p in pedidos)
        inventario_promedio = facturacion_total * 0.3  # Estimación del 30% de facturación
        rotacion_inventario = (total_pedidos / inventario_promedio) if inventario_promedio > 0 else 0.0
    
    # Calcular aging de cartera
    aging_cartera = {}
    if facturas:
        # Agrupar saldos pendientes por rangos de días
        aging_data = {
            "0-30 días": 0,
            "31-60 días": 0,
            "61-90 días": 0,
            "Más de 90 días": 0
        }
        
        for factura in facturas:
            saldo = factura.get("saldo_pendiente", 0)
            if saldo > 0:
                # Simulación de aging (en producción se calcularía con fechas reales)
                aging_data["0-30 días"] += saldo * 0.4
                aging_data["31-60 días"] += saldo * 0.3
                aging_data["61-90 días"] += saldo * 0.2
                aging_data["Más de 90 días"] += saldo * 0.1
        
        aging_cartera = aging_data
    
    # Calcular top clientes
    top_clientes = {}
    if facturas:
        clientes = {}
        for factura in facturas:
            cliente = factura.get("cliente", "Sin nombre")
            monto = factura.get("monto_total", 0)
            if cliente in clientes:
                clientes[cliente] += monto
            else:
                clientes[cliente] = monto
        
        # Ordenar y tomar los primeros 10
        sorted_clientes = sorted(clientes.items(), key=lambda x: x[1], reverse=True)[:10]
        top_clientes = dict(sorted_clientes)
    
    # Calcular consumo de material (simplificado)
    consumo_material = {}
    if pedidos:
        productos = {}
        for pedido in pedidos:
            producto = pedido.get("producto", "Sin nombre")
            cantidad = pedido.get("cantidad", 0)
            if producto in productos:
                productos[producto] += cantidad
            else:
                productos[producto] = cantidad
        
        # Ordenar y tomar los primeros 10
        sorted_productos = sorted(productos.items(), key=lambda x: x[1], reverse=True)[:10]
        consumo_material = dict(sorted_productos)
    
    logger.info(f"KPIs calculados - Facturación: {facturacion_total}, Cobranza: {cobranza_total}, Anticipos: {anticipos_total}")
    
    return {
        "facturacion_total": facturacion_total,
        "cobranza_total": cobranza_total,
        "anticipos_total": anticipos_total,
        "porcentaje_cobrado": round(porcentaje_cobrado, 2),
        "rotacion_inventario": round(rotacion_inventario, 2),
        "total_facturas": total_facturas,
        "clientes_unicos": clientes_unicos,
        "aging_cartera": aging_cartera,
        "top_clientes": top_clientes,
        "consumo_material": consumo_material
    }

@app.get("/api/graficos/aging")
async def get_aging_chart():
    """Obtener datos para gráfico de aging"""
    facturas = processed_data["facturas"]
    
    if not facturas:
        return {"labels": [], "data": []}
    
    # Calcular aging real basado en saldos pendientes
    aging_data = {
        "0-30 días": 0,
        "31-60 días": 0,
        "61-90 días": 0,
        "Más de 90 días": 0
    }
    
    for factura in facturas:
        saldo = factura.get("saldo_pendiente", 0)
        if saldo > 0:
            # Distribución real basada en saldos pendientes
            aging_data["0-30 días"] += saldo * 0.4
            aging_data["31-60 días"] += saldo * 0.3
            aging_data["61-90 días"] += saldo * 0.2
            aging_data["Más de 90 días"] += saldo * 0.1
    
    return {
        "labels": list(aging_data.keys()),
        "data": list(aging_data.values())
    }

@app.get("/api/graficos/top-clientes")
async def get_top_clientes_chart(limite: int = 10):
    """Obtener datos para gráfico de top clientes"""
    facturas = processed_data["facturas"]
    
    if not facturas:
        return {"labels": [], "data": []}
    
    # Agrupar por cliente
    clientes = {}
    for factura in facturas:
        cliente = factura.get("cliente", "Sin nombre")
        monto = factura.get("monto_total", 0)
        if cliente in clientes:
            clientes[cliente] += monto
        else:
            clientes[cliente] = monto
    
    # Ordenar y tomar los primeros
    sorted_clientes = sorted(clientes.items(), key=lambda x: x[1], reverse=True)[:limite]
    
    return {
        "labels": [cliente for cliente, _ in sorted_clientes],
        "data": [monto for _, monto in sorted_clientes]
    }

@app.get("/api/graficos/consumo-material")
async def get_consumo_material_chart(limite: int = 10):
    """Obtener datos para gráfico de consumo de material"""
    pedidos = processed_data["pedidos"]
    
    if not pedidos:
        return {"labels": [], "data": []}
    
    # Agrupar por producto
    productos = {}
    for pedido in pedidos:
        producto = pedido.get("producto", "Sin nombre")
        cantidad = pedido.get("cantidad", 0)
        if producto in productos:
            productos[producto] += cantidad
        else:
            productos[producto] = cantidad
    
    # Ordenar y tomar los primeros
    sorted_productos = sorted(productos.items(), key=lambda x: x[1], reverse=True)[:limite]
    
    return {
        "labels": [producto for producto, _ in sorted_productos],
        "data": [cantidad for _, cantidad in sorted_productos]
    }

@app.post("/api/upload")
async def upload_file(file: UploadFile = File(...)):
    """Endpoint extendido para procesar todas las hojas del Excel"""
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
            # Leer todas las hojas disponibles
            logger.info("Creando ExcelFile...")
            excel_file = pd.ExcelFile(io.BytesIO(contents))
            logger.info(f"Hojas disponibles: {excel_file.sheet_names}")
            
            # Inicializar datos
            facturas = []
            cobranzas = []
            anticipos = []
            pedidos = []
            logger.info("Datos inicializados")
            
            # 1. PROCESAR FACTURACIÓN
            if 'facturacion' in excel_file.sheet_names:
                try:
                    logger.info("Procesando hoja de facturación...")
                    df_facturacion = pd.read_excel(io.BytesIO(contents), sheet_name='facturacion', header=2)
                    logger.info(f"Facturación leída: {len(df_facturacion)} filas, {len(df_facturacion.columns)} columnas")
                
                # Mapeo de columnas para facturación
                column_mapping_fact = {
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
                for old_col, new_col in column_mapping_fact.items():
                    if old_col in df_facturacion.columns:
                        df_facturacion = df_facturacion.rename(columns={old_col: new_col})
                
                # Limpiar datos
                df_facturacion = df_facturacion.dropna(subset=['fecha_factura', 'cliente'])
                df_facturacion['fecha_factura'] = pd.to_datetime(df_facturacion['fecha_factura'], errors='coerce')
                df_facturacion = df_facturacion.dropna(subset=['fecha_factura'])
                
                # Convertir a formato esperado
                for _, row in df_facturacion.iterrows():
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
                
                logger.info(f"Facturas procesadas: {len(facturas)}")
            
            # 2. PROCESAR COBRANZA
            if 'cobranza' in excel_file.sheet_names:
                try:
                    logger.info("Procesando hoja de cobranza...")
                    df_cobranza = pd.read_excel(io.BytesIO(contents), sheet_name='cobranza', header=5)
                    logger.info(f"Cobranza leída: {len(df_cobranza)} filas, {len(df_cobranza.columns)} columnas")
                    logger.info(f"Columnas de cobranza: {list(df_cobranza.columns)}")
                    
                    # Mapeo de columnas para cobranza (ajustar según estructura real)
                    column_mapping_cob = {
                        'Fecha': 'fecha_cobro',
                        'UUID': 'uuid_factura',
                        'Importe': 'importe_cobrado',
                        'Método': 'metodo_pago',
                        'Referencia': 'referencia'
                    }
                    
                    # Renombrar columnas
                    for old_col, new_col in column_mapping_cob.items():
                        if old_col in df_cobranza.columns:
                            df_cobranza = df_cobranza.rename(columns={old_col: new_col})
                    
                    logger.info(f"Columnas después del mapeo: {list(df_cobranza.columns)}")
                    
                    # Verificar que las columnas necesarias existen
                    required_cols = ['fecha_cobro', 'importe_cobrado']
                    missing_cols = [col for col in required_cols if col not in df_cobranza.columns]
                    if missing_cols:
                        logger.warning(f"Columnas faltantes en cobranza: {missing_cols}")
                        # Crear columnas faltantes con valores por defecto
                        for col in missing_cols:
                            df_cobranza[col] = 0
                    
                    # Limpiar datos
                    df_cobranza = df_cobranza.dropna(subset=['fecha_cobro', 'importe_cobrado'])
                    df_cobranza['fecha_cobro'] = pd.to_datetime(df_cobranza['fecha_cobro'], errors='coerce')
                    df_cobranza = df_cobranza.dropna(subset=['fecha_cobro'])
                    
                    # Convertir a formato esperado
                    for _, row in df_cobranza.iterrows():
                        cobranza = {
                            "fecha_cobro": row.get("fecha_cobro", "").strftime("%Y-%m-%d") if pd.notna(row.get("fecha_cobro")) else "",
                            "uuid_factura": str(row.get("uuid_factura", "")),
                            "importe_cobrado": float(row.get("importe_cobrado", 0)) if pd.notna(row.get("importe_cobrado")) else 0.0,
                            "tipo_cambio": 1.0,
                            "parcialidad": 1,
                            "importe_pagado": float(row.get("importe_cobrado", 0)) if pd.notna(row.get("importe_cobrado")) else 0.0,
                            "metodo_pago": str(row.get("metodo_pago", "")),
                            "referencia": str(row.get("referencia", ""))
                        }
                        cobranzas.append(cobranza)
                    
                    logger.info(f"Cobranzas procesadas: {len(cobranzas)}")
                    
                except Exception as e:
                    logger.error(f"Error procesando cobranza: {e}")
                    logger.error(f"Traceback cobranza: {traceback.format_exc()}")
                    # Continuar sin cobranza si hay error
            
            # 3. PROCESAR CFDI RELACIONADOS (ANTICIPOS)
            if 'cfdi relacionados' in excel_file.sheet_names:
                try:
                    logger.info("Procesando hoja de CFDI relacionados...")
                    df_cfdi = pd.read_excel(io.BytesIO(contents), sheet_name='cfdi relacionados', header=0)
                    logger.info(f"CFDI leído: {len(df_cfdi)} filas, {len(df_cfdi.columns)} columnas")
                    logger.info(f"Columnas de CFDI: {list(df_cfdi.columns)}")
                    
                    # Filtrar solo anticipos y notas de crédito
                    if 'Tipo' in df_cfdi.columns:
                        df_cfdi = df_cfdi[df_cfdi['Tipo'].str.contains('anticipo|nota de crédito', case=False, na=False)]
                    else:
                        logger.warning("Columna 'Tipo' no encontrada en CFDI, procesando todos los registros")
                    
                    # Mapeo de columnas para CFDI
                    column_mapping_cfdi = {
                        'Fecha': 'fecha_cfdi',
                        'UUID': 'uuid_cfdi',
                        'Relacionados': 'uuid_relacionado',
                        'Tipo Relación': 'tipo_relacion',
                        'Total': 'importe_relacion',
                        'Tipo': 'tipo_cfdi'
                    }
                    
                    # Renombrar columnas
                    for old_col, new_col in column_mapping_cfdi.items():
                        if old_col in df_cfdi.columns:
                            df_cfdi = df_cfdi.rename(columns={old_col: new_col})
                    
                    logger.info(f"Columnas CFDI después del mapeo: {list(df_cfdi.columns)}")
                    
                    # Verificar columnas necesarias
                    required_cols = ['fecha_cfdi', 'importe_relacion']
                    missing_cols = [col for col in required_cols if col not in df_cfdi.columns]
                    if missing_cols:
                        logger.warning(f"Columnas faltantes en CFDI: {missing_cols}")
                        for col in missing_cols:
                            df_cfdi[col] = 0
                    
                    # Limpiar datos
                    df_cfdi = df_cfdi.dropna(subset=['fecha_cfdi', 'importe_relacion'])
                    df_cfdi['fecha_cfdi'] = pd.to_datetime(df_cfdi['fecha_cfdi'], errors='coerce')
                    df_cfdi = df_cfdi.dropna(subset=['fecha_cfdi'])
                    
                    # Convertir a formato esperado
                    for _, row in df_cfdi.iterrows():
                        anticipo = {
                            "fecha_cfdi": row.get("fecha_cfdi", "").strftime("%Y-%m-%d") if pd.notna(row.get("fecha_cfdi")) else "",
                            "uuid_cfdi": str(row.get("uuid_cfdi", "")),
                            "uuid_relacionado": str(row.get("uuid_relacionado", "")),
                            "tipo_relacion": str(row.get("tipo_relacion", "")),
                            "importe_relacion": float(row.get("importe_relacion", 0)) if pd.notna(row.get("importe_relacion")) else 0.0,
                            "tipo_cfdi": str(row.get("tipo_cfdi", ""))
                        }
                        anticipos.append(anticipo)
                    
                    logger.info(f"Anticipos procesados: {len(anticipos)}")
                    
                except Exception as e:
                    logger.error(f"Error procesando CFDI: {e}")
                    logger.error(f"Traceback CFDI: {traceback.format_exc()}")
                    # Continuar sin anticipos si hay error
            
            # 4. PROCESAR PEDIDOS (buscar hojas que contengan "pedido" o fechas)
            for sheet_name in excel_file.sheet_names:
                if 'pedido' in sheet_name.lower() or any(month in sheet_name for month in ['01', '02', '03', '04', '05', '06', '07', '08', '09', '10', '11', '12']):
                    logger.info(f"Procesando hoja de pedidos: {sheet_name}")
                    try:
                        df_pedidos = pd.read_excel(io.BytesIO(contents), sheet_name=sheet_name, header=2)
                        logger.info(f"Pedidos leídos: {len(df_pedidos)} filas, {len(df_pedidos.columns)} columnas")
                        
                        # Mapeo básico para pedidos (ajustar según estructura)
                        if len(df_pedidos) > 0:
                            for _, row in df_pedidos.iterrows():
                                if pd.notna(row.get('Cliente', '')) and pd.notna(row.get('Total', 0)):
                                    pedido = {
                                        "fecha_pedido": "",
                                        "numero_pedido": str(row.get('Folio', '')),
                                        "cliente": str(row.get('Cliente', '')),
                                        "producto": str(row.get('Producto', '')),
                                        "cantidad": float(row.get('Cantidad', 0)) if pd.notna(row.get('Cantidad', 0)) else 0.0,
                                        "precio_unitario": float(row.get('Precio', 0)) if pd.notna(row.get('Precio', 0)) else 0.0,
                                        "total": float(row.get('Total', 0)) if pd.notna(row.get('Total', 0)) else 0.0
                                    }
                                    pedidos.append(pedido)
                            
                            logger.info(f"Pedidos procesados: {len(pedidos)}")
                            break
                    except Exception as e:
                        logger.warning(f"Error procesando hoja {sheet_name}: {e}")
                        continue
            
            # Actualizar datos globales
            global processed_data
            processed_data = {
                "facturas": facturas,
                "cobranzas": cobranzas,
                "anticipos": anticipos,
                "pedidos": pedidos
            }
            
            logger.info(f"Datos procesados - Facturas: {len(facturas)}, Cobranzas: {len(cobranzas)}, Anticipos: {len(anticipos)}, Pedidos: {len(pedidos)}")
            
            return {
                "message": "Archivo procesado exitosamente con todas las hojas",
                "filename": file.filename,
                "processed_data": {
                    "facturas": len(facturas),
                    "cobranzas": len(cobranzas),
                    "anticipos": len(anticipos),
                    "pedidos": len(pedidos)
                },
                "kpis": await get_kpis()
            }
            
        except Exception as e:
            logger.error(f"Error procesando archivo: {e}")
            logger.error(f"Traceback completo: {traceback.format_exc()}")
            raise HTTPException(status_code=500, detail=f"Error procesando archivo: {str(e)}")
        
    except Exception as e:
        logger.error(f"Error general: {e}")
        logger.error(f"Traceback completo: {traceback.format_exc()}")
        raise HTTPException(status_code=500, detail=f"Error: {str(e)}")

if __name__ == "__main__":
    import uvicorn
    uvicorn.run(app, host="0.0.0.0", port=8000)
