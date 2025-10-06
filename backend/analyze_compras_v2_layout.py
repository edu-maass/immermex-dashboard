"""
Layout optimizado para compras_v2 y compras_v2_materiales
Análisis de columnas necesarias para poblar toda la base de datos
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

def analyze_table_structure():
    """Analiza la estructura de las tablas compras_v2 y compras_v2_materiales"""
    conn = get_supabase_connection()
    if not conn:
        return False
    
    try:
        cursor = conn.cursor()
        
        # Analizar compras_v2
        print("ESTRUCTURA DE LA TABLA 'compras_v2':")
        print("="*60)
        cursor.execute("""
            SELECT column_name, data_type, is_nullable, column_default
            FROM information_schema.columns 
            WHERE table_name = 'compras_v2' 
            ORDER BY ordinal_position
        """)
        
        compras_v2_columns = cursor.fetchall()
        
        print("Columnas de compras_v2:")
        for col in compras_v2_columns:
            nullable = "NULL" if col['is_nullable'] == 'YES' else "NOT NULL"
            default = f" DEFAULT {col['column_default']}" if col['column_default'] else ""
            print(f"  - {col['column_name']} ({col['data_type']}) {nullable}{default}")
        
        # Analizar compras_v2_materiales
        print(f"\nESTRUCTURA DE LA TABLA 'compras_v2_materiales':")
        print("="*60)
        cursor.execute("""
            SELECT column_name, data_type, is_nullable, column_default
            FROM information_schema.columns 
            WHERE table_name = 'compras_v2_materiales' 
            ORDER BY ordinal_position
        """)
        
        materiales_columns = cursor.fetchall()
        
        print("Columnas de compras_v2_materiales:")
        for col in materiales_columns:
            nullable = "NULL" if col['is_nullable'] == 'YES' else "NOT NULL"
            default = f" DEFAULT {col['column_default']}" if col['column_default'] else ""
            print(f"  - {col['column_name']} ({col['data_type']}) {nullable}{default}")
        
        # Analizar Proveedores
        print(f"\nESTRUCTURA DE LA TABLA 'Proveedores':")
        print("="*60)
        cursor.execute("""
            SELECT column_name, data_type, is_nullable, column_default
            FROM information_schema.columns 
            WHERE table_name = 'Proveedores' 
            ORDER BY ordinal_position
        """)
        
        proveedores_columns = cursor.fetchall()
        
        print("Columnas de Proveedores:")
        for col in proveedores_columns:
            nullable = "NULL" if col['is_nullable'] == 'YES' else "NOT NULL"
            default = f" DEFAULT {col['column_default']}" if col['column_default'] else ""
            print(f"  - {col['column_name']} ({col['data_type']}) {nullable}{default}")
        
        cursor.close()
        conn.close()
        
        return True
        
    except Exception as e:
        logger.error(f"Error analizando estructura: {str(e)}")
        try:
            conn.close()
        except:
            pass
        return False

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
        print(f"  ✓ {col:<25} - {desc}")
    
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
        print(f"  ✓ {col:<25} - {desc}")
    
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
        print(f"  ⚡ {col:<25} - {desc}")
    
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
        "IMI": ["imi", "IMI", "Imi", "numero_imi", "Número IMI"],
        "Proveedor": ["proveedor", "Proveedor", "PROVEEDOR", "supplier", "Supplier"],
        "Fecha Pedido": ["fecha_pedido", "Fecha Pedido", "FECHA PEDIDO", "fecha_compra", "Fecha Compra"],
        "Moneda": ["moneda", "Moneda", "MONEDA", "currency", "Currency", "divisa", "Divisa"],
        "Días Crédito": ["dias_credito", "Días Crédito", "DIAS CREDITO", "credit_days", "Credit Days"],
        "Anticipo %": ["anticipo_pct", "Anticipo %", "ANTICIPO PCT", "advance_pct", "Advance %"],
        "Anticipo Monto": ["anticipo_monto", "Anticipo Monto", "ANTICIPO MONTO", "advance_amount", "Advance Amount"],
        "Fecha Anticipo": ["fecha_anticipo", "Fecha Anticipo", "FECHA ANTICIPO", "advance_date", "Advance Date"],
        "Fecha Pago Factura": ["fecha_pago_factura", "Fecha Pago Factura", "FECHA PAGO FACTURA", "payment_date", "Payment Date"],
        "Tipo Cambio Estimado": ["tipo_cambio_estimado", "Tipo Cambio Estimado", "TC ESTIMADO", "estimated_rate", "Estimated Rate"],
        "Tipo Cambio Real": ["tipo_cambio_real", "Tipo Cambio Real", "TC REAL", "actual_rate", "Actual Rate"],
        "Gastos Importación Divisa": ["gastos_importacion_divisa", "Gastos Importación Divisa", "GASTOS IMP DIVISA", "import_costs", "Import Costs"],
        "Porcentaje Gastos Importación": ["porcentaje_gastos_importacion", "Porcentaje Gastos Importación", "% GASTOS IMP", "import_percentage", "Import %"],
        "IVA Monto Divisa": ["iva_monto_divisa", "IVA Monto Divisa", "IVA DIVISA", "tax_amount", "Tax Amount"],
        "Total Con IVA Divisa": ["total_con_iva_divisa", "Total Con IVA Divisa", "TOTAL IVA DIVISA", "total_with_tax", "Total With Tax"],
        
        # Compras_v2_materiales
        "Material Código": ["material_codigo", "Material Código", "MATERIAL CODIGO", "material_code", "Material Code", "concepto", "Concepto"],
        "KG": ["kg", "KG", "kilogramos", "Kilogramos", "KILOGRAMOS", "quantity", "Quantity", "cantidad", "Cantidad"],
        "PU Divisa": ["pu_divisa", "PU Divisa", "PU DIVISA", "unit_price", "Unit Price", "precio_unitario", "Precio Unitario"],
        "PU MXN": ["pu_mxn", "PU MXN", "precio_mxn", "Precio MXN", "PRECIO MXN"],
        "Costo Total Divisa": ["costo_total_divisa", "Costo Total Divisa", "COSTO TOTAL DIVISA", "total_cost", "Total Cost"],
        "Costo Total MXN": ["costo_total_mxn", "Costo Total MXN", "COSTO TOTAL MXN"],
        "IVA": ["iva", "IVA", "tax", "Tax"]
    }
    
    for standard_name, variations in column_mapping.items():
        print(f"  {standard_name:<25} → {', '.join(variations[:3])}{'...' if len(variations) > 3 else ''}")
    
    print(f"\nVALIDACIONES AUTOMATICAS:")
    print("-" * 50)
    print("  ✓ Verificar que el proveedor existe en tabla Proveedores")
    print("  ✓ Validar formato de fechas (YYYY-MM-DD)")
    print("  ✓ Convertir numeros con comas y puntos correctamente")
    print("  ✓ Validar que IMI sea unico")
    print("  ✓ Verificar que KG > 0")
    print("  ✓ Validar monedas conocidas (USD, EUR, MXN)")
    print("  ✓ Calcular campos derivados automaticamente")
    
    print(f"\nBENEFICIOS DEL NUEVO SISTEMA:")
    print("-" * 50)
    print("  ✓ Separacion clara entre compras y materiales")
    print("  ✓ Calculos automaticos con datos de proveedores")
    print("  ✓ Fechas estimadas precisas")
    print("  ✓ Manejo robusto de diferentes formatos de Excel")
    print("  ✓ Validaciones automaticas de integridad")
    print("  ✓ Escalabilidad para futuras mejoras")

if __name__ == "__main__":
    print("ANÁLISIS DE ESTRUCTURA DE TABLAS COMPRAS_V2")
    print("="*60)
    
    # Analizar estructura de tablas
    structure_success = analyze_table_structure()
    
    if structure_success:
        # Crear layout optimizado
        create_optimized_layout()
    else:
        print("Error analizando estructura de tablas")
