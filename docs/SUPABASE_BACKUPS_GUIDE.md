# Guía de Backups en Supabase para Immermex Dashboard

## 📋 Índice
1. [Backups Automáticos Incluidos](#backups-automáticos-incluidos)
2. [Cómo Restaurar un Backup](#cómo-restaurar-un-backup)
3. [Backups Manuales](#backups-manuales)
4. [Script de Backup Programado](#script-de-backup-programado)
5. [Mejores Prácticas](#mejores-prácticas)

---

## 🔄 Backups Automáticos Incluidos

### **Free Tier (Actual)**
✅ **Incluido sin costo adicional:**
- Backups diarios automáticos
- Retención: **7 días**
- Hora de backup: Configurada por Supabase (generalmente 00:00 UTC)

### **Pro Tier ($25/mes)**
Si necesitas más retención:
- Backups diarios por **30 días**
- Point-in-time recovery hasta **7 días**
- Backups bajo demanda ilimitados
- Restauración más rápida

---

## 🔙 Cómo Restaurar un Backup

### **Opción 1: Desde el Dashboard de Supabase (Recomendado)**

1. **Acceder al Dashboard**
   ```
   https://supabase.com/dashboard
   ```

2. **Seleccionar el Proyecto**
   - Click en tu proyecto "Immermex" o el nombre que tengas

3. **Ir a Backups**
   - En el menú lateral: **Database** → **Backups**

4. **Seleccionar el Backup**
   - Verás una lista de backups disponibles (últimos 7 días)
   - Busca el backup de **antes de las 04:03 UTC del 11-Oct-2025**
   - Ejemplo: "Backup del 10-Oct-2025 23:00 UTC"

5. **Restaurar**
   - Click en el botón **"Restore"** del backup deseado
   - Confirma la acción
   - ⏱️ Tiempo estimado: 5-15 minutos

6. **Verificar**
   ```sql
   -- Ejecutar en SQL Editor para verificar
   SELECT COUNT(*) FROM compras_v2;
   SELECT COUNT(*) FROM compras_v2_materiales;
   ```

---

### **Opción 2: Restaurar desde SQL Dump (Si tienes backup local)**

1. **Acceder al SQL Editor**
   - Dashboard → **SQL Editor** → **New Query**

2. **Ejecutar el SQL Dump**
   ```sql
   -- Limpiar tablas (si es necesario)
   TRUNCATE TABLE compras_v2_materiales CASCADE;
   TRUNCATE TABLE compras_v2 CASCADE;
   
   -- Luego pegar tu SQL dump aquí
   -- INSERT INTO compras_v2 (imi, proveedor, ...) VALUES ...
   ```

3. **Verificar Integridad**
   ```sql
   -- Verificar que las foreign keys estén bien
   SELECT c2.imi, COUNT(c2m.id) as materiales_count
   FROM compras_v2 c2
   LEFT JOIN compras_v2_materiales c2m ON c2.imi = c2m.compra_imi
   GROUP BY c2.imi
   LIMIT 10;
   ```

---

## 💾 Backups Manuales

### **Crear Backup Manual en Supabase**

1. **Desde el Dashboard**
   - Database → Backups → **"Create Backup Now"**
   - Útil antes de cambios importantes

### **Exportar Datos a CSV/SQL**

**Script Python para exportar:**

```python
# export_backup.py
import psycopg2
from psycopg2.extras import RealDictCursor
import csv
from datetime import datetime
import os

def export_table_to_csv(table_name, output_dir="backups"):
    """Exporta una tabla completa a CSV"""
    
    # Crear directorio de backups
    os.makedirs(output_dir, exist_ok=True)
    
    # Conectar a Supabase
    conn = psycopg2.connect(
        os.getenv("DATABASE_URL"),
        cursor_factory=RealDictCursor
    )
    
    cursor = conn.cursor()
    
    # Obtener todos los datos
    cursor.execute(f"SELECT * FROM {table_name}")
    rows = cursor.fetchall()
    
    if not rows:
        print(f"⚠️  Tabla {table_name} está vacía")
        return
    
    # Crear archivo con timestamp
    timestamp = datetime.now().strftime("%Y%m%d_%H%M%S")
    filename = f"{output_dir}/{table_name}_{timestamp}.csv"
    
    # Escribir CSV
    with open(filename, 'w', newline='', encoding='utf-8') as f:
        # Obtener nombres de columnas
        fieldnames = rows[0].keys()
        writer = csv.DictWriter(f, fieldnames=fieldnames)
        
        writer.writeheader()
        writer.writerows(rows)
    
    cursor.close()
    conn.close()
    
    print(f"✅ Exportado {len(rows)} registros de {table_name} a {filename}")

# Uso:
if __name__ == "__main__":
    export_table_to_csv("compras_v2")
    export_table_to_csv("compras_v2_materiales")
    export_table_to_csv("facturacion")
    export_table_to_csv("cobranza")
    export_table_to_csv("pedidos")
```

### **Ejecutar el Script**

```bash
# Configurar DATABASE_URL (obtener de Supabase Dashboard)
export DATABASE_URL="postgresql://postgres:[PASSWORD]@[HOST]/postgres"

# Ejecutar backup
python export_backup.py
```

Esto creará archivos CSV en la carpeta `backups/`:
- `compras_v2_20251011_120000.csv`
- `compras_v2_materiales_20251011_120000.csv`
- etc.

---

## 🤖 Script de Backup Programado

### **Opción A: GitHub Actions (Recomendado)**

Crea `.github/workflows/backup.yml`:

```yaml
name: Supabase Backup

on:
  schedule:
    # Ejecutar diariamente a las 02:00 UTC (después del backup de Supabase)
    - cron: '0 2 * * *'
  workflow_dispatch: # Permitir ejecución manual

jobs:
  backup:
    runs-on: ubuntu-latest
    
    steps:
      - name: Checkout código
        uses: actions/checkout@v3
      
      - name: Setup Python
        uses: actions/setup-python@v4
        with:
          python-version: '3.11'
      
      - name: Instalar dependencias
        run: |
          pip install psycopg2-binary pandas
      
      - name: Ejecutar backup
        env:
          DATABASE_URL: ${{ secrets.DATABASE_URL }}
        run: |
          python export_backup.py
      
      - name: Upload artifacts
        uses: actions/upload-artifact@v3
        with:
          name: supabase-backup
          path: backups/
          retention-days: 30
```

**Configurar en GitHub:**
1. Ve a tu repositorio en GitHub
2. Settings → Secrets and variables → Actions
3. New repository secret:
   - Name: `DATABASE_URL`
   - Value: Tu URL de Supabase (desde Dashboard → Settings → Database)

### **Opción B: Cron Job Local**

**Linux/Mac:**
```bash
# Editar crontab
crontab -e

# Agregar línea (ejecutar diariamente a las 2 AM)
0 2 * * * cd /path/to/immermex && /usr/bin/python3 export_backup.py
```

**Windows (Task Scheduler):**
1. Abrir "Task Scheduler"
2. Create Basic Task → "Supabase Backup Immermex"
3. Trigger: Daily, 2:00 AM
4. Action: Start a Program
   - Program: `python.exe`
   - Arguments: `export_backup.py`
   - Start in: `C:\path\to\immermex`

---

## 🛡️ Mejores Prácticas

### **1. Backups Antes de Cambios Mayores**

Crear backup manual antes de:
- Actualizar esquema de base de datos
- Migrar datos masivos
- Cambiar lógica de procesamiento

### **2. Verificar Backups Regularmente**

Script de verificación:

```python
# verify_backup.py
import os
from datetime import datetime, timedelta

def verify_recent_backup(backup_dir="backups", max_age_hours=26):
    """Verifica que exista un backup reciente"""
    
    if not os.path.exists(backup_dir):
        print("❌ No existe directorio de backups")
        return False
    
    files = os.listdir(backup_dir)
    csv_files = [f for f in files if f.endswith('.csv')]
    
    if not csv_files:
        print("❌ No hay archivos de backup")
        return False
    
    # Buscar el más reciente
    newest = max(csv_files, key=lambda f: os.path.getmtime(os.path.join(backup_dir, f)))
    newest_path = os.path.join(backup_dir, newest)
    mod_time = datetime.fromtimestamp(os.path.getmtime(newest_path))
    
    age_hours = (datetime.now() - mod_time).total_seconds() / 3600
    
    if age_hours > max_age_hours:
        print(f"⚠️  Backup más reciente tiene {age_hours:.1f} horas (máx: {max_age_hours})")
        return False
    
    print(f"✅ Backup reciente encontrado: {newest}")
    print(f"   Antigüedad: {age_hours:.1f} horas")
    return True

if __name__ == "__main__":
    verify_recent_backup()
```

### **3. Política de Retención Recomendada**

- **Diarios**: 7 días (incluido en Supabase Free)
- **Semanales**: 4 semanas (exportar manualmente cada lunes)
- **Mensuales**: 6 meses (exportar primer día de cada mes)
- **Anuales**: Indefinido (exportar 31-dic de cada año)

### **4. Múltiples Ubicaciones**

Guardar backups en al menos **2 ubicaciones**:

1. **Supabase** (automático)
2. **GitHub Actions Artifacts** (30 días)
3. **Local** (manual semanal)
4. **Cloud Storage** (opcional):
   - Google Drive
   - Dropbox
   - AWS S3
   - Azure Blob Storage

### **5. Documentar Backups**

Mantener log de backups:

```
backups/
├── backup_log.txt
├── compras_v2_20251011_020000.csv
├── compras_v2_materiales_20251011_020000.csv
└── ...
```

**backup_log.txt**:
```
2025-10-11 02:00:00 - Backup automático diario
  - compras_v2: 302 registros
  - compras_v2_materiales: 5 registros
  
2025-10-10 02:00:00 - Backup automático diario
  - compras_v2: 298 registros
  - compras_v2_materiales: 5 registros
```

---

## 🔧 Configuración Rápida

### **Paso 1: Habilitar Backups Diarios (Ya activo en Free Tier)**

Los backups diarios ya están activos. Solo verifica:
1. Dashboard → Database → Backups
2. Confirma que ves backups recientes

### **Paso 2: Crear Primer Backup Manual**

1. Dashboard → Database → Backups
2. Click **"Create Backup Now"**
3. Espera confirmación (1-2 minutos)

### **Paso 3: Configurar GitHub Actions (Opcional pero recomendado)**

1. Crea el archivo `.github/workflows/backup.yml` (ver arriba)
2. Agrega SECRET `DATABASE_URL` en GitHub
3. Ejecuta manualmente la primera vez:
   - Actions → Supabase Backup → Run workflow

### **Paso 4: Programar Script Local**

```bash
# Crear script ejecutable
chmod +x export_backup.py

# Probar manualmente
python export_backup.py

# Agregar a cron (Linux/Mac) o Task Scheduler (Windows)
```

---

## 📊 Monitoreo de Backups

### **Dashboard de Supabase**

Puedes ver:
- Fecha y hora de cada backup
- Tamaño del backup
- Estado (completado/fallido)
- Opción de restaurar

### **Alertas Recomendadas**

Configurar alertas si:
- No hay backup en últimas 26 horas
- Backup falla
- Tamaño del backup disminuye significativamente (posible pérdida de datos)

---

## 🚨 Plan de Recuperación ante Desastres

### **Escenario 1: Borrado Accidental (Como hoy)**

1. **Inmediato**: No hacer más cambios en la DB
2. **Restaurar**: Usar backup de Supabase del día anterior
3. **Re-cargar**: Subir datos del día actual si están disponibles

### **Escenario 2: Corrupción de Datos**

1. **Identificar**: Verificar con queries SQL qué datos están corruptos
2. **Restaurar**: Solo las tablas afectadas desde backup
3. **Validar**: Ejecutar queries de integridad

### **Escenario 3: Error de Aplicación**

1. **Rollback**: Revertir deploy en Render
2. **Verificar**: Que datos no estén corruptos
3. **Fix**: Corregir código antes de nuevo deploy

---

## 📝 Checklist de Backups

### **Diario (Automático)**
- [x] Supabase realiza backup automático
- [ ] Verificar que backup existe (cada semana)

### **Semanal (Manual)**
- [ ] Lunes: Ejecutar `export_backup.py`
- [ ] Verificar archivos CSV generados
- [ ] Commit archivos a Git LFS (opcional)

### **Mensual (Manual)**
- [ ] Primer día del mes: Crear backup manual en Supabase
- [ ] Exportar a CSV
- [ ] Subir a almacenamiento externo (Google Drive/Dropbox)

### **Antes de Cambios Importantes**
- [ ] Crear backup manual en Supabase
- [ ] Exportar tablas afectadas a CSV
- [ ] Documentar cambios a realizar

---

## 🔐 Seguridad de Backups

### **Encriptar Backups Locales**

```bash
# Comprimir y encriptar backup
tar -czf - backups/ | openssl enc -aes-256-cbc -salt -out backups_encrypted.tar.gz.enc

# Desencriptar cuando sea necesario
openssl enc -d -aes-256-cbc -in backups_encrypted.tar.gz.enc | tar -xzf -
```

### **Variables de Entorno Seguras**

```bash
# .env.backup (no subir a Git)
DATABASE_URL=postgresql://...
BACKUP_ENCRYPTION_KEY=tu_clave_secreta
```

---

## ⚡ Comandos Rápidos

```bash
# Crear backup inmediato
python export_backup.py

# Verificar backups recientes
python verify_backup.py

# Restaurar desde CSV (ejemplo)
psql $DATABASE_URL -c "\COPY compras_v2 FROM 'backups/compras_v2_latest.csv' CSV HEADER"

# Ver tamaño de tablas
psql $DATABASE_URL -c "
SELECT 
    tablename, 
    pg_size_pretty(pg_total_relation_size(schemaname||'.'||tablename)) AS size
FROM pg_tables 
WHERE schemaname = 'public'
ORDER BY pg_total_relation_size(schemaname||'.'||tablename) DESC;
"
```

---

## 📞 Contacto y Soporte

- **Supabase Support**: https://supabase.com/support
- **Documentación Backups**: https://supabase.com/docs/guides/platform/backups
- **Discord Supabase**: https://discord.supabase.com

---

## 🎯 Acción Inmediata Recomendada

1. ✅ **Restaurar backup de hoy** (antes del borrado)
2. ✅ **Verificar que el fix está desplegado** (`reemplazar_datos=False`)
3. ✅ **Crear backup manual** después de restaurar
4. 📝 **Configurar GitHub Actions** para backups adicionales
5. 📅 **Calendario**: Backups manuales cada lunes

---

**Última actualización**: 11 de Octubre, 2025
**Versión**: 1.0
**Autor**: Sistema Immermex Dashboard

