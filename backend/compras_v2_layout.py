"""
Layout optimizado para compras_v2 y compras_v2_materiales
Version simplificada sin caracteres especiales
"""

import os
import psycopg2
from psycopg2.extras import RealDictCursor
import logging

# Configurar logging
logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)

def load_production_config():
    """Carga la configuración desde production.env"""
    env_file = "production.env"
    
    if not os.path.exists(env_file):
        logger.error(f"Archivo {env_file} no encontrado")
        return None
    
    config = {}
    with open(env_file, 'r') as f:
        for line in f:
            line = line.strip()
            if line and not line.startswith('#') and '=' in line:
                key, value = line.split('=', 1)
                config[key] = value
    
    return config

def get_supabase_connection():
    """Obtiene conexión a Supabase usando la configuración de production.env"""
    try:
        config = load_production_config()
        if not config:
            return None
        
        database_url = config.get("DATABASE_URL")
        
        if not database_url:
            logger.error("DATABASE_URL no encontrada en production.env")
            return None
        
        conn = psycopg2.connect(
            database_url,
            cursor_factory=RealDictCursor,
            sslmode='require',
            connect_timeout=30
        )
        
        return conn
        
    except Exception as e:
        logger.error(f"Error conectando a Supabase: {str(e)}")
        return None

def create_optimized_layout():
    """Crea el layout optimizado con las columnas necesarias"""
    
    print("\n" + "="*80)
    print("LAYOUT OPTIMIZADO PARA COMPRAS_V2 Y COMPRAS_V2_MATERIALES")
    print("="*80)
    
    print("\nCOLUMNAS NECESARIAS EN EL EXCEL DE COMPRAS:")
    print("-" * 50)
    
    # Columnas obligatorias para compras_v2
    compras_v2_required = [
        ("IMI", "Numero unico de compra (clave primaria)"),
        ("Proveedor", "Nombre del proveedor (debe existir en tabla Proveedores)"),
        ("Fecha Pedido", "Fecha de pedido (para calcular fechas estimadas)"),
        ("Moneda", "Moneda de la compra (USD, EUR, etc.)"),
        ("Dias Credito", "Dias de credito del proveedor"),
        ("Anticipo %", "Porcentaje de anticipo"),
        ("Anticipo Monto", "Monto del anticipo en divisa"),
        ("Fecha Anticipo", "Fecha de pago del anticipo"),
        ("Fecha Pago Factura", "Fecha de pago de la factura"),
        ("Tipo Cambio Estimado", "Tipo de cambio estimado"),
        ("Tipo Cambio Real", "Tipo de cambio real"),
        ("Gastos Importacion Divisa", "Gastos de importacion en divisa"),
        ("Porcentaje Gastos Importacion", "Porcentaje de gastos de importacion"),
        ("IVA Monto Divisa", "IVA en divisa"),
        ("Total Con IVA Divisa", "Total con IVA en divisa")
    ]
    
    print("COMPRAS_V2 (Informacion general de la compra):")
    for col, desc in compras_v2_required:
        print(f"  [X] {col:<25} - {desc}")
    
    # Columnas obligatorias para compras_v2_materiales
    materiales_required = [
        ("Material Codigo", "Codigo del material/producto"),
        ("KG", "Cantidad en kilogramos"),
        ("PU Divisa", "Precio unitario en divisa"),
        ("PU MXN", "Precio unitario en MXN"),
        ("Costo Total Divisa", "Costo total en divisa"),
        ("Costo Total MXN", "Costo total en MXN"),
        ("IVA", "IVA del material")
    ]
    
    print(f"\nCOMPRAS_V2_MATERIALES (Detalle de materiales):")
    for col, desc in materiales_required:
        print(f"  [X] {col:<25} - {desc}")
    
    # Columnas calculadas automáticamente
    calculated_fields = [
        ("Puerto Origen", "Se obtiene de Proveedores.Puerto"),
        ("Fecha Salida Estimada", "Fecha Pedido + Promedio Dias Produccion"),
        ("Fecha Arribo Estimada", "Fecha Salida + Promedio Dias Transporte"),
        ("Gastos Importacion MXN", "Gastos Divisa × Tipo Cambio"),
        ("IVA Monto MXN", "IVA Divisa × Tipo Cambio"),
        ("Total Con IVA MXN", "Total Divisa × Tipo Cambio"),
        ("PU MXN Importacion", "PU MXN × (1 + % Gastos)"),
        ("Costo Total MXN Importacion", "Costo Total MXN × (1 + % Gastos)"),
        ("Costo Total Con IVA", "Costo Total MXN Importacion + IVA")
    ]
    
    print(f"\nCAMPOS CALCULADOS AUTOMATICAMENTE:")
    for col, desc in calculated_fields:
        print(f"  [*] {col:<25} - {desc}")
    
    # Estructura del Excel recomendada
    print(f"\nESTRUCTURA RECOMENDADA DEL EXCEL:")
    print("-" * 50)
    print("HOJA 1: 'Compras Generales'")
    print("  - Una fila por compra (IMI)")
    print("  - Columnas: IMI, Proveedor, Fecha Pedido, Moneda, etc.")
    print("")
    print("HOJA 2: 'Materiales Detalle'")
    print("  - Una fila por material de cada compra")
    print("  - Columnas: IMI, Material Codigo, KG, PU Divisa, etc.")
    print("")
    print("HOJA 3: 'Proveedores' (opcional)")
    print("  - Informacion de proveedores si no existe en BD")
    print("  - Columnas: Nombre, Puerto, Dias Produccion, Dias Transporte")
    
    # Mapeo de columnas robusto
    print(f"\nMAPEO ROBUSTO DE COLUMNAS:")
    print("-" * 50)
    
    column_mapping = {
        # Compras_v2
        "IMI": ["imi", "IMI", "Imi", "numero_imi", "Numero IMI"],
        "Proveedor": ["proveedor", "Proveedor", "PROVEEDOR", "supplier", "Supplier"],
        "Fecha Pedido": ["fecha_pedido", "Fecha Pedido", "FECHA PEDIDO", "fecha_compra", "Fecha Compra"],
        "Moneda": ["moneda", "Moneda", "MONEDA", "currency", "Currency", "divisa", "Divisa"],
        "Dias Credito": ["dias_credito", "Dias Credito", "DIAS CREDITO", "credit_days", "Credit Days"],
        "Anticipo %": ["anticipo_pct", "Anticipo %", "ANTICIPO PCT", "advance_pct", "Advance %"],
        "Anticipo Monto": ["anticipo_monto", "Anticipo Monto", "ANTICIPO MONTO", "advance_amount", "Advance Amount"],
        "Fecha Anticipo": ["fecha_anticipo", "Fecha Anticipo", "FECHA ANTICIPO", "advance_date", "Advance Date"],
        "Fecha Pago Factura": ["fecha_pago_factura", "Fecha Pago Factura", "FECHA PAGO FACTURA", "payment_date", "Payment Date"],
        "Tipo Cambio Estimado": ["tipo_cambio_estimado", "Tipo Cambio Estimado", "TC ESTIMADO", "estimated_rate", "Estimated Rate"],
        "Tipo Cambio Real": ["tipo_cambio_real", "Tipo Cambio Real", "TC REAL", "actual_rate", "Actual Rate"],
        "Gastos Importacion Divisa": ["gastos_importacion_divisa", "Gastos Importacion Divisa", "GASTOS IMP DIVISA", "import_costs", "Import Costs"],
        "Porcentaje Gastos Importacion": ["porcentaje_gastos_importacion", "Porcentaje Gastos Importacion", "% GASTOS IMP", "import_percentage", "Import %"],
        "IVA Monto Divisa": ["iva_monto_divisa", "IVA Monto Divisa", "IVA DIVISA", "tax_amount", "Tax Amount"],
        "Total Con IVA Divisa": ["total_con_iva_divisa", "Total Con IVA Divisa", "TOTAL IVA DIVISA", "total_with_tax", "Total With Tax"],
        
        # Compras_v2_materiales
        "Material Codigo": ["material_codigo", "Material Codigo", "MATERIAL CODIGO", "material_code", "Material Code", "concepto", "Concepto"],
        "KG": ["kg", "KG", "kilogramos", "Kilogramos", "KILOGRAMOS", "quantity", "Quantity", "cantidad", "Cantidad"],
        "PU Divisa": ["pu_divisa", "PU Divisa", "PU DIVISA", "unit_price", "Unit Price", "precio_unitario", "Precio Unitario"],
        "PU MXN": ["pu_mxn", "PU MXN", "precio_mxn", "Precio MXN", "PRECIO MXN"],
        "Costo Total Divisa": ["costo_total_divisa", "Costo Total Divisa", "COSTO TOTAL DIVISA", "total_cost", "Total Cost"],
        "Costo Total MXN": ["costo_total_mxn", "Costo Total MXN", "COSTO TOTAL MXN"],
        "IVA": ["iva", "IVA", "tax", "Tax"]
    }
    
    for standard_name, variations in column_mapping.items():
        print(f"  {standard_name:<25} -> {', '.join(variations[:3])}{'...' if len(variations) > 3 else ''}")
    
    print(f"\nVALIDACIONES AUTOMATICAS:")
    print("-" * 50)
    print("  [X] Verificar que el proveedor existe en tabla Proveedores")
    print("  [X] Validar formato de fechas (YYYY-MM-DD)")
    print("  [X] Convertir numeros con comas y puntos correctamente")
    print("  [X] Validar que IMI sea unico")
    print("  [X] Verificar que KG > 0")
    print("  [X] Validar monedas conocidas (USD, EUR, MXN)")
    print("  [X] Calcular campos derivados automaticamente")
    
    print(f"\nBENEFICIOS DEL NUEVO SISTEMA:")
    print("-" * 50)
    print("  [X] Separacion clara entre compras y materiales")
    print("  [X] Calculos automaticos con datos de proveedores")
    print("  [X] Fechas estimadas precisas")
    print("  [X] Manejo robusto de diferentes formatos de Excel")
    print("  [X] Validaciones automaticas de integridad")
    print("  [X] Escalabilidad para futuras mejoras")
    
    print(f"\nTABLA RESUMEN DE COLUMNAS NECESARIAS:")
    print("="*80)
    print(f"{'COLUMNA':<30} {'TIPO':<15} {'OBLIGATORIO':<12} {'DESCRIPCION'}")
    print("-"*80)
    
    # Tabla resumen
    all_columns = [
        # Compras_v2 obligatorias
        ("IMI", "INTEGER", "SI", "Numero unico de compra"),
        ("Proveedor", "TEXT", "SI", "Nombre del proveedor"),
        ("Fecha Pedido", "DATE", "SI", "Fecha de pedido"),
        ("Moneda", "VARCHAR", "SI", "Moneda de la compra"),
        ("Dias Credito", "INTEGER", "NO", "Dias de credito"),
        ("Anticipo %", "NUMERIC", "NO", "Porcentaje de anticipo"),
        ("Anticipo Monto", "NUMERIC", "NO", "Monto del anticipo"),
        ("Fecha Anticipo", "DATE", "NO", "Fecha de pago anticipo"),
        ("Fecha Pago Factura", "DATE", "NO", "Fecha de pago factura"),
        ("Tipo Cambio Estimado", "NUMERIC", "NO", "Tipo de cambio estimado"),
        ("Tipo Cambio Real", "NUMERIC", "NO", "Tipo de cambio real"),
        ("Gastos Importacion Divisa", "NUMERIC", "NO", "Gastos en divisa"),
        ("Porcentaje Gastos Importacion", "NUMERIC", "NO", "% gastos importacion"),
        ("IVA Monto Divisa", "NUMERIC", "NO", "IVA en divisa"),
        ("Total Con IVA Divisa", "NUMERIC", "NO", "Total con IVA en divisa"),
        
        # Compras_v2_materiales obligatorias
        ("Material Codigo", "VARCHAR", "SI", "Codigo del material"),
        ("KG", "NUMERIC", "SI", "Cantidad en kilogramos"),
        ("PU Divisa", "NUMERIC", "SI", "Precio unitario en divisa"),
        ("PU MXN", "NUMERIC", "SI", "Precio unitario en MXN"),
        ("Costo Total Divisa", "NUMERIC", "SI", "Costo total en divisa"),
        ("Costo Total MXN", "NUMERIC", "SI", "Costo total en MXN"),
        ("IVA", "NUMERIC", "NO", "IVA del material")
    ]
    
    for col, tipo, obligatorio, desc in all_columns:
        print(f"{col:<30} {tipo:<15} {obligatorio:<12} {desc}")

if __name__ == "__main__":
    print("LAYOUT OPTIMIZADO PARA COMPRAS_V2 Y COMPRAS_V2_MATERIALES")
    print("="*60)
    
    # Crear layout optimizado
    create_optimized_layout()
