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
    
    if not facturas:
        return default_kpis
    
    # 1. FACTURACIÓN TOTAL (periodo)
    facturacion_total = sum(f.get("monto_total", 0) for f in facturas)
    
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
    
    # 3. % COBRANZA SOBRE FACTURACIÓN
    porcentaje_cobrado = (cobranza_total / facturacion_total * 100) if facturacion_total > 0 else 0
    
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
    """Endpoint para subir archivos Excel según especificaciones Immermex"""
    try:
        # Validar tipo de archivo
        if not file.filename or not file.filename.endswith(('.xlsx', '.xls')):
            raise HTTPException(status_code=400, detail="Solo se permiten archivos Excel (.xlsx, .xls)")
        
        logger.info(f"Procesando archivo Immermex: {file.filename}")
        
        # Leer contenido del archivo
        contents = await file.read()
        
        # Validar tamaño del archivo (máximo 10MB)
        if len(contents) > 10 * 1024 * 1024:
            raise HTTPException(status_code=400, detail="El archivo es demasiado grande. Máximo 10MB permitido.")
        
        # Leer todas las hojas del Excel
        excel_file = pd.ExcelFile(io.BytesIO(contents))
        logger.info(f"Hojas disponibles: {excel_file.sheet_names}")
        
        # Limpiar datos procesados anteriores
        for key in processed_data:
            processed_data[key] = []
        
        registros_procesados = 0
        
        # 1. PROCESAR HOJA 'facturacion'
        if 'facturacion' in excel_file.sheet_names:
            df_facturacion = pd.read_excel(io.BytesIO(contents), sheet_name='facturacion')
            logger.info(f"Procesando hoja facturacion: {len(df_facturacion)} filas")
            
            for index, row in df_facturacion.iterrows():
                try:
                    factura = {
                        "fecha_factura": str(row.get("Fecha de factura", "")),
                        "serie": str(row.get("Serie factura", "")),
                        "folio": str(row.get("Folio factura", "")),
                        "cliente": str(row.get("Cliente", "")),
                        "monto_neto": float(row.get("Monto neto", 0)),
                        "monto_total": float(row.get("Monto total", 0)),
                        "saldo_pendiente": float(row.get("Saldo pendiente", 0)),
                        "dias_credito": int(row.get("Referencia / días crédito", 30)),
                        "agente": str(row.get("Agente", "")),
                        "uuid": str(row.get("UUID factura", ""))
                    }
                    processed_data["facturas"].append(factura)
                    registros_procesados += 1
                except Exception as e:
                    logger.warning(f"Error procesando factura {index}: {str(e)}")
                    # Agregar factura con datos por defecto para evitar pérdida de datos
                    factura = {
                        "fecha_factura": "",
                        "serie": "",
                        "folio": "",
                        "cliente": "",
                        "monto_neto": 0.0,
                        "monto_total": 0.0,
                        "saldo_pendiente": 0.0,
                        "dias_credito": 30,
                        "agente": "",
                        "uuid": ""
                    }
                    processed_data["facturas"].append(factura)
                    continue
        
        # 2. PROCESAR HOJA 'cobranza'
        if 'cobranza' in excel_file.sheet_names:
            df_cobranza = pd.read_excel(io.BytesIO(contents), sheet_name='cobranza')
            logger.info(f"Procesando hoja cobranza: {len(df_cobranza)} filas")
            
            for index, row in df_cobranza.iterrows():
                try:
                    cobranza = {
                        "fecha_pago": str(row.get("Fecha de pago", "")),
                        "serie_pago": str(row.get("Serie pago", "")),
                        "folio_pago": str(row.get("Folio pago", "")),
                        "concepto_pago": str(row.get("Concepto pago", "")),
                        "uuid_pago": str(row.get("UUID pago", "")),
                        "cliente": str(row.get("Cliente", "")),
                        "moneda": str(row.get("Moneda", "")),
                        "tipo_cambio": float(row.get("Tipo de cambio", 1)),
                        "forma_pago": str(row.get("Forma pago", "")),
                        "no_parcialidad": int(row.get("No. parcialidad", 1)),
                        "importe_pagado": float(row.get("Importe pagado", 0)),
                        "numero_operacion": str(row.get("Número operación", "")),
                        "fecha_emision_pago": str(row.get("Fecha emisión pago", "")),
                        "fecha_factura_relacionada": str(row.get("Fecha factura relacionada", "")),
                        "serie_factura_relacionada": str(row.get("Serie factura relacionada", "")),
                        "folio_factura_relacionada": str(row.get("Folio factura relacionada", "")),
                        "uuid_factura_relacionada": str(row.get("UUID factura relacionada", ""))
                    }
                    processed_data["cobranzas"].append(cobranza)
                    registros_procesados += 1
                except Exception as e:
                    logger.warning(f"Error procesando cobranza {index}: {str(e)}")
                    continue
        
        # 3. PROCESAR HOJA 'cfdi relacionados' (anticipos)
        if 'cfdi relacionados' in excel_file.sheet_names:
            df_cfdi = pd.read_excel(io.BytesIO(contents), sheet_name='cfdi relacionados')
            logger.info(f"Procesando hoja cfdi relacionados: {len(df_cfdi)} filas")
            
            for index, row in df_cfdi.iterrows():
                try:
                    tipo_relacion = str(row.get("Tipo relación", ""))
                    if "anticipo" in tipo_relacion.lower() or "anticipo" in str(row.get("Cliente receptor", "")).lower():
                        anticipo = {
                            "uuid_cfdi": str(row.get("UUID CFDI", "")),
                            "cliente_receptor": str(row.get("Cliente receptor", "")),
                            "fecha_emision": str(row.get("Fecha emisión CFDI", "")),
                            "tipo_relacion": tipo_relacion,
                            "importe_relacion": float(row.get("Importe relación", 0)),
                            "uuid_factura_relacionada": str(row.get("UUID factura relacionada", ""))
                        }
                        processed_data["anticipos"].append(anticipo)
                        registros_procesados += 1
                except Exception as e:
                    logger.warning(f"Error procesando CFDI {index}: {str(e)}")
                    continue
        
        # 4. PROCESAR HOJA '1-14 sep' (pedidos)
        for sheet_name in excel_file.sheet_names:
            if 'sep' in sheet_name.lower() or 'pedido' in sheet_name.lower():
                df_pedidos = pd.read_excel(io.BytesIO(contents), sheet_name=sheet_name)
                logger.info(f"Procesando hoja {sheet_name}: {len(df_pedidos)} filas")
                
                for index, row in df_pedidos.iterrows():
                    try:
                        pedido = {
                            "factura_asociada": str(row.get("Factura asociada", "")),
                            "numero_pedido": str(row.get("Número de pedido", "")),
                            "kg": float(row.get("Kg", 0)),
                            "precio_unitario": float(row.get("Precio unitario", 0)),
                            "importe_sin_iva": float(row.get("Importe sin IVA", 0)),
                            "material": str(row.get("Material", "")),
                            "cliente": str(row.get("Cliente", "")),
                            "dias_credito": int(row.get("Días crédito", 30)),
                            "fecha_factura": str(row.get("Fecha factura", "")),
                            "fecha_pago": str(row.get("Fecha pago", ""))
                        }
                        processed_data["pedidos"].append(pedido)
                        registros_procesados += 1
                    except Exception as e:
                        logger.warning(f"Error procesando pedido {index}: {str(e)}")
                        continue
                break  # Solo procesar la primera hoja que contenga 'sep' o 'pedido'
        
        logger.info(f"Procesados {registros_procesados} registros de {file.filename}")
        logger.info(f"Resumen: {len(processed_data['facturas'])} facturas, {len(processed_data['cobranzas'])} cobranzas, {len(processed_data['anticipos'])} anticipos, {len(processed_data['pedidos'])} pedidos")
        
        return {
            "mensaje": "Archivo procesado exitosamente según especificaciones Immermex",
            "nombre_archivo": file.filename,
            "registros_procesados": registros_procesados,
            "fecha_procesamiento": datetime.now().isoformat(),
            "estado": "procesado",
            "resumen": {
                "facturas": len(processed_data["facturas"]),
                "cobranzas": len(processed_data["cobranzas"]),
                "anticipos": len(processed_data["anticipos"]),
                "pedidos": len(processed_data["pedidos"])
            }
        }
    except Exception as e:
        logger.error(f"Error procesando archivo: {str(e)}")
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
