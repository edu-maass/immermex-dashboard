# Modificaciones de KPIs de Cobranza para Pestaña de Pedidos

## Resumen de Cambios Implementados

Se han implementado las modificaciones solicitadas para los KPIs de cobranza en la pestaña de pedidos, siguiendo la relación específica entre las tablas de Supabase.

### Relaciones Implementadas

1. **folio_factura (Pedidos) == folio_factura (Facturación)**
   - Se obtienen los folios de factura de los pedidos filtrados
   - Se buscan las facturas que coincidan con estos folios

2. **folio_factura (Facturación) -> uuid_factura (Facturación)**
   - Se extraen los UUIDs de las facturas encontradas
   - Se crea un conjunto de UUIDs para búsqueda eficiente

3. **uuid_factura (Facturación) == uuid_factura_relacionada (Cobranza)**
   - Se buscan las cobranzas que tengan uuid_factura_relacionada coincidente
   - Solo se consideran cobranzas válidas (con folio_pago válido)

### Cálculos Implementados

#### Cobranza Sin IVA
- Se calcula dividiendo la cobranza total entre 1.16
- Fórmula: `cobranza_sin_iva = sum(c.importe_pagado / 1.16 for c in cobranzas_relacionadas)`

#### Porcentaje Cobrado
- Se calcula como: `(cobranza_total / facturacion_total * 100)`
- Solo considera la cobranza relacionada con las facturas de los pedidos filtrados

### Archivos Modificados

#### Backend
- **`backend/database_service.py`**: 
  - Modificado el método `calculate_kpis()` para implementar la nueva lógica de filtrado
  - Agregada lógica específica para filtros por pedidos
  - Implementado cálculo correcto de cobranza sin IVA

#### Frontend
- **`frontend/src/components/DashboardFiltrado.tsx`**: 
  - Ya mostraba correctamente los KPIs de cobranza
  - No requirió modificaciones adicionales

### Funcionalidad Verificada

Se creó y ejecutó un test completo que verificó:

1. **KPIs sin filtros**: Cálculo correcto de todos los indicadores
2. **KPIs filtrados por pedido específico**: Relación correcta entre pedidos, facturas y cobranza
3. **Cobranza parcial**: Manejo correcto de cobranzas parciales

### Resultados del Test

```
✅ Test 1: KPIs sin filtros
   - Facturación total: $46,400.00
   - Facturación sin IVA: $40,000.00
   - Cobranza total: $29,000.00
   - Cobranza sin IVA: $25,000.00
   - % Cobrado: 62.5%

✅ Test 2: KPIs filtrados por PED001
   - Facturación total: $11,600.00
   - Facturación sin IVA: $10,000.00
   - Cobranza total: $11,600.00
   - Cobranza sin IVA: $10,000.00
   - % Cobrado: 100.0%

✅ Test 3: KPIs filtrados por PED002
   - Facturación total: $34,800.00
   - Cobranza total: $17,400.00
   - % Cobrado: 50.0%
```

### Beneficios de la Implementación

1. **Precisión**: Solo se muestra la cobranza relacionada con las facturas de los pedidos filtrados
2. **Transparencia**: Cálculo correcto de cobranza sin IVA dividiendo entre 1.16
3. **Exactitud**: Porcentaje cobrado calculado correctamente como cobranza/facturación
4. **Rendimiento**: Uso eficiente de índices de base de datos para las relaciones
5. **Mantenibilidad**: Código bien documentado y testeado

### Uso en el Frontend

Los usuarios pueden ahora:
- Filtrar por pedidos específicos en la pestaña de pedidos
- Ver la cobranza exacta relacionada con esos pedidos
- Observar el porcentaje cobrado preciso
- Analizar la cobranza sin IVA correctamente calculada

La implementación está lista para uso en producción y ha sido verificada mediante tests automatizados.
