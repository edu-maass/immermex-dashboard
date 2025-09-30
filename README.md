# 📊 Immermex Dashboard

Sistema web moderno para análisis financiero y operacional de Immermex, construido con React, FastAPI, PostgreSQL y Tailwind CSS. Incluye persistencia de datos en la nube con Supabase.

## 🌐 Demo en Línea

**Dashboard en vivo**: https://edu-maass.github.io/immermex-dashboard/
**Backend API**: https://immermex-dashboard.vercel.app
**Documentación API**: https://immermex-dashboard.vercel.app/docs

## 🎯 Características Principales

- ✅ **KPIs Financieros Avanzados**: Facturación, cobranza, inventario, anticipos, análisis de pedidos
- ✅ **Gráficos Interactivos**: Aging de cartera, top clientes, consumo por material, expectativa de cobranza
- ✅ **Filtros Dinámicos**: Por fecha, cliente, agente, material, pedido específico
- ✅ **Subida de Archivos**: Drag & drop para archivos Excel mensuales con procesamiento avanzado
- ✅ **Persistencia de Datos**: Almacenamiento en PostgreSQL con Supabase
- ✅ **Gestión de Datos**: Historial de archivos procesados, eliminación de datos
- ✅ **Análisis por Pedido**: Dashboard especializado para análisis detallado de pedidos
- ✅ **Diseño Responsivo**: Funciona en desktop y móvil
- ✅ **API REST Completa**: Documentación automática con Swagger
- ✅ **Análisis en Tiempo Real**: Cálculo automático de métricas con persistencia
- ✅ **Sistema de Monitoreo**: Métricas de rendimiento y alertas en tiempo real
- ✅ **Optimizaciones Avanzadas**: Caching, compresión, lazy loading, bundle splitting
- ✅ **Seguridad Mejorada**: Rate limiting, validación de entrada, sanitización

## 🚀 Acceso al Sistema

El sistema está desplegado en la nube y no requiere instalación local:

1. **Accede al Dashboard**: https://edu-maass.github.io/immermex-dashboard/
2. **Sube tu archivo Excel** mensual con los datos
3. **Explora los KPIs y gráficos** generados automáticamente
4. **Usa los filtros** para análisis específicos

## 📁 Estructura del Proyecto

```
immermex-dashboard/
├── frontend/                    # Aplicación React
│   ├── src/
│   │   ├── components/         # Componentes React
│   │   │   ├── Charts/         # Gráficos especializados
│   │   │   │   ├── AgingChart.tsx
│   │   │   │   ├── ConsumoMaterialChart.tsx
│   │   │   │   ├── ExpectativaCobranzaChart.tsx
│   │   │   │   └── TopClientesChart.tsx
│   │   │   ├── ui/             # Componentes UI base
│   │   │   ├── Dashboard.tsx   # Dashboard principal
│   │   │   ├── DashboardFiltrado.tsx # Dashboard por pedidos
│   │   │   ├── DataManagement.tsx    # Gestión de datos
│   │   │   ├── FileUpload.tsx  # Subida de archivos
│   │   │   ├── Filters.tsx     # Filtros dinámicos
│   │   │   ├── KPICard.tsx     # Tarjetas de KPIs
│   │   │   └── MainDashboard.tsx # Componente principal
│   │   ├── services/           # Servicios API
│   │   ├── types/             # Tipos TypeScript
│   │   └── App.tsx            # Punto de entrada
│   └── package.json            # Dependencias Node.js
├── backend/                    # API FastAPI con Base de Datos
│   ├── main_with_db.py        # Servidor principal con persistencia
│   ├── database_service.py    # Servicio de base de datos
│   ├── database.py            # Configuración de BD y modelos
│   ├── data_processor.py       # Procesador de datos avanzado
│   ├── excel_processor.py     # Procesador especializado de Excel
│   ├── models.py              # Modelos Pydantic
│   ├── logging_config.py      # Configuración de logging
│   ├── create_tables_supabase.sql # Script de migración
│   ├── migrate_to_supabase.py # Migración a Supabase
│   └── requirements.txt       # Dependencias Python
├── docs/                      # Documentación técnica completa
│   ├── SISTEMA_IMMERMEX_DASHBOARD.md
│   ├── ESTRUCTURA_PROYECTO.md
│   ├── PROCESADOR_EXCEL.md
│   ├── SUPABASE_INTEGRATION.md
│   ├── DEPLOYMENT_PRODUCTION.md
│   └── CORRECCIONES_BUGS.md
└── README.md                  # Este archivo
```

## 📊 Formato de Datos Requerido

El sistema procesa archivos Excel con las siguientes hojas:

1. **'facturacion'** - Datos de facturación
2. **'cobranza'** - Datos de cobranza
3. **'cfdi relacionados'** - Anticipos y notas de crédito
4. **Hoja de pedidos** (ej: '1-14 sep') - Datos de pedidos por período

### 🔧 Procesador de Excel Avanzado

El sistema incluye un procesador especializado (`excel_processor.py`) que:

- ✅ **Detección automática** de filas de encabezados
- ✅ **Mapeo flexible** de nombres de columnas
- ✅ **Limpieza robusta** de datos y validación de tipos
- ✅ **Normalización** de fechas, montos y UUIDs
- ✅ **Cálculo automático** de relaciones entre tablas
- ✅ **Manejo de errores** con logging detallado
- ✅ **Persistencia automática** en base de datos PostgreSQL

**Columnas estándar procesadas:**
- **Facturación**: fecha_factura, cliente, monto_total, saldo_pendiente, uuid_factura, agente
- **Cobranza**: fecha_pago, importe_pagado, uuid_factura_relacionada, forma_pago
- **CFDI**: tipo_relacion, importe_relacion (filtra anticipos y notas de crédito)
- **Pedidos**: folio_factura, pedido, kg, material, dias_credito, precio_unitario

### 🗄️ Base de Datos y Persistencia

El sistema utiliza PostgreSQL con Supabase para:

- ✅ **Almacenamiento persistente** de todos los datos procesados
- ✅ **Historial de archivos** procesados con metadatos
- ✅ **KPIs calculados** y almacenados automáticamente
- ✅ **Filtros persistentes** que se mantienen entre sesiones
- ✅ **Gestión de datos** con capacidad de eliminación
- ✅ **Backup automático** y escalabilidad en la nube

## 🔧 Para Desarrolladores

### Documentación Técnica Completa

- **[API Documentation](docs/API_DOCUMENTATION.md)**: Documentación completa de la API REST con ejemplos
- **[System Architecture](docs/SYSTEM_ARCHITECTURE.md)**: Arquitectura del sistema, tecnologías y componentes
- **[Development Guide](docs/DEVELOPMENT_GUIDE.md)**: Guía completa de desarrollo, testing y deployment
- **[Troubleshooting & FAQ](docs/TROUBLESHOOTING_FAQ.md)**: Solución de problemas comunes y debugging
- **[Sistema Original](docs/SISTEMA_IMMERMEX_DASHBOARD.md)**: Documentación técnica original del sistema

### Agregar Nuevas Funcionalidades
1. **Nuevos KPIs**: Modificar `backend/database_service.py` y `backend/main_with_db.py`
2. **Nuevos Gráficos**: Crear componentes en `frontend/src/components/Charts/`
3. **Nuevos Filtros**: Actualizar `frontend/src/components/Filters.tsx`
4. **Nuevas Tablas**: Agregar modelos en `backend/database.py` y migrar con Supabase
5. **Nuevos Endpoints**: Implementar en `backend/main_with_db.py` con documentación automática

## 📞 Soporte y Contacto

- **Desarrollador**: Eduardo Maass
- **Repositorio**: https://github.com/edu-maass/immermex-dashboard
- **Dashboard**: https://edu-maass.github.io/immermex-dashboard/
- **Documentación Técnica**: [docs/SISTEMA_IMMERMEX_DASHBOARD.md](./docs/SISTEMA_IMMERMEX_DASHBOARD.md)

## 📝 Licencia

MIT License - Ver archivo LICENSE para más detalles.

---

*Sistema Immermex Dashboard v2.0.0 - Sistema completo de análisis financiero con persistencia de datos*