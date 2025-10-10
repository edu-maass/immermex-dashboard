# Guía de Deployment en Render

Esta guía te llevará paso a paso para migrar tu backend de FastAPI desde Vercel a Render.

## 📋 Requisitos Previos

- [ ] Cuenta en GitHub con tu repositorio
- [ ] Credenciales de Supabase (DATABASE_URL, SUPABASE_KEY, etc.)
- [ ] Cuenta en Render (crear en https://render.com)

## 🚀 Paso 1: Crear Cuenta en Render

1. Ve a https://render.com
2. Haz clic en **"Get Started"** o **"Sign Up"**
3. Registrate usando tu cuenta de GitHub (recomendado) o email
4. Autoriza a Render para acceder a tus repositorios de GitHub

## 📦 Paso 2: Crear un Nuevo Web Service

1. Una vez logueado, haz clic en **"New +"** en el dashboard
2. Selecciona **"Web Service"**
3. Conecta tu repositorio:
   - Si conectaste con GitHub, verás una lista de tus repos
   - Busca y selecciona: `Immermex` (o el nombre de tu repo)
   - Haz clic en **"Connect"**

## ⚙️ Paso 3: Configurar el Web Service

En la página de configuración, llena los siguientes campos:

### Configuración Básica:
- **Name**: `immermex-backend` (o el nombre que prefieras)
- **Region**: Selecciona la región más cercana (US West o US East)
- **Branch**: `main` (o tu rama principal)
- **Root Directory**: Déjalo vacío (usa la raíz del proyecto)
- **Runtime**: Selecciona **Python 3**

### Build & Deploy:
- **Build Command**: 
  ```bash
  pip install -r requirements.txt
  ```
- **Start Command**: 
  ```bash
  uvicorn main_with_db:app --host 0.0.0.0 --port $PORT
  ```

### Configuración de Plan:
- **Instance Type**: Selecciona **Free** (o el plan que prefieras)
  - ⚠️ El plan Free tiene limitaciones: se duerme después de 15 min de inactividad
  - Para producción, considera **Starter** ($7/mes) sin cold starts

## 🔐 Paso 4: Configurar Variables de Entorno

En la sección **"Environment Variables"**, agrega las siguientes variables (haz clic en "Add Environment Variable" para cada una):

```
ENVIRONMENT = production
DEBUG = false
LOG_LEVEL = info
DATABASE_URL = postgresql://postgres.ldxahcawfrvlmdiwapli:Database_Immermex@aws-1-us-west-1.pooler.supabase.com:6543/postgres?sslmode=require
SUPABASE_URL = https://ldxahcawfrvlmdiwapli.supabase.co
SUPABASE_KEY = [Tu SUPABASE_KEY aquí]
SUPABASE_SERVICE_ROLE_KEY = [Tu SUPABASE_SERVICE_ROLE_KEY aquí]
SUPABASE_PASSWORD = Database_Immermex
ALLOWED_ORIGINS = https://edu-maass.github.io,https://immermex-dashboard.vercel.app
PYTHON_VERSION = 3.11.0
```

### 📝 Cómo obtener las claves de Supabase:

1. Ve a tu proyecto en https://supabase.com
2. En el menú lateral, haz clic en **Settings** → **API**
3. Copia:
   - **SUPABASE_KEY**: Es el "anon public" key
   - **SUPABASE_SERVICE_ROLE_KEY**: Es el "service_role" key (mantén esto secreto)

## 🎬 Paso 5: Deploy Inicial

1. Revisa toda la configuración
2. Haz clic en **"Create Web Service"** al final de la página
3. Render comenzará a:
   - Clonar tu repositorio
   - Instalar dependencias (`pip install -r requirements.txt`)
   - Iniciar tu aplicación
   - Esto puede tardar 2-5 minutos

4. Monitorea el proceso en la pestaña **"Logs"**
   - Deberías ver mensajes de instalación de paquetes
   - Luego verás que Uvicorn inicia tu aplicación
   - Mensaje exitoso: `Application startup complete`

## 🔗 Paso 6: Obtener la URL de tu Backend

1. Una vez completado el deploy, verás tu URL en la parte superior:
   ```
   https://immermex-backend.onrender.com
   ```
2. **Copia esta URL** - la necesitarás para el frontend

3. Verifica que funciona visitando:
   ```
   https://immermex-backend.onrender.com/health
   ```
   Deberías ver un JSON con status "healthy"

## 🔄 Paso 7: Actualizar el Frontend

Ahora necesitas actualizar tu frontend para que use la nueva URL del backend:

### Opción A: Si tu frontend está en el mismo repo
1. Ve a `frontend/src/services/api.ts`
2. Actualiza la `baseURL`:
   ```typescript
   const API_BASE_URL = 'https://immermex-backend.onrender.com';
   ```

### Opción B: Si usas variables de entorno
1. Actualiza tu `.env` o configuración de Vercel/GitHub Pages
2. Cambia la variable `VITE_API_URL` o similar a:
   ```
   VITE_API_URL=https://immermex-backend.onrender.com
   ```

### Actualizar CORS si es necesario:
Si tu frontend está en una nueva URL, actualiza la variable `ALLOWED_ORIGINS` en Render:
1. Ve a tu servicio en Render
2. Haz clic en **"Environment"** en el menú lateral
3. Edita `ALLOWED_ORIGINS` para incluir tu URL del frontend
4. Guarda y el servicio se re-deployará automáticamente

## ✅ Paso 8: Verificar el Deployment

Prueba los siguientes endpoints para verificar que todo funciona:

1. **Health Check**:
   ```bash
   curl https://immermex-backend.onrender.com/health
   ```

2. **API Info**:
   ```bash
   curl https://immermex-backend.onrender.com/
   ```

3. **Desde tu frontend**:
   - Abre tu aplicación web
   - Verifica que los datos se cargan correctamente
   - Revisa la consola del navegador para errores

## 🔧 Configuración Avanzada (Opcional)

### Auto-Deploy desde GitHub
Ya está configurado por defecto. Cada vez que hagas push a `main`, Render automáticamente:
1. Detecta el cambio
2. Hace pull del código nuevo
3. Re-ejecuta el build
4. Despliega la nueva versión

### Health Check Personalizado
Render ya está configurado para revisar `/health` cada cierto tiempo. Si tu app no responde, Render intentará reiniciarla.

### Ver Logs en Tiempo Real
1. En Render dashboard, selecciona tu servicio
2. Haz clic en **"Logs"** en el menú lateral
3. Verás logs en tiempo real de tu aplicación

### Escalamiento (Para plan Starter o superior)
1. Ve a **"Settings"** en tu servicio
2. En **"Instance Type"**, puedes cambiar a instancias más potentes
3. En **"Scaling"**, puedes configurar auto-scaling

## 🚨 Troubleshooting

### Problema: "Application failed to start"
- **Solución**: Revisa los logs para ver el error específico
- Verifica que todas las variables de entorno estén configuradas
- Asegúrate que `requirements.txt` tiene todas las dependencias

### Problema: "Connection refused to database"
- **Solución**: Verifica tu `DATABASE_URL`
- Asegúrate que incluye `?sslmode=require`
- Revisa que Supabase permite conexiones desde Render

### Problema: CORS errors en el frontend
- **Solución**: Actualiza `ALLOWED_ORIGINS` en Render
- Incluye la URL exacta de tu frontend (con https://)
- Re-deploya el servicio después de cambiar variables

### Problema: App se duerme (solo plan Free)
- **Causa**: El plan Free duerme después de 15 min sin actividad
- **Solución**: 
  - Actualiza a plan Starter ($7/mes)
  - O acepta el "cold start" de ~30 segundos al despertar

## 💰 Costos

- **Free Tier**: $0/mes
  - 750 horas/mes gratis
  - Se duerme con inactividad
  - Bueno para testing

- **Starter**: $7/mes
  - Siempre activo (sin cold starts)
  - Más recursos
  - Recomendado para producción

## 🎉 ¡Listo!

Tu backend de FastAPI ahora está corriendo en Render. Beneficios vs Vercel:
- ✅ Mejor para aplicaciones Python persistentes
- ✅ Sin límites de tiempo de ejecución
- ✅ Mejor manejo de conexiones a base de datos
- ✅ Logs más completos
- ✅ Sin cold starts (en plan pago)

## 📞 Soporte

- Documentación de Render: https://render.com/docs
- Render Community: https://community.render.com
- FastAPI Docs: https://fastapi.tiangolo.com

---

**¿Necesitas ayuda?** Revisa los logs en Render o contacta a su soporte (muy responsivos).


