# 📊 Procesador de Excel Avanzado Immermex v2.0.0

## Descripción General

El `excel_processor.py` es un módulo especializado y avanzado para procesar archivos Excel mensuales de Immermex. Proporciona limpieza automática de datos, normalización de columnas, cálculo de relaciones entre tablas y persistencia automática en PostgreSQL.

## 🎯 Características Principales Avanzadas

### ✅ Detección Automática Inteligente de Encabezados
- Busca dinámicamente la fila de encabezados en cada hoja usando algoritmos inteligentes
- Utiliza palabras clave específicas y patrones para cada tipo de datos
- Maneja variaciones complejas en el formato de archivos
- Detección de múltiples formatos de fecha y números
- Validación automática de estructura de datos

### ✅ Mapeo Flexible y Robusto de Columnas
- Mapeo inteligente de nombres de columnas variables con múltiples sinónimos
- Soporte para múltiples formatos de nomenclatura (español, inglés, abreviaciones)
- Normalización automática a nombres estándar con validación
- Detección automática de tipos de datos
- Manejo de columnas faltantes con valores por defecto

### ✅ Limpieza Robusta y Avanzada de Datos
- Normalización de fechas a formato YYYY-MM-DD con múltiples formatos de entrada
- Conversión automática de tipos numéricos con manejo de errores
- Limpieza avanzada de strings (espacios, mayúsculas/minúsculas, caracteres especiales)
- Validación y limpieza de UUIDs con verificación de formato
- Manejo de valores NaN, null, vacíos y errores de formato
- Sanitización de datos para prevenir inyección SQL

### ✅ Cálculo Avanzado de Relaciones
- Relaciona facturación con cobranza por UUID con validación de integridad
- Calcula días de cobro automáticamente con análisis de puntualidad
- Recalcula saldos pendientes con precisión decimal
- Identifica anticipos y notas de crédito con clasificación automática
- Cálculo de márgenes y rentabilidad por pedido
- Análisis de tendencias temporales

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

## 🚀 Uso Avanzado

### Función Principal con Persistencia
```python
from backend.excel_processor import load_and_clean_excel
from backend.database_service import DatabaseService

# Procesar archivo Excel con persistencia automática
data = load_and_clean_excel("ruta/al/archivo.xlsx")

# Los datos se almacenan automáticamente en PostgreSQL
# Acceder a los datos procesados
facturacion = data['facturacion_clean']
cobranza = data['cobranza_clean']
cfdi = data['cfdi_clean']
pedidos = data['pedidos_clean']

# Verificar persistencia
db_service = DatabaseService()
summary = db_service.get_data_summary()
print(f"Datos almacenados: {summary}")
```

### Uso con Clase Avanzada
```python
from backend.excel_processor import ImmermexExcelProcessor
from backend.database_service import DatabaseService

# Crear instancia con persistencia
processor = ImmermexExcelProcessor()
db_service = DatabaseService()

# Procesar archivo con almacenamiento automático
data = processor.load_and_clean_excel("archivo.xlsx")

# Los datos se guardan automáticamente en la BD
# Verificar datos persistentes
archivos = db_service.get_archivos_procesados()
print(f"Archivos procesados: {len(archivos)}")
```

### Procesamiento Individual con Validación
```python
# Procesar hojas individuales con validación avanzada
facturacion = processor.clean_facturacion("archivo.xlsx")
pedidos = processor.clean_pedidos("archivo.xlsx", "1-21 0925")

# Validar datos antes de persistir
if processor.validate_data_quality(facturacion):
    db_service.save_facturacion(facturacion)
else:
    print("Datos no válidos, revisar archivo")
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

## 🔄 Integración con Backend Avanzado

### Endpoint de Upload con Persistencia
```python
from backend.excel_processor import load_and_clean_excel
from backend.database_service import DatabaseService

@app.post("/api/upload")
async def upload_file(file: UploadFile = File(...)):
    # Procesar archivo con el procesador especializado
    data = load_and_clean_excel(file_path)
    
    # Persistir automáticamente en PostgreSQL
    db_service = DatabaseService()
    archivo_id = db_service.save_archivo_procesado(file.filename, len(data))
    
    # Usar datos procesados en KPIs
    kpis = db_service.calculate_kpis_from_persistent_data()
    return {
        "kpis": kpis,
        "archivo_id": archivo_id,
        "registros_procesados": len(data)
    }
```

### Cálculo de KPIs desde Datos Persistentes
```python
def calculate_kpis_from_persistent_data():
    db_service = DatabaseService()
    
    # Obtener datos desde PostgreSQL
    facturacion = db_service.get_facturacion_data()
    cobranza = db_service.get_cobranza_data()
    
    kpis = {
        'total_facturado': facturacion['monto_total'].sum(),
        'total_pendiente': facturacion['saldo_pendiente'].sum(),
        'num_facturas': len(facturacion),
        'promedio_factura': facturacion['monto_total'].mean(),
        'porcentaje_cobrado': calculate_cobranza_percentage(facturacion, cobranza),
        'aging_cartera': calculate_aging_from_persistent_data(facturacion)
    }
    
    return kpis
```

### Gestión de Archivos Procesados
```python
# Obtener historial de archivos
archivos = db_service.get_archivos_procesados(skip=0, limit=10)

# Eliminar archivo específico
db_service.delete_archivo(archivo_id)

# Verificar integridad de datos
integrity_check = db_service.verify_data_integrity()
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

*Procesador de Excel Avanzado Immermex v2.0.0 - Sistema robusto para procesamiento de datos financieros con persistencia completa*
