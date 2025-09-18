# 📊 Immermex Dashboard

Dashboard financiero y operacional moderno para Immermex, construido con React, FastAPI y Tailwind CSS.

## 🚀 Inicio Rápido

### Windows
```bash
# Clonar el repositorio
git clone <tu-repo-url>
cd immermex-dashboard

# Ejecutar el sistema completo
start.bat
```

### Linux/Mac
```bash
# Clonar el repositorio
git clone <tu-repo-url>
cd immermex-dashboard

# Dar permisos de ejecución
chmod +x start.sh

# Ejecutar el sistema completo
./start.sh
```

## 📋 Requisitos Previos

- **Python 3.8+** con pip
- **Node.js 16+** con npm
- **Git** para clonar el repositorio

## 🛠️ Instalación Manual

### Backend (FastAPI)
```bash
cd backend
pip install -r requirements.txt
python simple_main.py
```

### Frontend (React + Vite)
```bash
cd frontend
npm install
npm run dev
```

## 🌐 URLs del Sistema

- **📊 Dashboard**: http://localhost:3000
- **🔧 Backend API**: http://localhost:8000
- **📚 Documentación API**: http://localhost:8000/docs

## 📁 Estructura del Proyecto

```
immermex-dashboard/
├── backend/                 # API FastAPI
│   ├── simple_main.py      # Servidor principal
│   ├── requirements.txt    # Dependencias Python
│   └── data/              # Archivos de datos
├── frontend/               # Aplicación React
│   ├── src/
│   │   ├── components/    # Componentes React
│   │   ├── services/      # Servicios API
│   │   └── types/         # Tipos TypeScript
│   ├── package.json       # Dependencias Node.js
│   └── tailwind.config.js # Configuración Tailwind
├── start.bat              # Script de inicio Windows
├── start.sh               # Script de inicio Linux/Mac
└── README.md              # Este archivo
```

## 🎯 Características

- ✅ **KPIs Financieros**: Facturación, cobranza, inventario
- ✅ **Gráficos Interactivos**: Aging, top clientes, consumo material
- ✅ **Filtros Dinámicos**: Por fecha, cliente, producto
- ✅ **Subida de Archivos**: Drag & drop para Excel/CSV
- ✅ **Diseño Responsivo**: Funciona en desktop y móvil
- ✅ **API REST**: Documentación automática con Swagger

## 🔧 Desarrollo

### Agregar Nuevos KPIs
1. Modificar `backend/simple_main.py` para agregar endpoints
2. Actualizar `frontend/src/types/index.ts` con nuevos tipos
3. Crear componentes en `frontend/src/components/`

### Personalizar Estilos
1. Modificar `frontend/tailwind.config.js` para colores/temas
2. Actualizar `frontend/src/index.css` para estilos globales

## 📊 Datos de Ejemplo

El sistema incluye datos de ejemplo para:
- Facturación mensual
- Estados de cobranza
- CFDI relacionados
- Inventario de materiales

## 🚀 Despliegue

### Desarrollo Local
```bash
npm run dev
```

### Producción
```bash
npm run build
# Servir archivos estáticos desde frontend/dist
```

## 📝 Licencia

MIT License - Ver archivo LICENSE para más detalles.

## 🤝 Contribución

1. Fork el proyecto
2. Crea una rama para tu feature (`git checkout -b feature/AmazingFeature`)
3. Commit tus cambios (`git commit -m 'Add some AmazingFeature'`)
4. Push a la rama (`git push origin feature/AmazingFeature`)
5. Abre un Pull Request

## 📞 Soporte

Para soporte técnico, contacta al equipo de desarrollo de Immermex.