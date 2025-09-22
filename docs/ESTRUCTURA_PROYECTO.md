# 📁 Estructura del Proyecto Immermex Dashboard

## 🎯 Resumen

El proyecto ha sido organizado y limpiado para mantener solo los archivos esenciales para el funcionamiento del sistema web. Se eliminaron todos los scripts de prueba, archivos temporales y configuraciones de desarrollo local.

## 📂 Estructura Actual

```
immermex-dashboard/
├── 📁 backend/                    # API FastAPI
│   ├── __init__.py               # Inicializador del paquete
│   ├── data_processor.py         # Procesador de datos Excel
│   ├── database.py               # Configuración de base de datos
│   ├── models.py                 # Modelos Pydantic
│   ├── requirements.txt          # Dependencias Python
│   ├── simple_main.py            # Servidor principal (API)
│   └── vercel.json               # Configuración de despliegue Vercel
├── 📁 frontend/                   # Aplicación React
│   ├── 📁 src/
│   │   ├── 📁 components/        # Componentes React
│   │   │   ├── 📁 Charts/        # Gráficos especializados
│   │   │   │   ├── AgingChart.tsx
│   │   │   │   ├── ConsumoMaterialChart.tsx
│   │   │   │   └── TopClientesChart.tsx
│   │   │   ├── 📁 ui/            # Componentes UI base
│   │   │   │   ├── button.tsx
│   │   │   │   ├── card.tsx
│   │   │   │   ├── input.tsx
│   │   │   │   └── select.tsx
│   │   │   ├── Dashboard.tsx     # Componente principal
│   │   │   ├── FileUpload.tsx    # Subida de archivos
│   │   │   ├── Filters.tsx       # Filtros dinámicos
│   │   │   └── KPICard.tsx       # Tarjetas de KPIs
│   │   ├── 📁 services/          # Servicios API
│   │   │   └── api.ts            # Cliente API
│   │   ├── 📁 types/             # Tipos TypeScript
│   │   │   └── index.ts          # Definiciones de tipos
│   │   ├── App.tsx               # Componente raíz
│   │   ├── App.css               # Estilos globales
│   │   ├── index.css             # Estilos base
│   │   └── main.tsx              # Punto de entrada
│   ├── 📁 public/                # Archivos públicos
│   │   ├── _redirects            # Configuración de redirecciones
│   │   └── vite.svg              # Logo de Vite
│   ├── package.json              # Dependencias Node.js
│   ├── package-lock.json         # Lock file de dependencias
│   ├── tailwind.config.js        # Configuración Tailwind CSS
│   ├── vite.config.ts            # Configuración Vite
│   └── tsconfig.json             # Configuración TypeScript
├── 📁 docs/                      # Documentación
│   ├── Diccionario_Extraccion_Immermex.pdf
│   ├── Documentacion_Dashboard_Immermex.pdf
│   ├── ESTRUCTURA_PROYECTO.md    # Este archivo
│   ├── README.md                 # Índice de documentación
│   └── SISTEMA_IMMERMEX_DASHBOARD.md
├── .gitignore                    # Archivos ignorados por Git
└── README.md                     # Documentación principal
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

## 🎯 Archivos Esenciales Mantenidos

### Backend
- `simple_main.py` - Servidor API principal
- `data_processor.py` - Procesador de datos Excel
- `models.py` - Modelos de datos
- `database.py` - Configuración de BD
- `requirements.txt` - Dependencias Python
- `vercel.json` - Configuración de despliegue

### Frontend
- Estructura completa de React
- Componentes de UI y gráficos
- Servicios de API
- Configuración de build y desarrollo

### Documentación
- Documentación técnica completa
- PDFs de especificaciones
- README principal actualizado

## 🚀 Estado del Proyecto

El proyecto está ahora:
- ✅ **Limpio** - Sin archivos innecesarios
- ✅ **Organizado** - Estructura clara y lógica
- ✅ **Documentado** - Documentación completa
- ✅ **Listo para Producción** - Solo archivos esenciales
- ✅ **Optimizado para Web** - Sin dependencias de desarrollo local

## 📝 Notas Importantes

1. **No se requieren scripts de inicio local** - El sistema se ejecuta desde la web
2. **Los archivos de datos se suben dinámicamente** - No se almacenan archivos estáticos
3. **La documentación está centralizada** - Todo en la carpeta `docs/`
4. **El .gitignore previene archivos innecesarios** - Evita subir archivos temporales

---

*Estructura organizada y documentada - Sistema Immermex Dashboard v1.0.0*
