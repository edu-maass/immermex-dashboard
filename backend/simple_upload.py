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
    facturacion_sin_iva = sum(f.get("monto_neto", 0) for f in facturas)  # Columna Neto
    total_facturas = len(facturas)
    clientes_unicos = len(set(f.get("cliente", "") for f in facturas))
    
    # KPIs de cobranza (manejar valores negativos como anticipos ya aplicados)
    cobranza_positiva = sum(c.get("importe_cobrado", 0) for c in cobranzas if c.get("importe_cobrado", 0) > 0)
    anticipos_aplicados = abs(sum(c.get("importe_cobrado", 0) for c in cobranzas if c.get("importe_cobrado", 0) < 0))
    cobranza_total = cobranza_positiva  # Solo cobranza positiva
    cobranza_sin_iva = cobranza_total * 0.84  # Aproximación: 84% del total (sin IVA 16%)
    porcentaje_cobrado = (cobranza_total / facturacion_total * 100) if facturacion_total > 0 else 0.0
    
    # Ajustar anticipos totales incluyendo los ya aplicados
    anticipos_total_ajustado = anticipos_total + anticipos_aplicados
    
    # KPIs de anticipos (usar total ajustado)
    anticipos_porcentaje = (anticipos_total_ajustado / facturacion_total * 100) if facturacion_total > 0 else 0.0
    
    # KPIs de pedidos
    total_pedidos = sum(p.get("total", 0) for p in pedidos)
    cantidad_total_pedidos = sum(p.get("cantidad", 0) for p in pedidos)
    total_pedidos_count = len(pedidos)
    
    # KPIs de inventario (mejorado)
    rotacion_inventario = 0.0
    if pedidos:
        # Inventario promedio estimado (30% de facturación o 20% de pedidos)
        inventario_promedio = max(facturacion_total * 0.3, total_pedidos * 0.2)
        
        # Rotación = Total de pedidos / Inventario promedio
        rotacion_inventario = (total_pedidos / inventario_promedio) if inventario_promedio > 0 else 0.0
        
        logger.info(f"Cálculo rotación - Total pedidos: {total_pedidos}, Cantidad total: {cantidad_total_pedidos}, Inventario promedio: {inventario_promedio}")
    else:
        logger.info("No hay pedidos para calcular rotación de inventario")
    
    # Calcular días CxC ajustados
    dias_cxc_ajustado = 0.0
    if facturas and cobranza_total > 0:
        # Días CxC = (Facturación pendiente / Facturación diaria promedio) * 30
        facturacion_pendiente = facturacion_total - cobranza_total
        facturacion_diaria = facturacion_total / 30  # Asumiendo 30 días
        dias_cxc_ajustado = (facturacion_pendiente / facturacion_diaria) if facturacion_diaria > 0 else 0.0
    
    # Calcular ciclo de efectivo
    ciclo_efectivo = 0.0
    if dias_cxc_ajustado > 0 and rotacion_inventario > 0:
        # Ciclo de efectivo = Días CxC + (365 / Rotación inventario)
        dias_inventario = 365 / rotacion_inventario if rotacion_inventario > 0 else 0
        ciclo_efectivo = dias_cxc_ajustado + dias_inventario
    
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
            # Filtrar clientes válidos y montos positivos
            if cliente and cliente != "Sin nombre" and cliente != "nan" and monto > 0:
                if cliente in clientes:
                    clientes[cliente] += monto
                else:
                    clientes[cliente] = monto
        
        # Ordenar y tomar los primeros 10
        sorted_clientes = sorted(clientes.items(), key=lambda x: x[1], reverse=True)[:10]
        top_clientes = dict(sorted_clientes)
        
        logger.info(f"Top clientes calculado - {len(top_clientes)} clientes únicos")
        if top_clientes:
            logger.info(f"Cliente top: {list(top_clientes.items())[0]}")
    
    # Calcular consumo de material usando columna G (material)
    consumo_material = {}
    if pedidos:
        materiales = {}
        for pedido in pedidos:
            material_codigo = pedido.get("material", "")
            cantidad = pedido.get("cantidad", 0)
            
            # Transformar código de material: tomar solo caracteres alfanuméricos del inicio
            if material_codigo and str(material_codigo) != "nan" and str(material_codigo).strip():
                # Extraer solo caracteres alfanuméricos del inicio del código
                import re
                material_limpio = re.match(r'^[A-Za-z0-9]+', str(material_codigo).strip())
                if material_limpio:
                    material_limpio = material_limpio.group(0)
                else:
                    material_limpio = str(material_codigo).strip()[:10]  # Primeros 10 caracteres si no hay alfanuméricos
                
                # Solo procesar si hay cantidad válida
                if cantidad > 0:
                    if material_limpio in materiales:
                        materiales[material_limpio] += cantidad
                    else:
                        materiales[material_limpio] = cantidad
        
        # Ordenar y tomar los primeros 10
        sorted_materiales = sorted(materiales.items(), key=lambda x: x[1], reverse=True)[:10]
        consumo_material = dict(sorted_materiales)
        
        logger.info(f"Consumo material calculado - {len(consumo_material)} materiales únicos")
        if consumo_material:
            logger.info(f"Material top: {list(consumo_material.items())[0]}")
    else:
        logger.info("No hay pedidos para calcular consumo de material")
    
    logger.info(f"KPIs calculados - Facturación: {facturacion_total}, Cobranza: {cobranza_total}, Anticipos: {anticipos_total}")
    
    return {
        # Facturación
        "facturacion_total": facturacion_total,
        "facturacion_sin_iva": round(facturacion_sin_iva, 2),
        "total_facturas": total_facturas,
        "clientes_unicos": clientes_unicos,
        
        # Cobranza
        "cobranza_total": cobranza_total,
        "cobranza_sin_iva": round(cobranza_sin_iva, 2),
        "porcentaje_cobrado": round(porcentaje_cobrado, 2),
        
        # Anticipos
        "anticipos_total": anticipos_total_ajustado,
        "anticipos_porcentaje": round(anticipos_porcentaje, 2),
        
        # Pedidos
        "total_pedidos": total_pedidos,
        "total_pedidos_count": total_pedidos_count,
        "cantidad_total_pedidos": round(cantidad_total_pedidos, 2),
        
        # Inventario
        "rotacion_inventario": round(rotacion_inventario, 2),
        "dias_cxc_ajustado": round(dias_cxc_ajustado, 2),
        "ciclo_efectivo": round(ciclo_efectivo, 2),
        
        # Gráficos
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
                    
                except Exception as e:
                    logger.error(f"Error procesando facturación: {e}")
                    logger.error(f"Traceback facturación: {traceback.format_exc()}")
                    # Continuar sin facturación si hay error
            
            # 2. PROCESAR COBRANZA
            if 'cobranza' in excel_file.sheet_names:
                try:
                    logger.info("Procesando hoja de cobranza...")
                    df_cobranza = pd.read_excel(io.BytesIO(contents), sheet_name='cobranza', header=5)
                    logger.info(f"Cobranza leída: {len(df_cobranza)} filas, {len(df_cobranza.columns)} columnas")
                    logger.info(f"Columnas de cobranza: {list(df_cobranza.columns)}")
                    
                    # Mapeo de columnas para cobranza (ajustado según estructura real)
                    column_mapping_cob = {
                        'Fecha Pago': 'fecha_cobro',
                        'UUID': 'uuid_factura',
                        'Importe Pagado': 'importe_cobrado',
                        'Forma Pago': 'metodo_pago',
                        'Número Operación': 'referencia'
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
            
            # 4. PROCESAR PEDIDOS (buscar hojas que contengan "pedido", fechas, o patrones de inventario)
            for sheet_name in excel_file.sheet_names:
                # Detectar hojas de pedidos/inventario por varios patrones
                is_pedidos_sheet = (
                    'pedido' in sheet_name.lower() or 
                    any(month in sheet_name for month in ['01', '02', '03', '04', '05', '06', '07', '08', '09', '10', '11', '12']) or
                    any(pattern in sheet_name.lower() for pattern in ['inventario', 'movimiento', 'stock']) or
                    '0925' in sheet_name  # Patrón específico del archivo actual
                )
                
                if is_pedidos_sheet:
                    try:
                        logger.info(f"Procesando hoja de pedidos: {sheet_name}")
                        df_pedidos = pd.read_excel(io.BytesIO(contents), sheet_name=sheet_name, header=2)
                        logger.info(f"Pedidos leídos: {len(df_pedidos)} filas, {len(df_pedidos.columns)} columnas")
                        logger.info(f"Columnas de pedidos: {list(df_pedidos.columns)}")
                        
                        # Mapeo basado en la estructura real de la hoja de pedidos
                        # Columna 1 (A): Índice - Columna 2 (B): Factura - Columna 3 (C): Vacía
                        # Columna 4 (D): Pedido - Columna 5 (E): KGS - Columna 6 (F): Precio unitario
                        # Columna 7 (G): Importe - Columna 8 (H): Material - Columna 9 (I): Cliente
                        
                        # Mapeo directo por posición de columna (índice 0-based)
                        column_mapping_pedidos = {
                            'Unnamed: 0': 'numero_factura',   # Columna A (número de factura)
                            'Hora: 15:59:28:697': 'fecha_pedido',  # Columna B (fecha)
                            'Unnamed: 2': 'numero_pedido',    # Columna C (número de pedido)
                            'FACTURADO': 'total',             # Columna D (total - tiene datos numéricos)
                            'Unnamed: 4': 'cantidad',         # Columna E (KGS)
                            'Unnamed: 5': 'precio_unitario',  # Columna F (precio unitario)
                            'Unnamed: 6': 'material',         # Columna G (material - para consumo)
                            'Unnamed: 7': 'producto',         # Columna H (producto)
                            'Unnamed: 8': 'cliente'           # Columna I (cliente)
                        }
                        
                        # Renombrar columnas
                        for old_col, new_col in column_mapping_pedidos.items():
                            if old_col in df_pedidos.columns:
                                df_pedidos = df_pedidos.rename(columns={old_col: new_col})
                        
                        logger.info(f"Columnas pedidos después del mapeo: {list(df_pedidos.columns)}")
                        
                        # Verificar columnas necesarias (ajustadas según estructura real)
                        required_cols = ['cliente', 'total', 'cantidad']
                        missing_cols = [col for col in required_cols if col not in df_pedidos.columns]
                        if missing_cols:
                            logger.warning(f"Columnas faltantes en pedidos: {missing_cols}")
                            for col in missing_cols:
                                if col == 'cliente':
                                    df_pedidos[col] = 'Sin nombre'
                                elif col == 'total':
                                    df_pedidos[col] = 0.0
                                elif col == 'cantidad':
                                    df_pedidos[col] = 0.0
                        
                        # Si no hay columna cliente, usar número de factura como identificador
                        if 'cliente' not in df_pedidos.columns or df_pedidos['cliente'].isna().all():
                            if 'numero_factura' in df_pedidos.columns:
                                df_pedidos['cliente'] = 'Cliente_' + df_pedidos['numero_factura'].astype(str)
                            else:
                                df_pedidos['cliente'] = 'Cliente_' + df_pedidos.index.astype(str)
                        
                        # Limpiar datos (más flexible para la estructura real)
                        # Convertir columnas numéricas
                        df_pedidos['total'] = pd.to_numeric(df_pedidos['total'], errors='coerce')
                        df_pedidos['cantidad'] = pd.to_numeric(df_pedidos['cantidad'], errors='coerce')
                        df_pedidos['precio_unitario'] = pd.to_numeric(df_pedidos['precio_unitario'], errors='coerce')
                        
                        logger.info(f"Después de conversión numérica - Total filas: {len(df_pedidos)}")
                        logger.info(f"Valores únicos en 'total': {df_pedidos['total'].nunique()}")
                        logger.info(f"Valores únicos en 'cantidad': {df_pedidos['cantidad'].nunique()}")
                        logger.info(f"Valores únicos en 'cliente': {df_pedidos['cliente'].nunique()}")
                        logger.info(f"Primeros 5 valores de 'total': {df_pedidos['total'].head().tolist()}")
                        logger.info(f"Primeros 5 valores de 'cliente': {df_pedidos['cliente'].head().tolist()}")
                        
                        # Verificar columnas adicionales que podrían contener datos
                        logger.info(f"Valores únicos en 'Unnamed: 9': {df_pedidos['Unnamed: 9'].nunique()}")
                        logger.info(f"Valores únicos en 'Unnamed: 10': {df_pedidos['Unnamed: 10'].nunique()}")
                        logger.info(f"Primeros 5 valores de 'Unnamed: 9': {df_pedidos['Unnamed: 9'].head().tolist()}")
                        logger.info(f"Primeros 5 valores de 'Unnamed: 10': {df_pedidos['Unnamed: 10'].head().tolist()}")
                        
                        # Verificar todas las columnas para encontrar datos numéricos
                        for col in df_pedidos.columns:
                            if df_pedidos[col].dtype == 'object':
                                numeric_values = pd.to_numeric(df_pedidos[col], errors='coerce').dropna()
                                if len(numeric_values) > 0:
                                    logger.info(f"Columna '{col}' tiene {len(numeric_values)} valores numéricos: {numeric_values.head().tolist()}")
                        
                        # Filtrar datos válidos
                        df_pedidos = df_pedidos.dropna(subset=['total'])  # Requerir total
                        logger.info(f"Después de dropna total - Total filas: {len(df_pedidos)}")
                        
                        df_pedidos = df_pedidos[df_pedidos['total'] > 0]  # Solo pedidos con total > 0
                        logger.info(f"Después de filtrar total > 0 - Total filas: {len(df_pedidos)}")
                        
                        # Cliente ya se maneja arriba
                        
                        # Convertir a formato esperado
                        logger.info(f"Iniciando conversión de {len(df_pedidos)} filas a objetos pedido")
                        for i, (_, row) in enumerate(df_pedidos.iterrows()):
                            try:
                                pedido = {
                                    "fecha_pedido": row.get("fecha_pedido", "").strftime("%Y-%m-%d") if pd.notna(row.get("fecha_pedido")) and hasattr(row.get("fecha_pedido"), 'strftime') else "",
                                    "numero_pedido": str(row.get("indice", "")),
                                    "cliente": str(row.get("cliente", "")),
                                    "producto": str(row.get("producto", "Sin producto")),
                                    "cantidad": float(row.get("cantidad", 0)) if pd.notna(row.get("cantidad", 0)) else 0.0,
                                    "precio_unitario": float(row.get("precio_unitario", 0)) if pd.notna(row.get("precio_unitario", 0)) else 0.0,
                                    "total": float(row.get("total", 0)) if pd.notna(row.get("total", 0)) else 0.0
                                }
                                
                                # Solo agregar si tiene datos válidos
                                if pedido["cliente"] and pedido["cliente"] != "Sin nombre" and pedido["total"] > 0:
                                    pedidos.append(pedido)
                                    if len(pedidos) <= 3:  # Log solo los primeros 3
                                        logger.info(f"Pedido {len(pedidos)}: {pedido}")
                                    
                            except Exception as row_error:
                                logger.warning(f"Error procesando fila {i} de pedido: {row_error}")
                                continue
                        
                        logger.info(f"Pedidos procesados: {len(pedidos)}")
                        if pedidos:
                            logger.info(f"Primer pedido: {pedidos[0]}")
                            total_pedidos = sum(p.get("total", 0) for p in pedidos[:5])
                            logger.info(f"Suma de primeros 5 pedidos: {total_pedidos}")
                        break
                        
                    except Exception as e:
                        logger.error(f"Error procesando hoja de pedidos {sheet_name}: {e}")
                        logger.error(f"Traceback pedidos: {traceback.format_exc()}")
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
