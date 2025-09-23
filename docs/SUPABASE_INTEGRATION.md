# Integración con Supabase - Dashboard Immermex

Esta guía te ayudará a integrar tu dashboard con Supabase para tener persistencia de datos en la nube.

## 🚀 Pasos para la Integración

### 1. Configurar Supabase

1. **Accede a tu proyecto en Supabase**: https://supabase.com/dashboard
2. **Ve a Settings > Database**
3. **Copia la información de conexión**:
   - Host
   - Database name (usualmente `postgres`)
   - Port (usualmente `5432`)
   - User (usualmente `postgres`)
   - Password

### 2. Configurar Variables de Entorno

#### Para Desarrollo Local:

Crea un archivo `.env` en la carpeta `backend/` con el siguiente contenido:

```bash
# Configuración de Supabase
DATABASE_URL=postgresql://postgres:[TU_PASSWORD]@db.[TU_PROJECT_ID].supabase.co:5432/postgres

# Ejemplo real:
# DATABASE_URL=postgresql://postgres:mi_password123@db.abcdefghijk.supabase.co:5432/postgres
```

#### Para Vercel (Producción):

1. **En tu dashboard de Vercel**:
   - Ve a tu proyecto
   - Settings > Environment Variables
   - Agrega: `DATABASE_URL` con tu cadena de conexión de Supabase

### 3. Ejecutar Migración

```bash
# Instalar dependencias
cd backend
pip install -r requirements.txt

# Ejecutar migración
python migrate_to_supabase.py
```

### 4. Probar la Conexión

```bash
# Ejecutar el servidor con base de datos
python main_with_db.py
```

## 🔧 Estructura de la Base de Datos

El sistema creará automáticamente las siguientes tablas:

- **`facturacion`**: Datos de facturas procesadas
- **`cobranza`**: Datos de cobros y pagos
- **`cfdi_relacionados`**: Anticipos y notas de crédito
- **`pedidos`**: Información de pedidos y materiales
- **`archivos_procesados`**: Registro de archivos subidos
- **`kpis`**: KPIs calculados (opcional)

## 🌐 Despliegue en Vercel

### 1. Actualizar vercel.json

Reemplaza tu `vercel.json` actual con `vercel_with_db.json`:

```bash
cp backend/vercel_with_db.json vercel.json
```

### 2. Configurar Variables en Vercel

1. Ve a tu proyecto en Vercel
2. Settings > Environment Variables
3. Agrega `DATABASE_URL` con tu conexión de Supabase

### 3. Redesplegar

```bash
vercel --prod
```

## ✅ Verificación

### Endpoints de Verificación

- **Health Check**: `GET /api/health`
  - Verifica conexión a base de datos
  - Muestra estado de datos disponibles

- **Data Summary**: `GET /api/data/summary`
  - Resumen de datos persistentes
  - Información del último archivo procesado

### Logs de Verificación

Al iniciar el servidor, deberías ver:

```
🌐 Conectando a Supabase/PostgreSQL en la nube
✅ API con base de datos iniciada correctamente
✅ Conexión a base de datos verificada
```

## 🔄 Flujo de Datos

1. **Subida de Archivo**: Los datos se procesan y guardan en Supabase
2. **Cambio de Pestañas**: Los datos se recuperan desde Supabase
3. **Recarga de Página**: Los datos persisten y se muestran automáticamente
4. **Filtros**: Se aplican sobre los datos persistentes

## 🛠️ Solución de Problemas

### Error de Conexión

```bash
❌ Error conectando a Supabase: connection refused
```

**Solución**: Verifica que:
- La `DATABASE_URL` esté correcta
- El proyecto de Supabase esté activo
- La contraseña sea correcta

### Error SSL

```bash
❌ Error: SSL connection required
```

**Solución**: Asegúrate de que tu `DATABASE_URL` incluya `?sslmode=require` o que el driver use SSL por defecto.

### Error de Tablas

```bash
❌ Error creando tablas: permission denied
```

**Solución**: Verifica que el usuario tenga permisos de CREATE TABLE en Supabase.

## 📊 Beneficios de Supabase

- ✅ **Persistencia**: Los datos se mantienen entre sesiones
- ✅ **Escalabilidad**: Maneja grandes volúmenes de datos
- ✅ **Backup Automático**: Supabase hace backups automáticos
- ✅ **Acceso Global**: Disponible desde cualquier lugar
- ✅ **Seguridad**: Conexiones SSL y autenticación robusta
- ✅ **Monitoreo**: Dashboard de Supabase para monitoreo

## 🔒 Seguridad

- Las credenciales se manejan via variables de entorno
- Conexiones SSL obligatorias
- No se almacenan credenciales en el código
- Supabase maneja la seguridad de la base de datos

## 📈 Próximos Pasos

1. **Monitoreo**: Usa el dashboard de Supabase para monitorear el rendimiento
2. **Backup**: Configura backups automáticos adicionales si es necesario
3. **Optimización**: Monitorea las consultas y optimiza índices según sea necesario
4. **Escalabilidad**: Considera actualizar el plan de Supabase si necesitas más recursos
