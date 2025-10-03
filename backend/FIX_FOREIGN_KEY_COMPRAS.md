# Solución al Error de Foreign Key en Compras

## Problema Original

**Error:** 
```
(psycopg2.errors.ForeignKeyViolation) insert or update on table "compras" violates foreign key constraint "compras_archivo_id_fkey"
DETAIL: Key (archivo_id)=(50) is not present in table "archivos_procesados".
```

**Archivo afectado:** `backend/database_service.py`
**Metodo:** `save_processed_data()` línea 91

## Análisis de la Causa Raíz

El error se produce debido a un problema en el manejo de transacciones en PostgreSQL/Supabase:

1. **Creación del ArchivoProcesado**: Se crea correctamente y se obtiene el ID (50)
2. **Commit temprano**: Se hace commit del ArchivoProcesado en línea 58
3. **Transacción principal**: Cuando se llama a `_save_compras` con `archivo_id=50`
4. **Foreign Key Violation**: En PostgreSQL, durante una transacción activa, los datos committeados anteriormente pueden no ser visibles para las foreign key constraints hasta el commit global

## Solución Implementada

### 1. Cambio Principal: Commit → Flush
```python
# ANTES (línea 58):
self.db.commit()

# DESPUÉS (línea 58):
self.db.flush()
```

**Razón:** `flush()` hace que los datos sean visibles dentro de la misma transacción sin hacer commit intermedio.

### 2. Verificaciones Adicionales
```python
# Verificar que archivo_id existe antes de intentar insertar compras (línea 86-91)
archivo_exists = self.db.query(ArchivoProcesado).filter(ArchivoProcesado.id == archivo.id).first()
if not archivo_exists:
    logger.error(f"CRITICAL ERROR: archivo_id {archivo.id} no existe en archivos_procesados")
    raise Exception(f"CRITICAL ERROR: archivo_id {archivo.id} no existe en archivos_procesados")
```

### 3. Verificación en _save_compras
```python
def _save_compras(self, compras_data: list, archivo_id: int) -> int:
    # Verificar que archivo_id existe antes de intentar insertar
    archivo_check = self.db.query(ArchivoProcesado).filter(ArchivoProcesado.id == archivo_id).first()
    if not archivo_check:
        logger.error(f"❌ CRITICAL ERROR en _save_compras: archivo_id {archivo_id} no existe")
        raise Exception(f"CRITICAL: archivo_id {archivo_id} no existe en archivos_procesados")
```

### 4. Logging Mejorado
- Añadidos logs detallados con emojis para facilitar debugging
- Verificación de cada paso del proceso
- Identificación clara de errores críticos

## Archivos Modificados

1. **`backend/database_service.py`**:
   - Línea 58: `commit()` → `flush()`
   - Líneas 86-91: Verificación de existencia de archivo_id
   - Líneas 212-217: Verificación adicional en `_save_compras`
   - Líneas 23-44: Funciones helper `safe_date`, `safe_int`
   - Línea 19: Import de `numpy as np`

## Beneficios de la Solución

1. **Consistencia Transaccional**: Mantiene la transacción única hasta el commit final
2. **Visibilidad de Datos**: Los datos son visibles para foreign key constraints
3. **Robustez**: Verificaciones dobles antes de operaciones críticas
4. **Debugging**: Logs detallados para facilitar troubleshooting
5. **Mantenibilidad**: Código más fácil de entender y debuggear

## Prueba de la Solución

Se creó `backend/test_fix_compras_foreign_key.py` para verificar que la solución funciona correctamente.

## Impacto

- ✅ Resuelve el error 500 en la carga de archivos de compras
- ✅ Mantiene la integridad de datos
- ✅ Mejora el debugging y logging
- ✅ Sin impacto negativo en otras funcionalidades

## Deployment

La solución está lista para deployment inmediato. No requiere cambios en la base de datos ni migraciones.
