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
from logging_config import setup_logging, log_api_request, log_file_processing, log_error
from data_processor import load_and_clean_excel, process_immermex_file_advanced

# Configurar logging
logger = setup_logging()

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

# Almacenamiento en memoria de datos procesados según especificaciones Immermex
processed_data = {
    "facturas": [],      # Hoja 'facturacion'
    "cobranzas": [],     # Hoja 'cobranza' 
    "anticipos": [],     # Hoja 'cfdi relacionados' (tipo relación = anticipo)
    "inventario": [],    # Datos de inventario
    "pedidos": []        # Hoja '1-14 sep' (datos de pedidos)
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
    """Calcula KPIs basados en los datos procesados según especificaciones Immermex"""
    facturas = processed_data["facturas"]
    cobranzas = processed_data["cobranzas"]
    anticipos = processed_data["anticipos"]
    inventario = processed_data["inventario"]
    pedidos = processed_data["pedidos"]
    
    logger.info(f"Calculando KPIs - Facturas: {len(facturas)}, Cobranzas: {len(cobranzas)}, Anticipos: {len(anticipos)}")
    
    if not facturas:
        logger.warning("No hay facturas para calcular KPIs")
        return default_kpis
    
    # 1. FACTURACIÓN TOTAL (periodo)
    facturacion_total = sum(f.get("monto_total", 0) for f in facturas)
    logger.info(f"Facturación total calculada: {facturacion_total}")
    
    # Debug: verificar valores de monto_total
    montos = [f.get("monto_total", 0) for f in facturas[:5]]  # Primeros 5
    logger.info(f"Primeros 5 montos_total: {montos}")
    
    # Debug: verificar estructura de facturas
    if facturas:
        logger.info(f"Estructura de primera factura: {list(facturas[0].keys())}")
        logger.info(f"Valores de primera factura: {facturas[0]}")
    
    # 2. COBRANZA TOTAL (periodo) - cruce con facturación usando folio/UUID
    cobranza_total = 0
    for cobranza in cobranzas:
        # Buscar factura relacionada por UUID o folio
        uuid_relacionada = cobranza.get("uuid_factura_relacionada", "")
        serie_relacionada = cobranza.get("serie_factura_relacionada", "")
        folio_relacionada = cobranza.get("folio_factura_relacionada", "")
        
        for factura in facturas:
            if (factura.get("uuid", "") == uuid_relacionada or 
                (factura.get("serie", "") == serie_relacionada and 
                 factura.get("folio", "") == folio_relacionada)):
                cobranza_total += cobranza.get("importe_pagado", 0)
                break
    
    logger.info(f"Cobranza total calculada: {cobranza_total}")
    
    # 3. % COBRANZA SOBRE FACTURACIÓN
    porcentaje_cobrado = (cobranza_total / facturacion_total * 100) if facturacion_total > 0 else 0
    logger.info(f"Porcentaje cobrado: {porcentaje_cobrado}%")
    
    # 4. ANTICIPOS RECIBIDOS
    anticipos_total = sum(a.get("importe_relacion", 0) for a in anticipos)
    
    # 5. CARTERA VENCIDA (aging: 0-30, 31-60, 61-90, 90+)
    aging_cartera = {"0-30 días": 0, "31-60 días": 0, "61-90 días": 0, "90+ días": 0}
    
    for factura in facturas:
        dias_credito = factura.get("dias_credito", 0)
        fecha_factura = factura.get("fecha_factura", "")
        
        if fecha_factura:
            try:
                from datetime import datetime, timedelta
                fecha_fact = datetime.strptime(fecha_factura, "%Y-%m-%d")
                fecha_vencimiento = fecha_fact + timedelta(days=dias_credito)
                dias_vencidos = (datetime.now() - fecha_vencimiento).days
                
                if dias_vencidos <= 30:
                    aging_cartera["0-30 días"] += 1
                elif dias_vencidos <= 60:
                    aging_cartera["31-60 días"] += 1
                elif dias_vencidos <= 90:
                    aging_cartera["61-90 días"] += 1
                else:
                    aging_cartera["90+ días"] += 1
            except Exception as e:
                logger.warning(f"Error procesando fecha de factura: {str(e)}")
                pass
    
    # 6. DÍAS DE CUENTAS POR COBRAR (ajustado por anticipos)
    saldo_pendiente = sum(f.get("saldo_pendiente", 0) for f in facturas)
    dias_cxc_ajustado = (saldo_pendiente / facturacion_total * 30) if facturacion_total > 0 else 0
    
    # 7. ROTACIÓN DE INVENTARIOS (días corte/factura)
    rotacion_inventario = 0
    if inventario:
        # Calcular tiempo promedio entre fecha de corte y fecha de factura
        total_dias = 0
        count = 0
        for item in inventario:
            fecha_corte = item.get("fecha_corte", "")
            fecha_factura = item.get("fecha_factura", "")
            if fecha_corte and fecha_factura:
                try:
                    from datetime import datetime
                    corte = datetime.strptime(fecha_corte, "%Y-%m-%d")
                    factura = datetime.strptime(fecha_factura, "%Y-%m-%d")
                    dias = (factura - corte).days
                    total_dias += dias
                    count += 1
                except Exception as e:
                    logger.warning(f"Error calculando rotación de inventario: {str(e)}")
                    pass
        rotacion_inventario = total_dias / count if count > 0 else 0
    
    # 8. CONSUMO POR MATERIAL (kg, importe, margen)
    consumo_material = {}
    for pedido in pedidos:
        material = pedido.get("material", "")
        kg = pedido.get("kg", 0)
        importe = pedido.get("importe_sin_iva", 0)
        
        if material not in consumo_material:
            consumo_material[material] = {"kg": 0, "importe": 0, "margen": 0}
        
        consumo_material[material]["kg"] += kg
        consumo_material[material]["importe"] += importe
        # Margen se calcularía con catálogo de costos (simulado)
        consumo_material[material]["margen"] += importe * 0.3  # 30% margen simulado
    
    # 9. TOP CLIENTES (ranking por facturación, puntualidad y rentabilidad)
    clientes_analisis = {}
    for factura in facturas:
        cliente = factura.get("cliente", "")
        if cliente not in clientes_analisis:
            clientes_analisis[cliente] = {
                "facturacion": 0,
                "cobranza": 0,
                "puntualidad": 0,
                "ticket_promedio": 0,
                "facturas_count": 0
            }
        
        clientes_analisis[cliente]["facturacion"] += factura.get("monto_total", 0)
        clientes_analisis[cliente]["facturas_count"] += 1
    
    # Calcular cobranza por cliente
    for cobranza in cobranzas:
        cliente = cobranza.get("cliente", "")
        if cliente in clientes_analisis:
            clientes_analisis[cliente]["cobranza"] += cobranza.get("importe_pagado", 0)
    
    # Calcular puntualidad y ticket promedio
    for cliente, datos in clientes_analisis.items():
        if datos["facturas_count"] > 0:
            datos["ticket_promedio"] = datos["facturacion"] / datos["facturas_count"]
            datos["puntualidad"] = (datos["cobranza"] / datos["facturacion"] * 100) if datos["facturacion"] > 0 else 0
    
    # Top 5 clientes por facturación
    top_clientes = dict(sorted(clientes_analisis.items(), 
                             key=lambda x: x[1]["facturacion"], reverse=True)[:5])
    
    # 10. CICLO DE CONVERSIÓN DE EFECTIVO (Inventario + CxC)
    ciclo_efectivo = rotacion_inventario + dias_cxc_ajustado
    
    # 11. ANÁLISIS POR PEDIDO
    analisis_pedidos = []
    for pedido in pedidos:
        numero_pedido = pedido.get("numero_pedido", "")
        cliente = pedido.get("cliente", "")
        kg = pedido.get("kg", 0)
        importe = pedido.get("importe_sin_iva", 0)
        fecha_factura = pedido.get("fecha_factura", "")
        fecha_pago = pedido.get("fecha_pago", "")
        
        # Estado de cobro
        estado_cobro = "Pendiente"
        if fecha_pago:
            estado_cobro = "Cobrado"
        elif fecha_factura:
            try:
                from datetime import datetime
                fecha_fact = datetime.strptime(fecha_factura, "%Y-%m-%d")
                dias_transcurridos = (datetime.now() - fecha_fact).days
                if dias_transcurridos > pedido.get("dias_credito", 30):
                    estado_cobro = "Vencido"
            except Exception as e:
                logger.warning(f"Error calculando estado de cobro: {str(e)}")
                pass
        
        analisis_pedidos.append({
            "numero_pedido": numero_pedido,
            "cliente": cliente,
            "kg": kg,
            "importe": importe,
            "ticket_promedio": importe / kg if kg > 0 else 0,
            "margen": importe * 0.3,  # 30% simulado
            "estado_cobro": estado_cobro,
            "dias_credito": pedido.get("dias_credito", 30)
        })
    
    return {
        "facturacion_total": round(facturacion_total, 2),
        "cobranza_total": round(cobranza_total, 2),
        "anticipos_total": round(anticipos_total, 2),
        "porcentaje_cobrado": round(porcentaje_cobrado, 2),
        "rotacion_inventario": round(rotacion_inventario, 2),
        "dias_cxc_ajustado": round(dias_cxc_ajustado, 2),
        "ciclo_efectivo": round(ciclo_efectivo, 2),
        "total_facturas": len(facturas),
        "clientes_unicos": len(set(f.get("cliente", "") for f in facturas)),
        "aging_cartera": aging_cartera,
        "top_clientes": {k: v["facturacion"] for k, v in top_clientes.items()},
        "consumo_material": {k: v["kg"] for k, v in consumo_material.items()},
        "analisis_pedidos": analisis_pedidos[:10],  # Top 10 pedidos
        "clientes_analisis": clientes_analisis
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
    """Endpoint para subir archivos Excel con procesamiento avanzado integrado"""
    try:
        # Validar tipo de archivo
        if not file.filename or not file.filename.endswith(('.xlsx', '.xls')):
            raise HTTPException(status_code=400, detail="Solo se permiten archivos Excel (.xlsx, .xls)")
        
        logger.info(f"Procesando archivo Immermex con algoritmo avanzado: {file.filename}")
        
        # Leer contenido del archivo
        contents = await file.read()
        
        # Validar tamaño del archivo (máximo 10MB)
        if len(contents) > 10 * 1024 * 1024:
            raise HTTPException(status_code=400, detail="El archivo es demasiado grande. Máximo 10MB permitido.")
        
        # Guardar archivo temporalmente para procesamiento
        temp_file_path = f"temp_{file.filename}"
        with open(temp_file_path, "wb") as temp_file:
            temp_file.write(contents)
        
        try:
            # Usar el procesador avanzado integrado
            logger.info(f"Iniciando procesamiento del archivo: {temp_file_path}")
            logger.info(f"Archivo existe: {os.path.exists(temp_file_path)}")
            logger.info(f"Tamaño del archivo: {os.path.getsize(temp_file_path)} bytes")
            
            # Importar el procesador
            try:
                from data_processor import process_immermex_file_advanced
                logger.info("✅ Módulo data_processor importado correctamente")
            except ImportError as e:
                logger.error(f"❌ Error importando data_processor: {e}")
                raise
            
            # Procesar archivo
            logger.info("🔄 Llamando a process_immermex_file_advanced...")
            processed_data_dict, kpis = process_immermex_file_advanced(temp_file_path)
            logger.info(f"✅ Procesamiento completado. KPIs: {kpis}")
            
            # Debug: verificar qué datos se obtuvieron
            logger.info("=== DEBUG: Datos procesados ===")
            for key, df in processed_data_dict.items():
                logger.info(f"{key}: {df.shape[0]} registros")
                if not df.empty:
                    logger.info(f"  Columnas: {list(df.columns)}")
                    logger.info(f"  Primeras 3 filas:")
                    for i in range(min(3, len(df))):
                        logger.info(f"    Fila {i}: {df.iloc[i].to_dict()}")
                else:
                    logger.info(f"  DataFrame vacío")
            logger.info("=== FIN DEBUG ===")
            
            # Convertir DataFrames a formato compatible con el backend existente
            global processed_data
            processed_data = {
                "facturas": [],
                "cobranzas": [],
                "anticipos": [],
                "inventario": [],
                "pedidos": []
            }
            
            # Convertir facturación
            if not processed_data_dict["facturacion_clean"].empty:
                logger.info(f"Convirtiendo {len(processed_data_dict['facturacion_clean'])} registros de facturación")
                for _, row in processed_data_dict["facturacion_clean"].iterrows():
                    # Convertir fecha a string si es datetime
                    fecha_factura = row.get("fecha_factura", "")
                    if hasattr(fecha_factura, 'strftime'):
                        fecha_factura = fecha_factura.strftime("%Y-%m-%d")
                    else:
                        fecha_factura = str(fecha_factura)
                    
                    # Convertir valores numéricos de forma segura
                    monto_neto = row.get("monto_neto", 0)
                    monto_total = row.get("monto_total", 0)
                    saldo_pendiente = row.get("saldo_pendiente", 0)
                    dias_credito = row.get("dias_credito", 30)
                    
                    # Convertir a float de forma segura
                    try:
                        monto_neto = float(monto_neto) if pd.notna(monto_neto) else 0.0
                    except (ValueError, TypeError):
                        monto_neto = 0.0
                        
                    try:
                        monto_total = float(monto_total) if pd.notna(monto_total) else 0.0
                    except (ValueError, TypeError):
                        monto_total = 0.0
                        
                    try:
                        saldo_pendiente = float(saldo_pendiente) if pd.notna(saldo_pendiente) else 0.0
                    except (ValueError, TypeError):
                        saldo_pendiente = 0.0
                        
                    try:
                        dias_credito = int(dias_credito) if pd.notna(dias_credito) else 30
                    except (ValueError, TypeError):
                        dias_credito = 30
                    
                    factura = {
                        "fecha_factura": fecha_factura,
                        "serie": str(row.get("serie_factura", "")),
                        "folio": str(row.get("folio_factura", "")),
                        "cliente": str(row.get("cliente", "")),
                        "monto_neto": monto_neto,
                        "monto_total": monto_total,
                        "saldo_pendiente": saldo_pendiente,
                        "dias_credito": dias_credito,
                        "agente": str(row.get("agente", "")),
                        "uuid": str(row.get("uuid_factura", ""))
                    }
                    processed_data["facturas"].append(factura)
                
                logger.info(f"Facturación convertida: {len(processed_data['facturas'])} registros")
                if processed_data["facturas"]:
                    logger.info(f"Primera factura: {processed_data['facturas'][0]}")
                    # Verificar que los montos no sean cero
                    total_montos = sum(f.get("monto_total", 0) for f in processed_data["facturas"][:10])
                    logger.info(f"Suma de primeros 10 montos_total: {total_montos}")
            
            # Convertir cobranza
            if not processed_data_dict["cobranza_clean"].empty:
                logger.info(f"Convirtiendo {len(processed_data_dict['cobranza_clean'])} registros de cobranza")
                for _, row in processed_data_dict["cobranza_clean"].iterrows():
                    # Convertir fecha a string si es datetime
                    fecha_pago = row.get("fecha_pago", "")
                    if hasattr(fecha_pago, 'strftime'):
                        fecha_pago = fecha_pago.strftime("%Y-%m-%d")
                    else:
                        fecha_pago = str(fecha_pago)
                    
                    # Convertir valores numéricos de forma segura
                    tipo_cambio = row.get("tipo_cambio", 1)
                    parcialidad = row.get("parcialidad", 1)
                    importe_pagado = row.get("importe_pagado", 0)
                    
                    try:
                        tipo_cambio = float(tipo_cambio) if pd.notna(tipo_cambio) else 1.0
                    except (ValueError, TypeError):
                        tipo_cambio = 1.0
                        
                    try:
                        parcialidad = int(parcialidad) if pd.notna(parcialidad) else 1
                    except (ValueError, TypeError):
                        parcialidad = 1
                        
                    try:
                        importe_pagado = float(importe_pagado) if pd.notna(importe_pagado) else 0.0
                    except (ValueError, TypeError):
                        importe_pagado = 0.0
                    
                    cobranza = {
                        "fecha_pago": fecha_pago,
                        "serie_pago": str(row.get("serie_pago", "")),
                        "folio_pago": str(row.get("folio_pago", "")),
                        "concepto_pago": str(row.get("forma_pago", "")),
                        "uuid_pago": str(row.get("uuid_factura_relacionada", "")),
                        "cliente": str(row.get("cliente", "")),
                        "moneda": str(row.get("moneda", "MXN")),
                        "tipo_cambio": tipo_cambio,
                        "forma_pago": str(row.get("forma_pago", "")),
                        "no_parcialidad": parcialidad,
                        "importe_pagado": importe_pagado,
                        "numero_operacion": "",
                        "fecha_emision_pago": fecha_pago,
                        "fecha_factura_relacionada": "",
                        "serie_factura_relacionada": "",
                        "folio_factura_relacionada": "",
                        "uuid_factura_relacionada": str(row.get("uuid_factura_relacionada", ""))
                    }
                    processed_data["cobranzas"].append(cobranza)
                
                logger.info(f"Cobranza convertida: {len(processed_data['cobranzas'])} registros")
            
            # Convertir CFDI (anticipos)
            if not processed_data_dict["cfdi_clean"].empty:
                logger.info(f"Convirtiendo {len(processed_data_dict['cfdi_clean'])} registros de CFDI")
                for _, row in processed_data_dict["cfdi_clean"].iterrows():
                    # Convertir importe de forma segura
                    importe_relacion = row.get("importe_relacion", 0)
                    try:
                        importe_relacion = float(importe_relacion) if pd.notna(importe_relacion) else 0.0
                    except (ValueError, TypeError):
                        importe_relacion = 0.0
                    
                    anticipo = {
                        "uuid_cfdi": str(row.get("xml", "")),
                        "cliente_receptor": str(row.get("cliente_receptor", "")),
                        "fecha_emision": "",
                        "tipo_relacion": str(row.get("tipo_relacion", "")),
                        "importe_relacion": importe_relacion,
                        "uuid_factura_relacionada": str(row.get("uuid_factura_relacionada", ""))
                    }
                    processed_data["anticipos"].append(anticipo)
                
                logger.info(f"CFDI convertido: {len(processed_data['anticipos'])} registros")
            
            # Convertir pedidos
            if not processed_data_dict["pedidos_clean"].empty:
                for _, row in processed_data_dict["pedidos_clean"].iterrows():
                    pedido = {
                        "factura_asociada": str(row.get("folio_factura", "")),
                        "numero_pedido": str(row.get("pedido", "")),
                        "kg": float(row.get("kg", 0)),
                        "precio_unitario": float(row.get("precio_unitario", 0)),
                        "importe_sin_iva": float(row.get("importe_sin_iva", 0)),
                        "material": str(row.get("material", "")),
                        "cliente": "",
                        "dias_credito": int(row.get("dias_credito", 30)),
                        "fecha_factura": str(row.get("fecha_factura", "")),
                        "fecha_pago": str(row.get("fecha_pago", ""))
                    }
                    processed_data["pedidos"].append(pedido)
            
            # Calcular registros procesados
            registros_procesados = (
                len(processed_data["facturas"]) + 
                len(processed_data["cobranzas"]) + 
                len(processed_data["anticipos"]) + 
                len(processed_data["pedidos"])
            )
            
            logger.info(f"Procesados {registros_procesados} registros de {file.filename} con algoritmo avanzado")
            logger.info(f"Resumen: {len(processed_data['facturas'])} facturas, {len(processed_data['cobranzas'])} cobranzas, {len(processed_data['anticipos'])} anticipos, {len(processed_data['pedidos'])} pedidos")
            
            return {
                "mensaje": "Archivo procesado exitosamente con algoritmo avanzado de limpieza",
                "nombre_archivo": file.filename,
                "registros_procesados": registros_procesados,
                "fecha_procesamiento": datetime.now().isoformat(),
                "estado": "procesado",
                "algoritmo": "advanced_cleaning",
                "resumen": {
                    "facturas": len(processed_data["facturas"]),
                    "cobranzas": len(processed_data["cobranzas"]),
                    "anticipos": len(processed_data["anticipos"]),
                    "pedidos": len(processed_data["pedidos"])
                },
                "caracteristicas": {
                    "deteccion_automatica_encabezados": True,
                    "mapeo_flexible_columnas": True,
                    "validacion_datos": True,
                    "calculo_relaciones": True,
                    "limpieza_robusta": True
                }
            }
            
        finally:
            # Limpiar archivo temporal
            if os.path.exists(temp_file_path):
                os.remove(temp_file_path)
        
    except Exception as e:
        logger.error(f"Error procesando archivo con algoritmo avanzado: {str(e)}")
        import traceback
        logger.error(f"Traceback completo: {traceback.format_exc()}")
        raise HTTPException(status_code=500, detail=str(e))

@app.get("/api/debug/data")
async def get_debug_data():
    """Endpoint de debug para verificar datos procesados"""
    try:
        return {
            "processed_data_summary": {
                "facturas": len(processed_data["facturas"]),
                "cobranzas": len(processed_data["cobranzas"]),
                "anticipos": len(processed_data["anticipos"]),
                "pedidos": len(processed_data["pedidos"])
            },
            "sample_factura": processed_data["facturas"][0] if processed_data["facturas"] else None,
            "sample_cobranza": processed_data["cobranzas"][0] if processed_data["cobranzas"] else None,
            "kpis": calculate_kpis()
        }
    except Exception as e:
        logger.error(f"Error en debug data: {str(e)}")
        raise HTTPException(status_code=500, detail=str(e))

@app.get("/api/analisis/pedidos")
async def get_analisis_pedidos():
    """Obtiene análisis detallado de pedidos"""
    try:
        kpis = calculate_kpis()
        return {
            "pedidos": kpis.get("analisis_pedidos", []),
            "total_pedidos": len(processed_data["pedidos"]),
            "resumen": {
                "total_kg": sum(p.get("kg", 0) for p in processed_data["pedidos"]),
                "total_importe": sum(p.get("importe_sin_iva", 0) for p in processed_data["pedidos"]),
                "ticket_promedio": sum(p.get("importe_sin_iva", 0) for p in processed_data["pedidos"]) / len(processed_data["pedidos"]) if processed_data["pedidos"] else 0
            }
        }
    except Exception as e:
        logger.error(f"Error obteniendo análisis de pedidos: {str(e)}")
        raise HTTPException(status_code=500, detail=str(e))

@app.get("/api/analisis/clientes")
async def get_analisis_clientes():
    """Obtiene análisis detallado de clientes"""
    try:
        kpis = calculate_kpis()
        return {
            "clientes": kpis.get("clientes_analisis", {}),
            "total_clientes": len(kpis.get("clientes_analisis", {})),
            "resumen": {
                "facturacion_total": kpis.get("facturacion_total", 0),
                "cobranza_total": kpis.get("cobranza_total", 0),
                "porcentaje_cobrado": kpis.get("porcentaje_cobrado", 0)
            }
        }
    except Exception as e:
        logger.error(f"Error obteniendo análisis de clientes: {str(e)}")
        raise HTTPException(status_code=500, detail=str(e))

@app.get("/api/analisis/materiales")
async def get_analisis_materiales():
    """Obtiene análisis detallado de materiales"""
    try:
        kpis = calculate_kpis()
        materiales = kpis.get("consumo_material", {})
        
        # Convertir a formato para gráficos
        materiales_data = []
        for material, kg in materiales.items():
            materiales_data.append({
                "name": material,
                "value": kg,
                "importe": sum(p.get("importe_sin_iva", 0) for p in processed_data["pedidos"] if p.get("material", "") == material),
                "margen": sum(p.get("importe_sin_iva", 0) for p in processed_data["pedidos"] if p.get("material", "") == material) * 0.3
            })
        
        return {
            "materiales": materiales_data,
            "total_materiales": len(materiales_data),
            "resumen": {
                "total_kg": sum(m["value"] for m in materiales_data),
                "total_importe": sum(m["importe"] for m in materiales_data),
                "margen_total": sum(m["margen"] for m in materiales_data)
            }
        }
    except Exception as e:
        logger.error(f"Error obteniendo análisis de materiales: {str(e)}")
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
