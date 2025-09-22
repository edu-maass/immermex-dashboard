# 📊 Immermex Dashboard

Dashboard financiero y operacional moderno para Immermex, construido con React, FastAPI y Tailwind CSS.

## 🌐 Demo en Línea

**Dashboard en vivo**: https://edu-maass.github.io/immermex-dashboard/
**Backend API**: https://immermex-dashboard.vercel.app
**Documentación API**: https://immermex-dashboard.vercel.app/docs

## 🎯 Características Principales

- ✅ **KPIs Financieros**: Facturación, cobranza, inventario, anticipos
- ✅ **Gráficos Interactivos**: Aging de cartera, top clientes, consumo por material
- ✅ **Filtros Dinámicos**: Por fecha, cliente, agente, material
- ✅ **Subida de Archivos**: Drag & drop para archivos Excel mensuales
- ✅ **Diseño Responsivo**: Funciona en desktop y móvil
- ✅ **API REST**: Documentación automática con Swagger
- ✅ **Análisis en Tiempo Real**: Cálculo automático de métricas

## 🚀 Acceso al Sistema

El sistema está desplegado en la nube y no requiere instalación local:

1. **Accede al Dashboard**: https://edu-maass.github.io/immermex-dashboard/
2. **Sube tu archivo Excel** mensual con los datos
3. **Explora los KPIs y gráficos** generados automáticamente
4. **Usa los filtros** para análisis específicos

## 📁 Estructura del Proyecto

```
immermex-dashboard/
├── frontend/               # Aplicación React
│   ├── src/
│   │   ├── components/    # Componentes React
│   │   │   ├── Charts/    # Gráficos especializados
│   │   │   └── ui/        # Componentes UI base
│   │   ├── services/      # Servicios API
│   │   └── types/         # Tipos TypeScript
│   └── package.json       # Dependencias Node.js
├── backend/               # API FastAPI
│   ├── simple_main.py     # Servidor principal
│   ├── data_processor.py  # Procesador de datos
│   ├── models.py          # Modelos Pydantic
│   └── requirements.txt   # Dependencias Python
├── docs/                  # Documentación técnica
│   └── SISTEMA_IMMERMEX_DASHBOARD.md
└── README.md              # Este archivo
```

## 📊 Formato de Datos Requerido

El sistema procesa archivos Excel con las siguientes hojas:

1. **'facturacion'** - Datos de facturación
2. **'cobranza'** - Datos de cobranza
3. **'cfdi relacionados'** - Anticipos y notas de crédito
4. **Hoja de pedidos** (ej: '1-14 sep') - Datos de pedidos por período

## 🔧 Para Desarrolladores

### Documentación Técnica
Consulta la [documentación técnica completa](./docs/SISTEMA_IMMERMEX_DASHBOARD.md) para:
- Arquitectura detallada del sistema
- API endpoints y especificaciones
- Guías de desarrollo y mantenimiento
- Configuración de despliegue

### Agregar Nuevas Funcionalidades
1. **Nuevos KPIs**: Modificar `backend/simple_main.py`
2. **Nuevos Gráficos**: Crear componentes en `frontend/src/components/Charts/`
3. **Nuevos Filtros**: Actualizar `frontend/src/components/Filters.tsx`

## 📞 Soporte y Contacto

- **Desarrollador**: Eduardo Maass
- **Repositorio**: https://github.com/edu-maass/immermex-dashboard
- **Dashboard**: https://edu-maass.github.io/immermex-dashboard/
- **Documentación Técnica**: [docs/SISTEMA_IMMERMEX_DASHBOARD.md](./docs/SISTEMA_IMMERMEX_DASHBOARD.md)

## 📝 Licencia

MIT License - Ver archivo LICENSE para más detalles.

---

*Sistema Immermex Dashboard v1.0.0 - Dashboard financiero y operacional moderno*