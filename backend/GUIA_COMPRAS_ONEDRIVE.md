# Guía Completa: Integración de Compras con Microsoft OneDrive y Supabase

## Resumen

Esta guía te ayudará a configurar una tabla de compras en Supabase con actualización automática desde Microsoft OneDrive. El sistema incluye:

- ✅ Tabla de compras en Supabase con campos completos
- ✅ Integración con Microsoft OneDrive API
- ✅ Importación automática de archivos Excel
- ✅ Sincronización programada
- ✅ API endpoints para consultar datos
- ✅ Análisis y reportes de compras

## Archivos Creados

### Servicios Principales
- `backend/services/onedrive_service.py` - Servicio de conexión con OneDrive
- `backend/services/compras_import_service.py` - Servicio de importación de compras
- `backend/services/compras_api.py` - API endpoints para compras

### Scripts de Configuración
- `backend/get_onedrive_token.py` - Obtener tokens de OneDrive
- `backend/create_compras_table.py` - Crear tabla en Supabase
- `backend/compras_sync_manager.py` - Gestor de sincronización automática

### Base de Datos
- `backend/create_compras_table.sql` - SQL para crear tabla de compras

## Paso 1: Configurar Microsoft OneDrive API

### 1.1 Registrar Aplicación en Azure Portal

1. Ve a [Azure Portal](https://portal.azure.com)
2. Busca "Azure Active Directory" > "App registrations"
3. Haz clic en "New registration"
4. Configura:
   - **Name**: "Immermex OneDrive Integration"
   - **Supported account types**: "Accounts in this organizational directory only"
   - **Redirect URI**: "http://localhost:8080/auth/callback"

### 1.2 Configurar Permisos

1. En tu aplicación, ve a "API permissions"
2. Haz clic en "Add a permission"
3. Selecciona "Microsoft Graph"
4. Selecciona "Delegated permissions"
5. Agrega estos permisos:
   - `Files.Read`
   - `Files.ReadWrite`
   - `User.Read`

### 1.3 Generar Client Secret

1. Ve a "Certificates & secrets"
2. Haz clic en "New client secret"
3. Copia el valor del secret (solo se muestra una vez)

### 1.4 Obtener Credenciales

Ejecuta el script para obtener el refresh token:

```bash
cd backend
python get_onedrive_token.py
```

Sigue las instrucciones para autorizar la aplicación y obtener el refresh token.

## Paso 2: Configurar Variables de Entorno

Agrega estas variables a tu archivo `.env`:

```env
# Configuración de Microsoft OneDrive
ONEDRIVE_CLIENT_ID=tu_client_id_aqui
ONEDRIVE_CLIENT_SECRET=tu_client_secret_aqui
ONEDRIVE_TENANT_ID=tu_tenant_id_aqui
ONEDRIVE_REFRESH_TOKEN=tu_refresh_token_aqui
ONEDRIVE_COMPRAS_FOLDER=/Compras
ONEDRIVE_SYNC_INTERVAL=3600
```

## Paso 3: Crear Tabla en Supabase

Ejecuta el script para crear la tabla de compras:

```bash
cd backend
python create_compras_table.py
```

Este script creará:
- Tabla `compras` con todos los campos necesarios
- Tabla `categorias_compras` con categorías básicas
- Índices para optimizar consultas
- Triggers para calcular estado de pago automáticamente
- Vistas para resúmenes y reportes

## Paso 4: Preparar Archivos en OneDrive

### 4.1 Crear Carpeta de Compras

1. Ve a tu OneDrive
2. Crea una carpeta llamada "Compras"
3. Sube tus archivos Excel de compras allí

### 4.2 Formato de Archivos Excel

Los archivos deben tener columnas con estos nombres (o similares):

| Campo Requerido | Nombres Alternativos |
|----------------|---------------------|
| fecha_compra | fecha, fecha_factura, date |
| proveedor | supplier, vendor, cliente |
| total | importe_total, amount |
| numero_factura | factura, folio, invoice |
| concepto | descripcion, description, detalle |
| categoria | category, tipo, clasificacion |
| cantidad | quantity, qty, unidades |
| precio_unitario | unit_price, precio, costo_unitario |
| subtotal | sub_total, importe_sin_iva |
| iva | tax, impuesto |
| forma_pago | payment_method, metodo_pago |
| dias_credito | credit_days, dias |

## Paso 5: Probar la Integración

### 5.1 Probar Conexiones

```bash
cd backend
python compras_sync_manager.py --test
```

### 5.2 Ejecutar Primera Sincronización

```bash
cd backend
python compras_sync_manager.py --setup
```

### 5.3 Sincronización Manual

```bash
cd backend
python compras_sync_manager.py --sync
```

## Paso 6: Configurar Sincronización Automática

### 6.1 Como Daemon (Recomendado)

```bash
cd backend
python compras_sync_manager.py --daemon
```

### 6.2 Con Cron (Linux/Mac)

Agrega esta línea a tu crontab:

```bash
# Sincronizar cada hora
0 * * * * cd /path/to/backend && python compras_sync_manager.py --sync

# Sincronizar cada día a las 8:00 AM
0 8 * * * cd /path/to/backend && python compras_sync_manager.py --sync
```

### 6.3 Con Task Scheduler (Windows)

1. Abre Task Scheduler
2. Crea una nueva tarea
3. Configura para ejecutar cada hora:
   - Programa: `python`
   - Argumentos: `compras_sync_manager.py --sync`
   - Directorio: `C:\path\to\backend`

## Paso 7: Usar la API

### 7.1 Endpoints Disponibles

- `GET /api/compras/` - Lista de compras con filtros
- `GET /api/compras/summary` - Resumen de compras
- `GET /api/compras/proveedores` - Lista de proveedores
- `GET /api/compras/categorias` - Lista de categorías
- `POST /api/compras/import/onedrive` - Importar desde OneDrive
- `POST /api/compras/sync/automatic` - Sincronización automática
- `GET /api/compras/aging` - Análisis de aging
- `GET /api/compras/monthly-trend` - Tendencia mensual
- `GET /api/compras/top-proveedores` - Top proveedores
- `GET /api/compras/status` - Estado de importaciones

### 7.2 Ejemplos de Uso

```bash
# Obtener compras del mes actual
curl "http://localhost:8000/api/compras/?mes=12&año=2024"

# Obtener resumen de compras
curl "http://localhost:8000/api/compras/summary"

# Importar desde OneDrive
curl -X POST "http://localhost:8000/api/compras/import/onedrive"

# Obtener top 5 proveedores
curl "http://localhost:8000/api/compras/top-proveedores?limit=5"
```

## Paso 8: Monitoreo y Logs

### 8.1 Logs del Sistema

Los logs se guardan en:
- `backend/compras_sync.log` - Logs de sincronización
- `backend/immermex_dashboard.log` - Logs generales de la aplicación

### 8.2 Verificar Estado

```bash
# Ver estado de importaciones
curl "http://localhost:8000/api/compras/status"

# Verificar conexiones
python compras_sync_manager.py --test
```

## Estructura de la Tabla de Compras

```sql
CREATE TABLE compras (
    id SERIAL PRIMARY KEY,
    fecha_compra DATE,
    numero_factura VARCHAR(100),
    proveedor VARCHAR(255),
    concepto VARCHAR(500),
    categoria VARCHAR(100),
    subcategoria VARCHAR(100),
    cantidad DECIMAL(15,4) DEFAULT 0,
    unidad VARCHAR(50),
    precio_unitario DECIMAL(15,4) DEFAULT 0,
    subtotal DECIMAL(15,2) DEFAULT 0,
    iva DECIMAL(15,2) DEFAULT 0,
    total DECIMAL(15,2) DEFAULT 0,
    moneda VARCHAR(10) DEFAULT 'MXN',
    tipo_cambio DECIMAL(10,4) DEFAULT 1.0,
    forma_pago VARCHAR(100),
    dias_credito INTEGER DEFAULT 0,
    fecha_vencimiento DATE,
    fecha_pago DATE,
    estado_pago VARCHAR(50) DEFAULT 'pendiente',
    centro_costo VARCHAR(100),
    proyecto VARCHAR(100),
    notas TEXT,
    archivo_origen VARCHAR(255),
    archivo_id INTEGER REFERENCES archivos_procesados(id),
    mes INTEGER,
    año INTEGER,
    created_at TIMESTAMP WITH TIME ZONE DEFAULT CURRENT_TIMESTAMP,
    updated_at TIMESTAMP WITH TIME ZONE DEFAULT CURRENT_TIMESTAMP
);
```

## Solución de Problemas

### Error de Conexión con OneDrive

1. Verifica que las credenciales estén correctas
2. Asegúrate de que el refresh token no haya expirado
3. Verifica que la aplicación tenga los permisos necesarios

### Error de Conexión con Supabase

1. Verifica la URL de conexión en `DATABASE_URL`
2. Asegúrate de que la tabla se haya creado correctamente
3. Verifica que tengas permisos de escritura

### Archivos No Se Procesan

1. Verifica que los archivos estén en la carpeta correcta
2. Asegúrate de que los archivos tengan el formato correcto
3. Revisa los logs para ver errores específicos

### Sincronización No Funciona

1. Verifica que el daemon esté ejecutándose
2. Revisa la configuración de cron/task scheduler
3. Verifica los logs de sincronización

## Próximos Pasos

1. **Integrar con Frontend**: Crear componentes React para mostrar las compras
2. **Reportes Avanzados**: Implementar dashboards específicos para compras
3. **Notificaciones**: Configurar alertas para compras vencidas
4. **Aprobaciones**: Implementar flujo de aprobación de compras
5. **Presupuestos**: Integrar con sistema de presupuestos

## Soporte

Si encuentras problemas:

1. Revisa los logs en `backend/compras_sync.log`
2. Verifica la configuración de variables de entorno
3. Ejecuta las pruebas de conexión
4. Consulta la documentación de Microsoft Graph API

¡Tu sistema de compras con OneDrive está listo para usar! 🎉
