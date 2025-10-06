import pandas as pd
import openpyxl
import re
import os

def create_clean_pedimentos_table(file_path):
    """Crea una tabla limpia con los datos de pedimentos usando el valor máximo entre B29 y B30"""
    
    try:
        # Cargar el archivo Excel
        workbook = openpyxl.load_workbook(file_path, data_only=True)
        
        # Lista para almacenar los datos extraídos
        pedimentos_data = []
        
        # Procesar cada pestaña
        for sheet_name in workbook.sheetnames:
            # Saltar pestañas que no son pedimentos
            if any(skip_word in sheet_name.upper() for skip_word in ['CONCENTRADO', 'RESUMEN', 'CALCULO', 'REPORTE', 'CALENDARIO', 'BD', 'PY', 'PAGOS', 'EDO', 'SHEET', 'HOJA', 'LISTA', 'PROYECCION']):
                continue
                
            sheet = workbook[sheet_name]
            
            # Extraer tipo de cambio de G7
            tipo_cambio = sheet['G7'].value
            
            # Extraer gastos aduanales usando el valor máximo entre B29 y B30
            gastos_b29 = sheet['B29'].value
            gastos_b30 = sheet['B30'].value
            
            # Calcular el valor máximo entre B29 y B30
            gastos_values = []
            if gastos_b29 is not None:
                try:
                    gastos_values.append(float(gastos_b29))
                except (ValueError, TypeError):
                    pass
            
            if gastos_b30 is not None:
                try:
                    gastos_values.append(float(gastos_b30))
                except (ValueError, TypeError):
                    pass
            
            # Usar el valor máximo si hay valores válidos
            if gastos_values:
                gastos_aduanales = max(gastos_values)
            else:
                gastos_aduanales = None
            
            # Extraer número de pedido del nombre de la pestaña
            pedido_match = re.search(r'(\d{4})$', sheet_name)
            if pedido_match:
                numero_pedido = pedido_match.group(1)
            else:
                numero_pedido = sheet_name[-4:] if len(sheet_name) >= 4 else sheet_name
            
            # Solo agregar si tiene datos válidos
            if tipo_cambio is not None or gastos_aduanales is not None:
                pedimentos_data.append({
                    'Pedido': numero_pedido,
                    'Tipo_Cambio': tipo_cambio if tipo_cambio is not None else "N/A",
                    'Gastos_Aduanales': gastos_aduanales if gastos_aduanales is not None else "N/A",
                    'B29_Original': gastos_b29 if gastos_b29 is not None else "N/A",
                    'B30_Original': gastos_b30 if gastos_b30 is not None else "N/A"
                })
        
        # Crear DataFrame
        df = pd.DataFrame(pedimentos_data)
        
        # Limpiar datos numéricos
        df['Tipo_Cambio'] = pd.to_numeric(df['Tipo_Cambio'], errors='coerce')
        df['Gastos_Aduanales'] = pd.to_numeric(df['Gastos_Aduanales'], errors='coerce')
        
        # Ordenar por número de pedido
        df = df.sort_values('Pedido')
        
        return df
        
    except Exception as e:
        print(f"Error al procesar el archivo: {str(e)}")
        return None

def main():
    file_path = "docs/IMM-Compras de  importacion (Compartido).xlsx"
    
    if not os.path.exists(file_path):
        print(f"Archivo no encontrado: {file_path}")
        return
    
    # Crear tabla limpia
    df = create_clean_pedimentos_table(file_path)
    
    if df is not None and not df.empty:
        print("=" * 100)
        print("TABLA DE PEDIMENTOS - TIPO DE CAMBIO Y GASTOS ADUANALES (VALOR MÁXIMO ENTRE B29 Y B30)")
        print("=" * 100)
        
        # Mostrar tabla con formato mejorado
        pd.set_option('display.max_rows', None)
        pd.set_option('display.max_columns', None)
        pd.set_option('display.width', None)
        pd.set_option('display.max_colwidth', None)
        
        # Formatear números para mostrar
        df_display = df.copy()
        df_display['Tipo_Cambio'] = df_display['Tipo_Cambio'].apply(lambda x: f"{x:.4f}" if pd.notna(x) else "N/A")
        df_display['Gastos_Aduanales'] = df_display['Gastos_Aduanales'].apply(lambda x: f"{x:,.2f}" if pd.notna(x) else "N/A")
        df_display['B29_Original'] = df_display['B29_Original'].apply(lambda x: f"{x:,.2f}" if isinstance(x, (int, float)) else str(x))
        df_display['B30_Original'] = df_display['B30_Original'].apply(lambda x: f"{x:,.2f}" if isinstance(x, (int, float)) else str(x))
        
        # Mostrar solo las columnas principales para la tabla principal
        print(df_display[['Pedido', 'Tipo_Cambio', 'Gastos_Aduanales']].to_string(index=False))
        
        print("\n" + "=" * 100)
        print("COMPARACIÓN DE VALORES B29 vs B30 (Solo pedimentos con diferencias)")
        print("=" * 100)
        
        # Mostrar casos donde B29 y B30 son diferentes
        df_comparison = df.copy()
        df_comparison['B29_Numeric'] = pd.to_numeric(df_comparison['B29_Original'], errors='coerce')
        df_comparison['B30_Numeric'] = pd.to_numeric(df_comparison['B30_Original'], errors='coerce')
        
        # Filtrar casos donde ambos valores existen y son diferentes
        different_values = df_comparison[
            (df_comparison['B29_Numeric'].notna()) & 
            (df_comparison['B30_Numeric'].notna()) & 
            (df_comparison['B29_Numeric'] != df_comparison['B30_Numeric'])
        ]
        
        if not different_values.empty:
            print("Pedido | B29 Original | B30 Original | Valor Usado (Máximo)")
            print("-" * 70)
            for _, row in different_values.iterrows():
                max_val = max(row['B29_Numeric'], row['B30_Numeric'])
                print(f"{row['Pedido']:>6} | {row['B29_Numeric']:>11,.2f} | {row['B30_Numeric']:>11,.2f} | {max_val:>18,.2f}")
        else:
            print("No se encontraron casos donde B29 y B30 tengan valores diferentes.")
        
        print("\n" + "=" * 100)
        print("RESUMEN ESTADÍSTICO")
        print("=" * 100)
        
        # Estadísticas de tipo de cambio
        tipos_cambio_validos = df['Tipo_Cambio'].dropna()
        if not tipos_cambio_validos.empty:
            print(f"Tipo de Cambio:")
            print(f"  • Promedio: {tipos_cambio_validos.mean():.4f}")
            print(f"  • Mínimo:   {tipos_cambio_validos.min():.4f}")
            print(f"  • Máximo:   {tipos_cambio_validos.max():.4f}")
            print(f"  • Total registros: {len(tipos_cambio_validos)}")
        
        # Estadísticas de gastos aduanales (usando valor máximo)
        gastos_validos = df['Gastos_Aduanales'].dropna()
        if not gastos_validos.empty:
            print(f"\nGastos Aduanales (Valor Máximo entre B29 y B30):")
            print(f"  • Promedio: ${gastos_validos.mean():,.2f}")
            print(f"  • Mínimo:   ${gastos_validos.min():,.2f}")
            print(f"  • Máximo:   ${gastos_validos.max():,.2f}")
            print(f"  • Total registros: {len(gastos_validos)}")
        
        # Guardar tabla limpia
        output_file = "tabla_pedimentos_max_value.csv"
        df.to_csv(output_file, index=False, encoding='utf-8-sig')
        print(f"\nTabla guardada en: {output_file}")
        
    else:
        print("No se encontraron datos válidos para procesar.")

if __name__ == "__main__":
    main()
