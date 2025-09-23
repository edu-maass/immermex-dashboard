# 🚀 Guía de Despliegue en Producción

## Configuración de Supabase

### 1. Variables de Entorno en Vercel

Configura las siguientes variables de entorno en tu proyecto de Vercel:

```bash
DATABASE_URL=postgresql://postgres.ldxahcawfrvlmdiwapli:[TU_PASSWORD]@aws-1-us-west-1.pooler.supabase.com:6543/postgres
ENVIRONMENT=production
DEBUG=false
LOG_LEVEL=info
```

### 2. Migración de Base de Datos

Ejecuta la migración en producción:

```bash
# Localmente (para migrar)
python migrate_production.py

# O directamente en Supabase (recomendado)
# Ve a tu dashboard de Supabase > SQL Editor
# Ejecuta el script de creación de tablas
```

### 3. Despliegue del Backend

```bash
# Instalar Vercel CLI
npm i -g vercel

# Login en Vercel
vercel login

# Desplegar backend
cd backend
vercel --prod

# Configurar variables de entorno
vercel env add DATABASE_URL
vercel env add ENVIRONMENT
```

### 4. Despliegue del Frontend

```bash
# En el directorio frontend
npm run build
npm run deploy
```

## Estructura de URLs en Producción

- **Frontend**: `https://immermex-dashboard.vercel.app`
- **Backend**: `https://immermex-dashboard.vercel.app/api`
- **Base de Datos**: Supabase PostgreSQL

## Verificación Post-Despliegue

1. **Health Check**: `GET https://immermex-dashboard.vercel.app/api/health`
2. **Data Summary**: `GET https://immermex-dashboard.vercel.app/api/data/summary`
3. **Upload Test**: Subir un archivo Excel desde el frontend

## Troubleshooting

### Error de Conexión a Base de Datos
- Verificar que `DATABASE_URL` esté configurada correctamente
- Verificar que el pooler de Supabase esté activo
- Revisar logs en Vercel: `vercel logs`

### Error de CORS
- Verificar que los orígenes estén configurados en `main_with_db.py`
- Verificar que `ENVIRONMENT=production` esté configurado

### Error de Upload
- Verificar que el archivo sea menor a 10MB
- Verificar que sea un archivo Excel válido
- Revisar logs de procesamiento en Vercel

## Monitoreo

- **Vercel Analytics**: Monitorear rendimiento del backend
- **Supabase Dashboard**: Monitorear uso de base de datos
- **Logs**: `vercel logs --follow` para logs en tiempo real
