# 📊 Procesador de Excel Immermex

## Descripción General

El `excel_processor.py` es un módulo especializado para procesar archivos Excel mensuales de Immermex. Proporciona limpieza automática de datos, normalización de columnas y cálculo de relaciones entre tablas.

## 🎯 Características Principales

### ✅ Detección Automática de Encabezados
- Busca dinámicamente la fila de encabezados en cada hoja
- Utiliza palabras clave específicas para cada tipo de datos
- Maneja variaciones en el formato de archivos

### ✅ Mapeo Flexible de Columnas
- Mapeo inteligente de nombres de columnas variables
- Soporte para múltiples formatos de nomenclatura
- Normalización automática a nombres estándar

### ✅ Limpieza Robusta de Datos
- Normalización de fechas al formato YYYY-MM-DD
- Conversión automática de tipos numéricos
- Limpieza de strings (espacios, mayúsculas/minúsculas)
- Validación y limpieza de UUIDs

### ✅ Cálculo de Relaciones
- Relaciona facturación con cobranza por UUID
- Calcula días de cobro automáticamente
- Recalcula saldos pendientes
- Identifica anticipos y notas de crédito

## 📋 Estructura de Datos

### Facturación
```python
{
    'fecha_factura': datetime,
    'serie_factura': str,
    'folio_factura': str,
    'cliente': str,
    'monto_neto': float,
    'monto_total': float,
    'saldo_pendiente': float,
    'dias_credito': int,
    'agente': str,
    'uuid_factura': str
}
```

### Cobranza
```python
{
    'fecha_pago': datetime,
    'serie_pago': str,
    'folio_pago': str,
    'cliente': str,
    'moneda': str,
    'tipo_cambio': float,
    'forma_pago': str,
    'parcialidad': int,
    'importe_pagado': float,
    'uuid_factura_relacionada': str
}
```

### CFDI Relacionados
```python
{
    'xml': str,  # UUID del CFDI
    'cliente_receptor': str,
    'tipo_relacion': str,
    'importe_relacion': float,
    'uuid_factura_relacionada': str
}
```

### Pedidos
```python
{
    'folio_factura': str,
    'pedido': str,
    'kg': float,
    'precio_unitario': float,
    'importe_sin_iva': float,
    'material': str,
    'dias_credito': int,
    'fecha_factura': datetime,
    'fecha_pago': datetime
}
```

## 🚀 Uso Básico

### Función Principal
```python
from backend.excel_processor import load_and_clean_excel

# Procesar archivo Excel
data = load_and_clean_excel("ruta/al/archivo.xlsx")

# Acceder a los datos
facturacion = data['facturacion_clean']
cobranza = data['cobranza_clean']
cfdi = data['cfdi_clean']
pedidos = data['pedidos_clean']
```

### Uso con Clase
```python
from backend.excel_processor import ImmermexExcelProcessor

# Crear instancia
processor = ImmermexExcelProcessor()

# Procesar archivo
data = processor.load_and_clean_excel("archivo.xlsx")

# Procesar hojas individuales
facturacion = processor.clean_facturacion("archivo.xlsx")
pedidos = processor.clean_pedidos("archivo.xlsx", "1-21 0925")
```

## 🔧 Configuración Avanzada

### Detección de Encabezados
```python
# Palabras clave para detectar encabezados
keywords = ['fecha', 'cliente', 'monto', 'uuid']
header_row = processor.detect_header_row("archivo.xlsx", "facturacion", keywords)
```

### Mapeo Personalizado
El procesador incluye mapeos flexibles para diferentes formatos:

```python
# Ejemplo de mapeo para facturación
column_mapping = {
    'fecha': 'fecha_factura',
    'fecha de factura': 'fecha_factura',
    'razón social': 'cliente',
    'razon social': 'cliente',
    'neto': 'monto_neto',
    'total': 'monto_total',
    'pendiente': 'saldo_pendiente',
    'uuid': 'uuid_factura'
}
```

## 📊 Validaciones Implementadas

### Fechas
- Conversión automática a formato datetime
- Manejo de errores con `errors='coerce'`
- Validación de rangos de fechas

### Montos
- Conversión a float con manejo de errores
- Valores por defecto para datos faltantes
- Validación de valores numéricos

### UUIDs
- Limpieza de espacios y normalización a mayúsculas
- Validación de formato UUID estándar
- Eliminación de duplicados
- Filtrado de valores nulos o inválidos

### Strings
- Eliminación de espacios en blanco
- Normalización de espacios múltiples
- Limpieza de caracteres especiales

## 🛠️ Manejo de Errores

### Logging Detallado
```python
import logging

# El procesador incluye logging automático
logger = logging.getLogger(__name__)
logger.info("Procesando archivo Excel...")
logger.warning("Advertencia: Columna no encontrada")
logger.error("Error en procesamiento: {error}")
```

### Recuperación de Errores
- Datos por defecto para columnas faltantes
- Continuación del procesamiento ante errores individuales
- Retorno de DataFrames vacíos en caso de error crítico

## 📈 Métricas de Calidad

### Validaciones Automáticas
- Verificación de columnas requeridas
- Validación de tipos de datos
- Conteo de registros procesados
- Identificación de datos faltantes

### Reportes de Procesamiento
```python
# El procesador genera logs detallados
logger.info(f"Facturación: {len(df)} registros procesados")
logger.info(f"Rango de fechas: {fechas.min()} a {fechas.max()}")
logger.info(f"Total facturado: ${total:,.2f}")
```

## 🔄 Integración con Backend

### Endpoint de Upload
```python
from backend.excel_processor import load_and_clean_excel

@app.post("/api/upload")
async def upload_file(file: UploadFile = File(...)):
    # Procesar archivo con el procesador especializado
    data = load_and_clean_excel(file_path)
    
    # Usar datos procesados en KPIs
    kpis = calculate_kpis(data)
    return kpis
```

### Cálculo de KPIs
```python
def calculate_kpis_from_processed_data(data):
    facturacion = data['facturacion_clean']
    
    kpis = {
        'total_facturado': facturacion['monto_total'].sum(),
        'total_pendiente': facturacion['saldo_pendiente'].sum(),
        'num_facturas': len(facturacion),
        'promedio_factura': facturacion['monto_total'].mean()
    }
    
    return kpis
```

## 🧪 Pruebas y Validación

### Script de Prueba
```bash
# Ejecutar procesador con archivo de prueba
python backend/excel_processor.py archivo_prueba.xlsx
```

### Verificación de Estructura
```python
# Verificar que el procesador esté correctamente implementado
from backend.excel_processor import ImmermexExcelProcessor

processor = ImmermexExcelProcessor()
assert hasattr(processor, 'clean_facturacion')
assert hasattr(processor, 'clean_cobranza')
assert hasattr(processor, 'clean_cfdi')
assert hasattr(processor, 'clean_pedidos')
```

## 📝 Notas de Desarrollo

### Dependencias
- `pandas`: Manipulación de datos
- `numpy`: Operaciones numéricas
- `openpyxl`: Lectura de archivos Excel
- `datetime`: Manejo de fechas

### Rendimiento
- Procesamiento optimizado para archivos grandes
- Uso eficiente de memoria con DataFrames
- Logging estructurado para debugging

### Mantenimiento
- Código modular y bien documentado
- Fácil extensión para nuevos formatos
- Manejo robusto de errores
- Logging detallado para troubleshooting

---

*Procesador de Excel Immermex v1.0.0 - Sistema robusto para procesamiento de datos financieros*
