# 🛒 Sistema de Carga Manual de Compras - Immermex Dashboard

## ✅ Implementación Completada

Se ha implementado exitosamente un sistema completo para la carga manual de datos de compras en el Dashboard Immermex. El sistema incluye:

### 🎯 Funcionalidades Implementadas

1. **Interfaz Dual de Carga**
   - Sección izquierda: Facturación y Cobranza (existente)
   - Sección derecha: Compras e Importaciones (nueva)
   - Diseño responsivo y intuitivo

2. **Procesador Específico de Compras**
   - Manejo de la estructura específica del archivo "Resumen Compras"
   - Mapeo automático de columnas del Excel a la base de datos
   - Procesamiento de fechas, valores numéricos y estados de pago
   - Validación de datos específica para compras

3. **Endpoint API Dedicado**
   - `/api/upload/compras` - Endpoint específico para archivos de compras
   - Procesamiento independiente de datos de compras
   - Integración con el sistema de persistencia existente

4. **Base de Datos Extendida**
   - Tabla `compras` con campos específicos para importaciones
   - Índices optimizados para consultas eficientes
   - Triggers automáticos para timestamps

## 📁 Archivos Creados/Modificados

### Frontend
- `frontend/src/components/ComprasUpload.tsx` - Componente específico para carga de compras
- `frontend/src/components/DualUpload.tsx` - Componente que combina ambas secciones
- `frontend/src/services/api.ts` - Método `uploadComprasFile()` agregado
- `frontend/src/components/MainDashboard.tsx` - Integración del nuevo componente

### Backend
- `backend/compras_processor.py` - Procesador específico para archivos de compras
- `backend/main_with_db.py` - Endpoint `/api/upload/compras` agregado
- `backend/database_service_refactored.py` - Método `_save_compras()` agregado
- `backend/create_compras_table.sql` - Script SQL para crear la tabla de compras
- `backend/test_compras_functionality.py` - Script de pruebas (todas pasaron ✅)

## 🚀 Instrucciones de Uso

### 1. Configurar Base de Datos
```sql
-- Ejecutar en Supabase SQL Editor
-- El archivo create_compras_table.sql contiene el script completo
```

### 2. Iniciar el Sistema
```bash
# Backend
cd backend
python main_with_db.py

# Frontend (en otra terminal)
cd frontend
npm run dev
```

### 3. Usar la Interfaz
1. Acceder a la aplicación web
2. Ir a la pestaña "Carga de Archivos"
3. Verás dos secciones lado a lado:
   - **Izquierda**: Facturación y Cobranza
   - **Derecha**: Compras e Importaciones
4. Arrastra tu archivo Excel de compras en la sección derecha
5. El sistema procesará automáticamente los datos

## 📊 Estructura de Datos Esperada

El sistema espera un archivo Excel con una pestaña llamada **"Resumen Compras"** que contenga las siguientes columnas:

### Columnas Principales
- `IMI` - Identificador del material
- `Proveedor` - Nombre del proveedor
- `Material` - Descripción del material
- `fac prov` - Número de factura del proveedor
- `Kilogramos` - Cantidad en kilogramos
- `PU` - Precio unitario
- `DIVISA` - Moneda (USD, MXN, etc.)
- `Fecha Pedido` - Fecha de la compra

### Columnas de Importación
- `Puerto Origen` - Puerto de origen
- `Fecha Salida Puerto Origen (ETD/BL)` - Fecha de salida
- `FECHA ARRIBO A PUERTO (ETA)` - Fecha de arribo
- `FECHA ENTRADA IMMERMEX` - Fecha de entrada
- `PRECIO DLLS` - Precio en dólares
- `XR` - Tipo de cambio
- `Pedimento` - Número de pedimento
- `Gastos aduanales` - Gastos de importación
- `Agente` - Agente aduanal

## 🔧 Características Técnicas

### Procesamiento Inteligente
- **Detección automática de encabezados**: Encuentra la fila correcta aunque no esté en la primera fila
- **Mapeo flexible**: Maneja variaciones en nombres de columnas
- **Validación robusta**: Verifica datos requeridos antes de guardar
- **Manejo de errores**: Continúa procesando aunque algunos registros fallen

### Estados de Pago Automáticos
- **Pagado**: Si tiene fecha de pago
- **Vencido**: Si la fecha de vencimiento ya pasó
- **Pendiente**: Si no tiene fecha de pago ni está vencido

### Campos Calculados
- **Mes y Año**: Extraídos automáticamente de la fecha de compra
- **Subtotal**: Cantidad × Precio unitario
- **Total**: Usa costo_total si está disponible
- **Categoría**: Automáticamente marcada como "Importación"

## 📈 KPIs Generados

El sistema genera automáticamente KPIs específicos de compras:
- Total de compras procesadas
- Número de proveedores únicos
- Total de kilogramos importados
- Costo total en USD y MXN
- Distribución por estado de pago
- Estadísticas de importación

## 🛡️ Validaciones de Seguridad

- **Tamaño de archivo**: Máximo 10MB
- **Tipos de archivo**: Solo .xlsx y .xls
- **Validación de datos**: Campos requeridos verificados
- **Sanitización**: Datos limpios antes de guardar
- **Manejo de errores**: Logs detallados para debugging

## 🔄 Flujo de Datos

1. **Usuario sube archivo** → Frontend valida tipo y tamaño
2. **Frontend envía a API** → `/api/upload/compras`
3. **Backend procesa** → `compras_processor.py` limpia y mapea datos
4. **Base de datos** → `DatabaseService._save_compras()` guarda registros
5. **Respuesta** → Frontend muestra resultados y KPIs

## 🎉 Estado del Proyecto

**✅ COMPLETADO** - Todas las pruebas pasaron exitosamente:
- ✅ Procesador de compras funcionando
- ✅ Servicio de base de datos extendido
- ✅ Endpoint API implementado
- ✅ Componentes frontend creados
- ✅ Integración completa verificada

El sistema está listo para uso en producción. Solo falta ejecutar el script SQL en Supabase para crear la tabla de compras.
