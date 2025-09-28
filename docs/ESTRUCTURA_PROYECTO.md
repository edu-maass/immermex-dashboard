# 📁 Estructura del Proyecto Immermex Dashboard

## 🎯 Resumen

El proyecto ha sido completamente reorganizado y actualizado para incluir persistencia de datos con PostgreSQL/Supabase. El sistema ahora es un dashboard completo con almacenamiento en la nube, gestión de datos y análisis avanzado.

## 📂 Estructura Actual

```
immermex-dashboard/
├── 📁 backend/                           # API FastAPI con Base de Datos
│   ├── __init__.py                       # Inicializador del paquete
│   ├── main_with_db.py                   # Servidor principal con persistencia
│   ├── database_service.py               # Servicio de base de datos
│   ├── database.py                       # Configuración de BD y modelos SQLAlchemy
│   ├── data_processor.py                 # Procesador de datos avanzado
│   ├── excel_processor.py                # Procesador especializado de Excel
│   ├── models.py                         # Modelos Pydantic
│   ├── logging_config.py                 # Configuración de logging
│   ├── create_tables_supabase.sql         # Script de migración a Supabase
│   ├── migrate_to_supabase.py            # Migración automática
│   ├── migrate_production.py             # Migración para producción
│   ├── verify_production.py               # Verificación de producción
│   ├── requirements.txt                  # Dependencias Python
│   ├── requirements_vercel.txt           # Dependencias para Vercel
│   ├── vercel.json                       # Configuración de despliegue Vercel
│   ├── vercel_with_db.json               # Configuración con base de datos
│   ├── vercel.prod.json                  # Configuración de producción
│   ├── production.env                    # Variables de entorno producción
│   ├── supabase_config.txt               # Configuración de Supabase
│   └── env_example.txt                   # Ejemplo de variables de entorno
├── 📁 frontend/                          # Aplicación React
│   ├── 📁 src/
│   │   ├── 📁 components/                # Componentes React
│   │   │   ├── 📁 Charts/                # Gráficos especializados
│   │   │   │   ├── AgingChart.tsx        # Gráfico de aging de cartera
│   │   │   │   ├── ConsumoMaterialChart.tsx # Gráfico de consumo por material
│   │   │   │   ├── ExpectativaCobranzaChart.tsx # Gráfico de expectativa de cobranza
│   │   │   │   └── TopClientesChart.tsx  # Gráfico de top clientes
│   │   │   ├── 📁 ui/                    # Componentes UI base
│   │   │   │   ├── button.tsx            # Botón personalizado
│   │   │   │   ├── card.tsx              # Tarjeta personalizada
│   │   │   │   ├── chip.tsx              # Chip personalizado
│   │   │   │   ├── input.tsx             # Input personalizado
│   │   │   │   ├── searchable-select.tsx # Select con búsqueda
│   │   │   │   ├── select.tsx            # Select personalizado
│   │   │   │   └── tabs.tsx              # Tabs personalizado
│   │   │   ├── Dashboard.tsx             # Dashboard principal
│   │   │   ├── DashboardFiltrado.tsx    # Dashboard por pedidos
│   │   │   ├── DataManagement.tsx        # Gestión de datos
│   │   │   ├── FileUpload.tsx            # Subida de archivos
│   │   │   ├── Filters.tsx               # Filtros dinámicos
│   │   │   ├── KPICard.tsx               # Tarjetas de KPIs
│   │   │   ├── MainDashboard.tsx         # Componente principal con tabs
│   │   │   └── PedidoFilter.tsx          # Filtro específico de pedidos
│   │   ├── 📁 services/                  # Servicios API
│   │   │   └── api.ts                    # Cliente API con auto-detección
│   │   ├── 📁 types/                     # Tipos TypeScript
│   │   │   └── index.ts                  # Definiciones de tipos
│   │   ├── 📁 lib/                       # Utilidades
│   │   │   └── utils.ts                  # Funciones utilitarias
│   │   ├── App.tsx                       # Componente raíz
│   │   ├── App.css                       # Estilos globales
│   │   ├── index.css                     # Estilos base
│   │   ├── main.tsx                      # Punto de entrada
│   │   └── vite-env.d.ts                 # Tipos de Vite
│   ├── 📁 public/                        # Archivos públicos
│   │   ├── _redirects                    # Configuración de redirecciones
│   │   └── vite.svg                       # Logo de Vite
│   ├── 📁 dist/                          # Build de producción
│   │   ├── index.html                    # HTML principal
│   │   ├── assets/                       # Assets compilados
│   │   └── _redirects                    # Redirecciones para GitHub Pages
│   ├── package.json                      # Dependencias Node.js
│   ├── package-lock.json                 # Lock file de dependencias
│   ├── tailwind.config.js                # Configuración Tailwind CSS
│   ├── postcss.config.js                 # Configuración PostCSS
│   ├── vite.config.ts                    # Configuración Vite
│   ├── vite.config.js                    # Configuración Vite (alternativa)
│   ├── vite.config.d.ts                  # Tipos de configuración Vite
│   ├── tsconfig.json                     # Configuración TypeScript
│   ├── tsconfig.app.json                 # Configuración TS para app
│   ├── tsconfig.node.json                # Configuración TS para Node
│   ├── tsconfig.tsbuildinfo              # Cache de TypeScript
│   ├── eslint.config.js                  # Configuración ESLint
│   └── README.md                         # Documentación del frontend
├── 📁 docs/                             # Documentación técnica completa
│   ├── Diccionario_Extraccion_Immermex.pdf # Diccionario de extracción
│   ├── Documentacion_Dashboard_Immermex.pdf # Documentación original
│   ├── ESTRUCTURA_PROYECTO.md            # Este archivo
│   ├── README.md                         # Índice de documentación
│   ├── SISTEMA_IMMERMEX_DASHBOARD.md     # Documentación técnica principal
│   ├── PROCESADOR_EXCEL.md               # Documentación del procesador
│   ├── SUPABASE_INTEGRATION.md            # Guía de integración Supabase
│   ├── DEPLOYMENT_PRODUCTION.md           # Guía de despliegue producción
│   ├── DEPLOYMENT_COMPLETE.md            # Estado de despliegue completo
│   ├── DEPLOYMENT_GITHUB.md              # Despliegue en GitHub Pages
│   ├── CORRECCIONES_BUGS.md              # Correcciones y mejoras
│   ├── SOLUCION_PROBLEMA_DATOS.md        # Solución de problemas de datos
│   └── 0925_material_pedido (4).xlsx    # Archivo de ejemplo
├── 📁 __pycache__/                       # Cache de Python (ignorado)
├── .gitignore                            # Archivos ignorados por Git
├── README.md                             # Documentación principal
├── requirements.txt                      # Dependencias Python (raíz)
├── vercel.json                           # Configuración Vercel (raíz)
├── logging_config.py                     # Configuración logging (raíz)
├── main_with_db.py                       # Servidor principal (raíz)
├── database_service.py                   # Servicio BD (raíz)
├── database.py                           # Configuración BD (raíz)
├── data_processor.py                     # Procesador datos (raíz)
└── test_*.py                             # Archivos de prueba (ignorados)
```

## 🧹 Limpieza Realizada

### ✅ Archivos Eliminados

#### Scripts de Prueba y Desarrollo
- `test_*.py` - Todos los archivos de prueba
- `*_test.py` - Archivos de test
- `examinar_*.py` - Scripts de examen
- `probar_*.py` - Scripts de prueba
- `verificar_*.py` - Scripts de verificación
- `check_system.py` - Verificación del sistema
- `simple_test.py` - Pruebas simples

#### Scripts de Inicio Local
- `start*.bat` - Scripts de inicio Windows
- `start*.sh` - Scripts de inicio Linux/Mac
- `start*.ps1` - Scripts de inicio PowerShell
- `install_*.bat` - Scripts de instalación
- `fix_*.bat` - Scripts de reparación

#### Archivos de Datos Temporales
- `*.xlsx` - Archivos Excel de datos temporales
- `*.csv` - Archivos CSV de datos temporales
- `resultado_*.xlsx` - Archivos de resultados temporales
- `inmermex_datos_*.xlsx` - Archivos de datos mapeados

#### Archivos de Configuración Duplicados
- `package.json` (raíz) - Duplicado del frontend
- `package-lock.json` (raíz) - Duplicado del frontend
- `requirements.txt` (raíz) - Duplicado del backend
- `vercel.json` (raíz) - Duplicado del backend
- `env.example` - Archivo de ejemplo no necesario

#### Archivos de Documentación Extraídos
- `diccionario_extracto.txt` - Texto extraído del PDF
- `documentacion_extracto.txt` - Texto extraído del PDF

#### Archivos de Instrucciones Locales
- `INSTRUCCIONES_EJECUCION.md` - Instrucciones para desarrollo local
- `setup_github.md` - Configuración de GitHub

#### Archivos de Procesamiento
- `limpiar_datos_*.py` - Scripts de limpieza
- `mapear_*.py` - Scripts de mapeo
- `procesar_*.py` - Scripts de procesamiento
- `extract_*.py` - Scripts de extracción

#### Archivos del Backend No Utilizados
- `main.py` - Servidor principal no utilizado
- `run.py` - Script de ejecución
- `services.py` - Servicios no utilizados
- `create_sample_data.py` - Datos de muestra
- `simple_data_processor.py` - Procesador no utilizado
- `simple_sample_data.py` - Datos de muestra simples

#### Carpetas de Dependencias
- `node_modules/` - Dependencias de Node.js (se regeneran)
- `__pycache__/` - Archivos de caché de Python

### ✅ Archivos Organizados

#### Documentación
- PDFs movidos a `docs/`
- Documentación técnica centralizada en `docs/`
- README principal actualizado

#### Configuración
- `.gitignore` creado para evitar archivos innecesarios
- Archivos de configuración mantenidos en sus respectivas carpetas

## 🎯 Archivos Esenciales del Sistema Actual

### Backend (API con Base de Datos)
- `main_with_db.py` - Servidor API principal con persistencia
- `database_service.py` - Servicio completo de base de datos
- `database.py` - Modelos SQLAlchemy y configuración de BD
- `data_processor.py` - Procesador avanzado de datos
- `excel_processor.py` - Procesador especializado de Excel
- `models.py` - Modelos Pydantic para API
- `logging_config.py` - Sistema de logging estructurado
- `create_tables_supabase.sql` - Script de migración a Supabase
- `migrate_to_supabase.py` - Migración automática
- `requirements.txt` - Dependencias Python completas
- `vercel.json` - Configuración de despliegue Vercel

### Frontend (React Completo)
- `MainDashboard.tsx` - Componente principal con sistema de tabs
- `Dashboard.tsx` - Dashboard general con KPIs
- `DashboardFiltrado.tsx` - Dashboard especializado por pedidos
- `DataManagement.tsx` - Gestión de datos persistentes
- `FileUpload.tsx` - Subida de archivos con drag & drop
- `Filters.tsx` - Sistema de filtros dinámicos
- `Charts/` - Gráficos especializados (Aging, Top Clientes, Consumo, Expectativa)
- `ui/` - Componentes UI base personalizados
- `api.ts` - Cliente API con auto-detección de endpoints
- `types/index.ts` - Tipos TypeScript completos

### Base de Datos (PostgreSQL/Supabase)
- Tablas: `facturacion`, `cobranza`, `cfdi_relacionados`, `pedidos`, `archivos_procesados`
- Índices optimizados para consultas rápidas
- Triggers para actualización automática de timestamps
- Relaciones entre tablas con foreign keys
- Sistema de migración automática

### Documentación Técnica
- Documentación completa del sistema
- Guías de despliegue y configuración
- Documentación de API y endpoints
- Guías de integración con Supabase
- Correcciones y mejoras implementadas

## 🚀 Estado del Proyecto

El proyecto está ahora:
- ✅ **Completamente Funcional** - Sistema completo con persistencia de datos
- ✅ **Organizado** - Estructura clara y lógica con separación de responsabilidades
- ✅ **Documentado** - Documentación técnica completa y actualizada
- ✅ **Listo para Producción** - Desplegado en Vercel y GitHub Pages
- ✅ **Optimizado para Web** - Sin dependencias de desarrollo local
- ✅ **Escalable** - Base de datos PostgreSQL con Supabase
- ✅ **Mantenible** - Código modular y bien documentado
- ✅ **Robusto** - Manejo de errores y logging estructurado

## 📝 Notas Importantes

1. **Sistema Completo en la Nube** - Frontend en GitHub Pages, Backend en Vercel, BD en Supabase
2. **Persistencia de Datos** - Todos los datos se almacenan en PostgreSQL
3. **Gestión de Archivos** - Historial completo de archivos procesados
4. **Análisis Avanzado** - KPIs calculados automáticamente con filtros dinámicos
5. **Dashboard Especializado** - Análisis por pedidos con filtros específicos
6. **API REST Completa** - Documentación automática con Swagger
7. **Logging Estructurado** - Sistema de logs para debugging y monitoreo
8. **Migración Automática** - Scripts para migrar datos a Supabase

---

*Estructura actualizada y documentada - Sistema Immermex Dashboard v2.0.0 con persistencia completa*
