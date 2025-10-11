# Implementación de Columnas Calculadas: dias_transporte y dias_puerto_planta

## Resumen
Se han agregado dos columnas calculadas a la tabla `compras_v2` en Supabase para trackear métricas de tiempo en el proceso de importación:

- **dias_transporte**: Días entre `fecha_salida_real` y `fecha_arribo_real`
- **dias_puerto_planta**: Días entre `fecha_arribo_real` y `fecha_planta_real`

## Archivos Modificados

### 1. `backend/add_dias_columns_to_compras_v2.sql` (NUEVO)
Script SQL para ejecutar en Supabase que:
- Agrega las columnas `dias_transporte` y `dias_puerto_planta` a la tabla `compras_v2`
- Calcula valores para registros existentes que ya tienen las fechas reales
- Crea índices para mejorar el rendimiento
- Agrega comentarios de documentación

**Instrucciones de uso:**
```sql
-- Ejecutar en el SQL Editor de Supabase
-- El script es idempotente (puede ejecutarse múltiples veces sin problemas)
```

### 2. `backend/compras_v2_service.py`
Se agregaron y modificaron los siguientes métodos:

#### Métodos Nuevos:
- **`calculate_dias_transporte(fecha_salida_real, fecha_arribo_real)`**
  - Calcula los días de transporte marítimo
  - Retorna `None` si alguna fecha es nula
  - Maneja conversión de strings a fechas automáticamente
  
- **`calculate_dias_puerto_planta(fecha_arribo_real, fecha_planta_real)`**
  - Calcula los días desde puerto hasta planta
  - Retorna `None` si alguna fecha es nula
  - Maneja conversión de strings a fechas automáticamente

#### Métodos Modificados:
- **`save_compras_v2()`**
  - **INSERT**: Ahora calcula e inserta `dias_transporte` y `dias_puerto_planta` al crear nuevos registros
  - **UPDATE**: Recalcula ambas columnas durante actualizaciones si hay fechas reales disponibles

### 3. `backend/main_with_db.py`
Modificado el endpoint `/api/compras-v2/update-fechas-estimadas`:
- Verifica existencia de las columnas, las crea si no existen
- Recalcula `dias_transporte` para todos los registros con fechas reales
- Recalcula `dias_puerto_planta` para todos los registros con fechas reales
- Proporciona logging detallado de las actualizaciones

## Lógica de Cálculo

### dias_transporte
```python
dias_transporte = fecha_arribo_real - fecha_salida_real
```
- Si `fecha_salida_real` es NULL → `dias_transporte` = NULL
- Si `fecha_arribo_real` es NULL → `dias_transporte` = NULL
- Si ambas fechas existen → calcula la diferencia en días

### dias_puerto_planta
```python
dias_puerto_planta = fecha_planta_real - fecha_arribo_real
```
- Si `fecha_arribo_real` es NULL → `dias_puerto_planta` = NULL
- Si `fecha_planta_real` es NULL → `dias_puerto_planta` = NULL
- Si ambas fechas existen → calcula la diferencia en días

## Flujo de Datos

### Al Insertar Nueva Compra:
1. Se reciben los datos de la compra
2. Si incluye `fecha_salida_real` y `fecha_arribo_real`, calcula `dias_transporte`
3. Si incluye `fecha_arribo_real` y `fecha_planta_real`, calcula `dias_puerto_planta`
4. Inserta el registro con las columnas calculadas

### Al Actualizar Compra Existente:
1. Se verifica qué campos tienen valores nuevos
2. Si se actualizan fechas reales, recalcula las columnas correspondientes
3. Solo actualiza `dias_transporte` si hay valor calculado (no NULL)
4. Solo actualiza `dias_puerto_planta` si hay valor calculado (no NULL)

### En Proceso de Actualización Masiva:
1. Endpoint `/api/compras-v2/update-fechas-estimadas` es llamado
2. Actualiza fechas estimadas según promedio de proveedores
3. Recalcula todas las columnas calculadas para registros con fechas reales
4. Proporciona reporte de cuántos registros fueron actualizados

## Casos de Uso

### Análisis de Tiempos de Transporte
```sql
-- Promedio de días de transporte por proveedor
SELECT 
    proveedor,
    AVG(dias_transporte) as promedio_dias_transporte,
    COUNT(*) as compras_con_datos
FROM compras_v2
WHERE dias_transporte IS NOT NULL
GROUP BY proveedor
ORDER BY promedio_dias_transporte DESC;
```

### Análisis de Tiempos Puerto-Planta
```sql
-- Promedio de días desde puerto hasta planta
SELECT 
    AVG(dias_puerto_planta) as promedio_dias_puerto_planta,
    MIN(dias_puerto_planta) as min_dias,
    MAX(dias_puerto_planta) as max_dias
FROM compras_v2
WHERE dias_puerto_planta IS NOT NULL;
```

### Identificar Retrasos
```sql
-- Compras con tiempos de transporte inusuales (más de 45 días)
SELECT 
    imi,
    proveedor,
    fecha_salida_real,
    fecha_arribo_real,
    dias_transporte
FROM compras_v2
WHERE dias_transporte > 45
ORDER BY dias_transporte DESC;
```

## Ventajas de la Implementación

1. **Consistencia**: Los cálculos se realizan automáticamente, eliminando errores manuales
2. **Rendimiento**: Valores precalculados mejoran velocidad de consultas
3. **Mantenibilidad**: Lógica centralizada en métodos reutilizables
4. **Flexibilidad**: Manejo de NULL permite datos parciales
5. **Retrocompatibilidad**: Script SQL actualiza registros existentes
6. **Idempotencia**: Puede ejecutarse múltiples veces sin efectos adversos

## Próximos Pasos (Opcional)

### Posibles Mejoras Futuras:
1. **Dashboard Visual**: Agregar gráficos de tendencias de tiempos de transporte
2. **Alertas Automáticas**: Notificar cuando tiempos excedan umbrales
3. **Predicción**: Usar datos históricos para predecir tiempos futuros
4. **Comparación**: Comparar tiempos reales vs estimados automáticamente

## Testing

### Casos de Prueba Recomendados:
1. Insertar compra con todas las fechas reales → debe calcular ambas columnas
2. Insertar compra sin fechas reales → ambas columnas deben ser NULL
3. Actualizar compra agregando fechas reales → debe recalcular columnas
4. Actualizar compra sin cambiar fechas reales → columnas no deben cambiar
5. Ejecutar endpoint de actualización masiva → debe procesar todos los registros

## Soporte

Para preguntas o problemas relacionados con esta implementación:
- Revisar logs en `immermex_dashboard.log`
- Verificar estado de columnas en Supabase SQL Editor
- Consultar este documento para entender la lógica

---

**Fecha de Implementación**: Octubre 2025
**Versión**: 1.0
**Estado**: ✅ Completado

