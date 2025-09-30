"""
Script avanzado para analizar archivos Excel con estructura compleja
Analiza la pestaña 'Resumen Compras' con mejor detección de headers
"""

import pandas as pd
import os
import sys
import numpy as np

def analyze_excel_with_headers(file_path):
    """Analiza el archivo Excel buscando los headers reales"""
    
    print("="*60)
    print("ANALISIS AVANZADO DE ARCHIVO EXCEL")
    print("="*60)
    
    try:
        # Leer la pestaña 'Resumen Compras'
        df = pd.read_excel(file_path, sheet_name='Resumen Compras', header=None)
        
        print(f"Archivo leído: {len(df)} filas, {len(df.columns)} columnas")
        
        # Buscar la fila que contiene los headers reales
        header_row = None
        for i in range(min(20, len(df))):  # Buscar en las primeras 20 filas
            row = df.iloc[i]
            # Buscar fila con múltiples valores no nulos que parezcan headers
            non_null_count = row.notna().sum()
            if non_null_count > 5:  # Si tiene más de 5 valores no nulos
                # Verificar si contiene palabras que parezcan headers
                row_str = ' '.join([str(x) for x in row.dropna()]).lower()
                if any(keyword in row_str for keyword in ['fecha', 'proveedor', 'factura', 'importe', 'total', 'cantidad']):
                    header_row = i
                    break
        
        if header_row is not None:
            print(f"Header encontrado en fila: {header_row}")
            
            # Usar esa fila como header
            df_with_headers = pd.read_excel(file_path, sheet_name='Resumen Compras', header=header_row)
            
            # Limpiar nombres de columnas
            df_with_headers.columns = [str(col).strip() if pd.notna(col) else f'Col_{i}' for i, col in enumerate(df_with_headers.columns)]
            
            print(f"\nColumnas encontradas:")
            for i, col in enumerate(df_with_headers.columns, 1):
                print(f"   {i:2d}. {col}")
            
            # Mostrar primeras filas de datos reales
            print(f"\nPrimeras 5 filas de datos:")
            print(df_with_headers.head().to_string())
            
            # Analizar contenido de cada columna
            print(f"\nAnálisis de contenido por columna:")
            for col in df_with_headers.columns:
                non_null = df_with_headers[col].notna().sum()
                if non_null > 0:
                    sample_values = df_with_headers[col].dropna().head(3).tolist()
                    print(f"   {col}: {non_null} valores, ejemplos: {sample_values}")
            
            return df_with_headers
            
        else:
            print("No se encontró una fila de headers clara")
            print("Mostrando primeras 10 filas para análisis manual:")
            print(df.head(10).to_string())
            return None
            
    except Exception as e:
        print(f"Error analizando archivo: {e}")
        return None

def analyze_specific_columns(df):
    """Analiza columnas específicas para identificar campos de compras"""
    
    print(f"\n" + "="*60)
    print("ANALISIS DE CAMPOS ESPECIFICOS")
    print("="*60)
    
    # Buscar columnas que contengan información de compras
    compras_fields = {}
    
    for col in df.columns:
        col_lower = str(col).lower()
        
        # Buscar campos de fecha
        if any(keyword in col_lower for keyword in ['fecha', 'date', 'dia']):
            compras_fields['fecha'] = col
            print(f"FECHA encontrada: {col}")
        
        # Buscar campos de proveedor
        elif any(keyword in col_lower for keyword in ['proveedor', 'supplier', 'vendor', 'cliente']):
            compras_fields['proveedor'] = col
            print(f"PROVEEDOR encontrado: {col}")
        
        # Buscar campos de factura
        elif any(keyword in col_lower for keyword in ['factura', 'folio', 'invoice', 'numero']):
            compras_fields['factura'] = col
            print(f"FACTURA encontrada: {col}")
        
        # Buscar campos de importe/total
        elif any(keyword in col_lower for keyword in ['total', 'importe', 'amount', 'valor', 'precio']):
            compras_fields['total'] = col
            print(f"TOTAL encontrado: {col}")
        
        # Buscar campos de cantidad
        elif any(keyword in col_lower for keyword in ['cantidad', 'quantity', 'qty', 'unidades']):
            compras_fields['cantidad'] = col
            print(f"CANTIDAD encontrada: {col}")
        
        # Buscar campos de concepto/descripción
        elif any(keyword in col_lower for keyword in ['concepto', 'descripcion', 'description', 'detalle']):
            compras_fields['concepto'] = col
            print(f"CONCEPTO encontrado: {col}")
    
    return compras_fields

def create_sample_mapping(df, compras_fields):
    """Crea un mapeo de muestra basado en los campos encontrados"""
    
    print(f"\n" + "="*60)
    print("CREANDO MAPEO DE MUESTRA")
    print("="*60)
    
    mapping_content = f'''"""
Mapeo de columnas para archivo de compras Immermex
Archivo: IMM-Compras de importacion (Compartido).xlsx
Pestaña: Resumen Compras
"""

# Campos identificados automáticamente
IDENTIFIED_FIELDS = {{
'''
    
    for field_type, column_name in compras_fields.items():
        mapping_content += f"    '{field_type}': '{column_name}',\n"
    
    mapping_content += "}\n\n"
    
    mapping_content += '''# Mapeo completo sugerido (completar según necesidad)
COMPRAS_MAPPING = {
    # Campos básicos
    'fecha_compra': None,  # Mapear a columna de fecha
    'numero_factura': None,  # Mapear a columna de factura/folio
    'proveedor': None,  # Mapear a columna de proveedor
    'concepto': None,  # Mapear a columna de concepto/descripción
    
    # Campos financieros
    'cantidad': None,  # Mapear a columna de cantidad
    'precio_unitario': None,  # Mapear a columna de precio unitario
    'subtotal': None,  # Mapear a columna de subtotal
    'iva': None,  # Mapear a columna de IVA
    'total': None,  # Mapear a columna de total
    
    # Campos adicionales
    'moneda': 'MXN',  # Valor fijo o mapear a columna
    'forma_pago': None,  # Mapear a columna de forma de pago
    'dias_credito': 30,  # Valor por defecto o mapear a columna
    'categoria': None,  # Mapear a columna de categoría
    'centro_costo': None,  # Mapear a columna de centro de costo
    'proyecto': None,  # Mapear a columna de proyecto
}

# Función para aplicar el mapeo
def apply_mapping(df):
    """Aplica el mapeo a un DataFrame"""
    mapped_df = pd.DataFrame()
    
    for target_field, source_column in COMPRAS_MAPPING.items():
        if source_column is None:
            mapped_df[target_field] = None
        elif isinstance(source_column, str) and source_column in df.columns:
            mapped_df[target_field] = df[source_column]
        else:
            mapped_df[target_field] = source_column
    
    return mapped_df
'''
    
    # Guardar archivo
    with open("immermex_compras_mapping.py", 'w', encoding='utf-8') as f:
        f.write(mapping_content)
    
    print(f"Archivo de mapeo creado: immermex_compras_mapping.py")
    print(f"Campos identificados: {len(compras_fields)}")
    
    return compras_fields

def main():
    """Función principal"""
    
    file_path = "../docs/IMM-Compras de  importacion (Compartido).xlsx"
    
    if not os.path.exists(file_path):
        print(f"ERROR: Archivo no encontrado: {file_path}")
        return
    
    print(f"Analizando archivo: {file_path}")
    
    # Analizar estructura
    df = analyze_excel_with_headers(file_path)
    
    if df is None:
        print("No se pudo analizar la estructura del archivo")
        return
    
    # Analizar campos específicos
    compras_fields = analyze_specific_columns(df)
    
    # Crear mapeo de muestra
    create_sample_mapping(df, compras_fields)
    
    print(f"\n" + "="*60)
    print("ANALISIS COMPLETADO")
    print("="*60)
    print("Archivos generados:")
    print("1. immermex_compras_mapping.py - Mapeo de columnas")
    print("\nPróximos pasos:")
    print("1. Revisa el archivo de mapeo generado")
    print("2. Completa el mapeo manual para campos faltantes")
    print("3. Actualiza el servicio de importación")
    print("4. Prueba con datos reales")

if __name__ == "__main__":
    main()
