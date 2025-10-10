# 📊 Sistema Immermex Dashboard - Documentación Técnica Completa

## 🎯 Descripción General

El **Immermex Dashboard** es un sistema web completo para el análisis financiero y operativo de la empresa Immermex. Proporciona visualizaciones interactivas de KPIs, gráficos dinámicos, análisis de datos en tiempo real y persistencia completa de datos en la nube basados en archivos Excel mensuales.

## 🌐 Arquitectura del Sistema

### Frontend (React + TypeScript)
- **Framework**: React 19 con TypeScript
- **Build Tool**: Vite 7
- **Styling**: Tailwind CSS 3.4
- **Charts**: Recharts 3.2
- **Icons**: Lucide React 0.544
- **UI Components**: Radix UI primitives
- **Deployment**: GitHub Pages

### Backend (FastAPI + Python + PostgreSQL)
- **Framework**: FastAPI 0.104
- **Data Processing**: Pandas 2.1, NumPy 1.26
- **File Handling**: Excel (.xlsx, .xls) con OpenPyXL
- **Database**: PostgreSQL con SQLAlchemy 2.0
- **ORM**: SQLAlchemy con modelos relacionales
- **Authentication**: Python-JOSE para tokens
- **CORS**: Configurado dinámicamente según entorno
- **Deployment**: Render con auto-deploy desde GitHub
- **Logging**: Sistema estructurado con diferentes niveles

### Base de Datos (PostgreSQL/Supabase)
- **Provider**: Supabase PostgreSQL
- **ORM**: SQLAlchemy 2.0 con modelos declarativos
- **Migrations**: Scripts SQL automáticos
- **Indexing**: Índices optimizados para consultas rápidas
- **Backup**: Backup automático de Supabase
- **Scalability**: Pooler de conexiones para alta concurrencia

## 📁 Estructura del Proyecto

```
immermex-dashboard/
├── frontend/                    # Aplicación React
│   ├── src/
│   │   ├── components/         # Componentes React
│   │   │   ├── Charts/        # Gráficos especializados
│   │   │   ├── ui/            # Componentes UI base
│   │   │   ├── Dashboard.tsx  # Componente principal
│   │   │   ├── FileUpload.tsx # Subida de archivos
│   │   │   └── Filters.tsx    # Filtros dinámicos
│   │   ├── services/          # Servicios API
│   │   ├── types/             # Tipos TypeScript
│   │   └── App.tsx            # Punto de entrada
│   ├── package.json           # Dependencias Node.js
│   └── vite.config.ts         # Configuración Vite
├── backend/                    # API FastAPI
│   ├── simple_main.py         # Servidor principal
│   ├── data_processor.py      # Procesador de datos
│   ├── models.py              # Modelos Pydantic
│   ├── database.py            # Configuración BD
│   └── requirements.txt       # Dependencias Python
├── docs/                      # Documentación
└── README.md                  # Documentación principal
```

## 🔧 Funcionalidades Principales

### 1. **Dashboard de KPIs Avanzados**
- **Facturación Total**: Suma de todas las facturas del período con análisis detallado
- **Cobranza Total**: Total de cobros realizados con análisis de puntualidad
- **% Cobrado**: Porcentaje de cobranza sobre facturación con métricas de eficiencia
- **Anticipos**: Total de anticipos recibidos con análisis de impacto
- **Total Facturas**: Número de facturas emitidas con tendencias
- **Clientes Únicos**: Cantidad de clientes únicos con análisis de comportamiento
- **Rotación Inventario**: Veces que se rotó el inventario con métricas de eficiencia
- **Días CxC Ajustado**: Días promedio de cobro con análisis de aging
- **Ciclo de Efectivo**: Inventario + Cuentas por Cobrar con optimización
- **Análisis de Pedidos**: Métricas específicas por pedido con rentabilidad
- **Expectativa de Cobranza**: Proyecciones semanales vs realidad

### 2. **Gráficos Interactivos Avanzados**
- **Aging de Cartera**: Distribución por rangos de días (0-30, 31-60, 61-90, 90+) con análisis de tendencias
- **Top Clientes**: Ranking por facturación con métricas de rentabilidad
- **Consumo por Material**: Análisis de materiales por kg con proyecciones
- **Expectativa de Cobranza**: Comparación semanal entre cobranza esperada vs real
- **Análisis de Pedidos**: Gráficos específicos por pedido con rentabilidad
- **Tendencias Temporales**: Análisis de evolución en el tiempo

### 3. **Sistema de Persistencia Completo**
- **Almacenamiento Automático**: Todos los datos se guardan en PostgreSQL
- **Historial de Archivos**: Registro completo de archivos procesados
- **Gestión de Datos**: Capacidad de eliminar y gestionar datos históricos
- **Filtros Persistentes**: Los filtros se mantienen entre sesiones
- **Backup Automático**: Respaldo automático en Supabase
- **Escalabilidad**: Manejo de grandes volúmenes de datos

### 4. **Subida de Archivos Avanzada**
- **Formatos Soportados**: Excel (.xlsx, .xls) con validación automática
- **Procesamiento Inteligente**: Detección automática de encabezados y estructura
- **Validación Robusta**: Verificación de tamaño, formato y contenido
- **Hojas Procesadas**:
  - `facturacion`: Datos de facturación con análisis completo
  - `cobranza`: Datos de cobranza con cálculo de días de cobro
  - `cfdi relacionados`: Anticipos y notas de crédito filtrados
  - `1-14 sep` (o similar): Datos de pedidos por período con análisis de materiales
- **Persistencia Automática**: Los datos se almacenan automáticamente en la BD
- **Historial Completo**: Registro de todos los archivos procesados con metadatos

### 5. **Filtros Dinámicos Avanzados**
- **Por Fecha**: Rango de fechas personalizable con análisis temporal
- **Por Cliente**: Filtro específico de cliente con análisis individual
- **Por Agente**: Filtro por agente comercial con métricas de rendimiento
- **Por Material**: Filtro por tipo de material con análisis de consumo
- **Por Pedido**: Filtro específico por número de pedido
- **Por Mes/Año**: Filtros temporales con análisis de tendencias
- **Combinaciones**: Múltiples filtros simultáneos con análisis cruzado
- **Persistencia**: Los filtros se mantienen entre sesiones

## 🔄 Flujo de Procesamiento de Datos

### 1. **Carga de Archivo**
```mermaid
graph TD
    A[Usuario sube Excel] --> B[Validación formato]
    B --> C[Lectura de hojas]
    C --> D[Procesamiento por hoja]
    D --> E[Normalización datos]
    E --> F[Cálculo KPIs]
    F --> G[Actualización Dashboard]
```

### 2. **Procesamiento por Hoja**

#### **Hoja 'facturacion'**
- Mapeo de columnas a estructura estándar
- Normalización de fechas y importes
- Cálculo de campos derivados (mes, año)
- Limpieza de UUIDs y folios

#### **Hoja 'cobranza'**
- Relación con facturas por UUID/folio
- Agregación de importes por factura
- Cálculo de fechas de cobro

#### **Hoja 'cfdi relacionados'**
- Filtrado de anticipos
- Agregación por UUID de factura
- Cálculo de importes de anticipos

#### **Hoja de Pedidos (ej: '1-14 sep')**
- Procesamiento de datos de pedidos
- Cálculo de consumos por material
- Análisis de rentabilidad

### 3. **Cálculo de KPIs**

```python
# Ejemplo de cálculo de KPIs principales
facturacion_total = sum(facturas['monto_total'])
cobranza_total = sum(cobranzas_relacionadas['importe_pagado'])
porcentaje_cobrado = (cobranza_total / facturacion_total) * 100
aging_cartera = calcular_aging_por_dias(facturas_pendientes)
```

## 🌐 API Endpoints Completos

### **KPIs y Datos Principales**
- `GET /api/kpis` - Obtiene KPIs principales con filtros opcionales
- `GET /api/kpis/pedidos` - KPIs específicos por pedido
- `GET /api/health` - Verificación de salud del sistema
- `GET /api/data/summary` - Resumen de datos persistentes

### **Gráficos y Visualizaciones**
- `GET /api/graficos/aging` - Datos para gráfico de aging de cartera
- `GET /api/graficos/top-clientes` - Datos de top clientes por facturación
- `GET /api/graficos/consumo-material` - Datos de consumo por material
- `GET /api/graficos/expectativa-cobranza` - Datos de expectativa vs realidad

### **Gestión de Archivos**
- `POST /api/upload` - Subida de archivos Excel con procesamiento automático
- `GET /api/archivos` - Lista de archivos procesados con paginación
- `DELETE /api/archivos/{id}` - Eliminación de archivo específico
- `GET /api/archivos/{id}` - Detalles de archivo procesado

### **Análisis Detallado**
- `GET /api/analisis/pedidos` - Análisis completo de pedidos
- `GET /api/analisis/clientes` - Análisis detallado de clientes
- `GET /api/analisis/materiales` - Análisis de materiales y consumo
- `GET /api/pedido/{numero}` - Detalles específicos de un pedido
- `GET /api/cliente/{nombre}` - Detalles específicos de un cliente

### **Filtros y Búsquedas**
- `GET /api/filtros/clientes` - Lista de clientes disponibles
- `GET /api/filtros/materiales` - Lista de materiales disponibles
- `GET /api/filtros/pedidos` - Lista de pedidos disponibles
- `GET /api/filtros/disponibles` - Filtros disponibles para el período
- `POST /api/filtros/aplicar` - Aplicar filtros temporales
- `POST /api/filtros/pedidos/aplicar` - Aplicar filtros por pedidos

### **Gestión de Datos**
- `GET /api/data/status` - Estado actual de los datos
- `POST /api/data/refresh` - Refrescar cálculos de KPIs
- `DELETE /api/data/clear` - Limpiar todos los datos (con confirmación)

## 🚀 Despliegue y Configuración

### **Frontend (GitHub Pages)**
```bash
# URL de producción
https://edu-maass.github.io/immermex-dashboard/
```

### **Backend (Render)**
```bash
# URL de API
https://immermex-backend.onrender.com
# Documentación API
https://immermex-backend.onrender.com/docs
```

### **Variables de Entorno**
```env
# Frontend
VITE_API_URL=https://immermex-backend.onrender.com

# Backend (Render)
DATABASE_URL=postgresql://postgres:[PASSWORD]@aws-1-us-west-1.pooler.supabase.com:6543/postgres?sslmode=require
ENVIRONMENT=production
DEBUG=false
LOG_LEVEL=info

# Supabase
SUPABASE_URL=https://[PROJECT_ID].supabase.co
SUPABASE_ANON_KEY=[ANON_KEY]
SUPABASE_SERVICE_ROLE_KEY=[SERVICE_ROLE_KEY]
```

### **Configuración de Base de Datos**
```sql
-- Tablas principales
CREATE TABLE facturacion (...);
CREATE TABLE cobranza (...);
CREATE TABLE cfdi_relacionados (...);
CREATE TABLE pedidos (...);
CREATE TABLE archivos_procesados (...);

-- Índices optimizados
CREATE INDEX idx_facturacion_fecha ON facturacion(fecha_factura);
CREATE INDEX idx_facturacion_cliente ON facturacion(cliente);
CREATE INDEX idx_cobranza_uuid ON cobranza(uuid_factura_relacionada);
```

## 📊 Especificaciones de Datos

### **Formato de Archivo Excel Requerido**

El sistema espera un archivo Excel con las siguientes hojas:

1. **'facturacion'**
   - Fecha de factura
   - Serie factura
   - Folio factura
   - Cliente
   - Monto neto/total
   - Saldo pendiente
   - Días crédito
   - Agente
   - UUID factura

2. **'cobranza'**
   - Fecha de pago
   - Serie/Folio pago
   - Cliente
   - Importe pagado
   - UUID factura relacionada
   - Forma de pago

3. **'cfdi relacionados'**
   - UUID CFDI
   - Cliente receptor
   - Tipo relación
   - Importe relación
   - UUID factura relacionada

4. **Hoja de Pedidos (ej: '1-14 sep')**
   - Número de pedido
   - Cliente
   - Material
   - Kg
   - Precio unitario
   - Importe sin IVA
   - Días crédito
   - Fecha factura/pago

## 🔧 Configuración Técnica

### **Dependencias Frontend**
```json
{
  "react": "^19.1.1",
  "react-dom": "^19.1.1",
  "typescript": "~5.8.3",
  "vite": "^7.1.2",
  "tailwindcss": "^3.4.13",
  "recharts": "^3.2.1",
  "lucide-react": "^0.544.0",
  "@radix-ui/react-dialog": "^1.1.15",
  "@radix-ui/react-dropdown-menu": "^2.1.16",
  "@radix-ui/react-select": "^2.2.6",
  "@radix-ui/react-tabs": "^1.1.13",
  "react-dropzone": "^14.3.8"
}
```

### **Dependencias Backend**
```txt
fastapi==0.104.1
uvicorn[standard]==0.24.0
pandas==2.1.4
openpyxl==3.1.2
sqlalchemy==2.0.23
python-multipart==0.0.6
python-jose[cryptography]==3.3.0
passlib[bcrypt]==1.7.4
python-dotenv==1.0.0
pydantic==2.5.0
psycopg2-binary==2.9.9
numpy==1.26.4
python-dateutil==2.8.2
```

## 🛠️ Desarrollo y Mantenimiento

### **Agregar Nuevos KPIs**
1. Modificar `backend/database_service.py` en función `calculate_kpis()`
2. Actualizar `backend/main_with_db.py` para exponer el nuevo endpoint
3. Actualizar `frontend/src/types/index.ts` con nuevos tipos
4. Agregar componente en `frontend/src/components/KPICard.tsx`

### **Agregar Nuevos Gráficos**
1. Crear componente en `frontend/src/components/Charts/`
2. Agregar endpoint en `backend/main_with_db.py`
3. Integrar en `frontend/src/components/Dashboard.tsx`
4. Actualizar tipos en `frontend/src/types/index.ts`

### **Modificar Procesamiento de Datos**
1. Actualizar `backend/data_processor.py` para nuevos campos
2. Modificar `backend/excel_processor.py` para nuevos mapeos
3. Actualizar modelos en `backend/database.py` si es necesario
4. Ejecutar migración con `backend/migrate_to_supabase.py`

### **Agregar Nuevas Tablas**
1. Definir modelo en `backend/database.py`
2. Crear script de migración en `backend/create_tables_supabase.sql`
3. Ejecutar migración en Supabase
4. Actualizar `backend/database_service.py` para nuevas operaciones

## 📈 Métricas y Monitoreo

### **KPIs Calculados Automáticamente**
- Facturación total del período con análisis detallado
- Eficiencia de cobranza (% cobrado) con métricas de puntualidad
- Análisis de aging de cartera con distribución por rangos
- Rotación de inventarios con cálculos de eficiencia
- Consumo por material con análisis de tendencias
- Análisis de clientes top con métricas de rentabilidad
- Expectativa de cobranza con proyecciones semanales
- Análisis de pedidos con cálculo de márgenes
- Métricas de anticipos con impacto en flujo de efectivo

### **Validaciones de Datos Avanzadas**
- Formato de fechas consistente con múltiples formatos soportados
- Importes numéricos válidos con manejo de errores
- UUIDs únicos y válidos con validación de formato
- Relaciones entre facturas y cobranzas con integridad referencial
- Validación de archivos Excel con detección de estructura
- Verificación de completitud de datos críticos
- Análisis de calidad de datos con métricas de integridad

## 🔒 Seguridad y Rendimiento

### **Seguridad Avanzada**
- Validación de tipos de archivo con verificación de contenido
- Sanitización de datos de entrada con escape de caracteres especiales
- CORS configurado dinámicamente según entorno (desarrollo/producción)
- Manejo de errores robusto sin exposición de información sensible
- Autenticación con tokens JWT para endpoints sensibles
- Validación de tamaño de archivos (máximo 10MB)
- Logging de seguridad para auditoría y monitoreo
- Conexiones SSL obligatorias para base de datos

### **Rendimiento Optimizado**
- Procesamiento asíncrono de archivos con progress tracking
- Caché de datos en memoria con invalidación inteligente
- Optimización de consultas con índices específicos
- Compresión de respuestas HTTP con gzip
- Paginación en endpoints de listado para grandes volúmenes
- Pool de conexiones a base de datos para alta concurrencia
- Lazy loading de componentes en frontend
- Optimización de bundle con tree shaking

## 📞 Soporte y Contacto

Para soporte técnico o consultas sobre el sistema:
- **Desarrollador**: Eduardo Maass
- **Repositorio**: https://github.com/edu-maass/immermex-dashboard
- **Dashboard**: https://edu-maass.github.io/immermex-dashboard/

---

*Documentación generada automáticamente - Sistema Immermex Dashboard v2.0.0 con persistencia completa*
