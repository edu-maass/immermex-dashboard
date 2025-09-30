"""
Script para analizar la estructura del archivo de compras existente
Lee la pestaña 'Resumen Compras' y adapta el mapeo de columnas
"""

import pandas as pd
import os
import sys
from pathlib import Path

def analyze_excel_structure(file_path):
    """Analiza la estructura del archivo Excel de compras"""
    
    print("="*60)
    print("ANALISIS DE ESTRUCTURA DE ARCHIVO DE COMPRAS")
    print("="*60)
    
    try:
        # Leer todas las pestañas del archivo
        excel_file = pd.ExcelFile(file_path)
        print(f"Pestañas encontradas: {excel_file.sheet_names}")
        
        # Buscar la pestaña de resumen compras
        resumen_sheet = None
        for sheet_name in excel_file.sheet_names:
            if 'resumen' in sheet_name.lower() and 'compra' in sheet_name.lower():
                resumen_sheet = sheet_name
                break
        
        if not resumen_sheet:
            print("No se encontró pestaña 'Resumen Compras'")
            print("Pestañas disponibles:")
            for i, sheet in enumerate(excel_file.sheet_names, 1):
                print(f"   {i}. {sheet}")
            
            # Usar la primera pestaña como alternativa
            resumen_sheet = excel_file.sheet_names[0]
            print(f"\nAnalizando pestaña: {resumen_sheet}")
        else:
            print(f"Pestaña encontrada: {resumen_sheet}")
        
        # Leer la pestaña de resumen
        df = pd.read_excel(file_path, sheet_name=resumen_sheet)
        
        print(f"\nInformacion de la pestaña '{resumen_sheet}':")
        print(f"   - Filas: {len(df)}")
        print(f"   - Columnas: {len(df.columns)}")
        
        print(f"\nColumnas encontradas:")
        for i, col in enumerate(df.columns, 1):
            print(f"   {i:2d}. {col}")
        
        # Mostrar primeras filas para entender la estructura
        print(f"\nPrimeras 5 filas de datos:")
        print(df.head().to_string())
        
        # Analizar tipos de datos
        print(f"\nTipos de datos:")
        for col in df.columns:
            dtype = df[col].dtype
            non_null = df[col].notna().sum()
            print(f"   {col}: {dtype} ({non_null} valores no nulos)")
        
        return df, resumen_sheet
        
    except Exception as e:
        print(f"Error analizando archivo: {e}")
        return None, None

def generate_column_mapping(df):
    """Genera mapeo de columnas basado en la estructura real"""
    
    print(f"\n" + "="*60)
    print("GENERANDO MAPEO DE COLUMNAS")
    print("="*60)
    
    # Mapeo estándar que ya tenemos
    standard_mapping = {
        'fecha_compra': ['fecha', 'fecha_compra', 'date', 'fecha_factura'],
        'numero_factura': ['factura', 'numero_factura', 'folio', 'invoice'],
        'proveedor': ['proveedor', 'supplier', 'vendor', 'cliente'],
        'concepto': ['concepto', 'descripcion', 'description', 'detalle'],
        'categoria': ['categoria', 'category', 'tipo', 'clasificacion'],
        'subcategoria': ['subcategoria', 'subcategory', 'sub_tipo'],
        'cantidad': ['cantidad', 'quantity', 'qty', 'unidades'],
        'unidad': ['unidad', 'unit', 'medida', 'uom'],
        'precio_unitario': ['precio_unitario', 'unit_price', 'precio', 'costo_unitario'],
        'subtotal': ['subtotal', 'sub_total', 'importe_sin_iva'],
        'iva': ['iva', 'tax', 'impuesto'],
        'total': ['total', 'importe_total', 'amount'],
        'moneda': ['moneda', 'currency', 'curr'],
        'forma_pago': ['forma_pago', 'payment_method', 'metodo_pago'],
        'dias_credito': ['dias_credito', 'credit_days', 'dias'],
        'fecha_vencimiento': ['fecha_vencimiento', 'due_date', 'vencimiento'],
        'fecha_pago': ['fecha_pago', 'payment_date', 'fecha_cobro'],
        'centro_costo': ['centro_costo', 'cost_center', 'departamento'],
        'proyecto': ['proyecto', 'project', 'obra'],
        'notas': ['notas', 'notes', 'observaciones', 'comentarios']
    }
    
    # Encontrar coincidencias
    found_mappings = {}
    unmatched_columns = []
    
    for standard_field, possible_names in standard_mapping.items():
        found_column = None
        
        for col in df.columns:
            col_lower = str(col).lower().strip()
            for possible_name in possible_names:
                if possible_name.lower() in col_lower or col_lower in possible_name.lower():
                    found_column = col
                    break
            if found_column:
                break
        
        if found_column:
            found_mappings[standard_field] = found_column
            print(f"ENCONTRADO: {standard_field} -> {found_column}")
        else:
            print(f"NO ENCONTRADO: {standard_field}")
    
    # Columnas no mapeadas
    mapped_columns = set(found_mappings.values())
    for col in df.columns:
        if col not in mapped_columns:
            unmatched_columns.append(col)
    
    if unmatched_columns:
        print(f"\nColumnas no mapeadas:")
        for col in unmatched_columns:
            print(f"   - {col}")
    
    return found_mappings, unmatched_columns

def create_custom_mapping_file(mappings, unmatched_columns, file_path):
    """Crea archivo de mapeo personalizado"""
    
    print(f"\n" + "="*60)
    print("CREANDO ARCHIVO DE MAPEO PERSONALIZADO")
    print("="*60)
    
    mapping_content = f'''"""
Mapeo de columnas personalizado para archivo de compras
Archivo analizado: {file_path}
"""

# Mapeo encontrado automaticamente
AUTO_MAPPING = {{
'''
    
    for standard_field, excel_column in mappings.items():
        mapping_content += f"    '{standard_field}': '{excel_column}',\n"
    
    mapping_content += "}\n\n"
    
    if unmatched_columns:
        mapping_content += "# Columnas no mapeadas - revisar manualmente\n"
        mapping_content += "UNMAPPED_COLUMNS = [\n"
        for col in unmatched_columns:
            mapping_content += f"    '{col}',\n"
        mapping_content += "]\n\n"
    
    mapping_content += '''# Mapeo manual adicional (completar segun necesidad)
MANUAL_MAPPING = {
    # Ejemplo: 'campo_personalizado': 'columna_excel',
}

# Mapeo final combinado
FINAL_MAPPING = {**AUTO_MAPPING, **MANUAL_MAPPING}
'''
    
    # Guardar archivo
    output_file = "custom_column_mapping.py"
    with open(output_file, 'w', encoding='utf-8') as f:
        f.write(mapping_content)
    
    print(f"Archivo de mapeo creado: {output_file}")
    print(f"Revisa y completa el mapeo manual segun tus necesidades")

def main():
    """Función principal"""
    
    # Ruta del archivo
    file_path = "../docs/IMM-Compras de  importacion (Compartido).xlsx"
    
    if not os.path.exists(file_path):
        print(f"ERROR: Archivo no encontrado: {file_path}")
        print("INFO: Asegurate de que el archivo este en la ubicacion correcta")
        return
    
    print(f"Analizando archivo: {file_path}")
    
    # Analizar estructura
    df, sheet_name = analyze_excel_structure(file_path)
    
    if df is None:
        print("No se pudo analizar el archivo")
        return
    
    # Generar mapeo
    mappings, unmatched = generate_column_mapping(df)
    
    # Crear archivo de mapeo personalizado
    create_custom_mapping_file(mappings, unmatched, file_path)
    
    print(f"\n" + "="*60)
    print("ANALISIS COMPLETADO")
    print("="*60)
    print("Proximos pasos:")
    print("1. Revisa el archivo 'custom_column_mapping.py'")
    print("2. Completa el mapeo manual para columnas no encontradas")
    print("3. Actualiza el servicio de importacion con el mapeo personalizado")
    print("4. Prueba la importacion con tu archivo real")

if __name__ == "__main__":
    main()