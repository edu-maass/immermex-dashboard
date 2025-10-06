import pandas as pd
import io

# Crear datos de prueba para compras_v2
compras_data = {
    'imi': [9991, 9992, 9993],
    'proveedor': ['HONGKONG', 'PEREZ TRADING', 'COSMO'],
    'fecha_pedido': ['2024-12-01', '2024-12-02', '2024-12-03'],
    'moneda': ['USD', 'USD', 'USD'],
    'dias_credito': [30, 45, 30],
    'anticipo_pct': [10.0, 15.0, 5.0],
    'anticipo_monto': [1000.0, 1500.0, 500.0],
    'fecha_anticipo': ['2024-11-25', '2024-11-26', '2024-11-27'],
    'fecha_pago_factura': ['2024-12-31', '2025-01-15', '2025-01-02'],
    'tipo_cambio_estimado': [20.0, 20.5, 20.2],
    'tipo_cambio_real': [20.1, 20.6, 20.3],
    'gastos_importacion_divisa': [100.0, 150.0, 75.0],
    'porcentaje_gastos_importacion': [5.0, 7.5, 3.0],
    'iva_monto_divisa': [200.0, 300.0, 150.0],
    'total_con_iva_divisa': [2200.0, 3300.0, 1650.0]
}

materiales_data = {
    'imi': [9991, 9991, 9992, 9992, 9993],
    'material_codigo': ['TEST001', 'TEST002', 'TEST003', 'TEST004', 'TEST005'],
    'kg': [100.0, 150.0, 200.0, 100.0, 250.0],
    'pu_divisa': [10.0, 12.0, 15.0, 8.0, 6.0],
    'pu_mxn': [200.0, 240.0, 300.0, 160.0, 120.0],
    'costo_total_divisa': [1000.0, 1800.0, 3000.0, 800.0, 1500.0],
    'costo_total_mxn': [20000.0, 36000.0, 60000.0, 16000.0, 30000.0],
    'iva': [160.0, 288.0, 480.0, 128.0, 240.0]
}

# Crear DataFrames
compras_df = pd.DataFrame(compras_data)
materiales_df = pd.DataFrame(materiales_data)

# Crear archivo Excel en memoria
excel_buffer = io.BytesIO()
with pd.ExcelWriter(excel_buffer, engine='openpyxl') as writer:
    compras_df.to_excel(writer, sheet_name='Compras Generales', index=False)
    materiales_df.to_excel(writer, sheet_name='Materiales Detalle', index=False)

excel_buffer.seek(0)
file_content = excel_buffer.getvalue()

# Guardar archivo de prueba
with open('test_compras_v2_production.xlsx', 'wb') as f:
    f.write(file_content)

print("Archivo de prueba creado: test_compras_v2_production.xlsx")
print(f"Tamaño del archivo: {len(file_content)} bytes")
print("Datos incluidos:")
print(f"- Compras: {len(compras_df)} registros")
print(f"- Materiales: {len(materiales_df)} registros")
