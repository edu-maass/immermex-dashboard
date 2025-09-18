# 🚀 Configuración del Repositorio GitHub

## Pasos Manuales Requeridos:

### 1. Crear Repositorio en GitHub
1. Ve a https://github.com
2. Haz clic en "New repository"
3. Configura:
   - **Name**: `immermex-dashboard`
   - **Description**: `Dashboard financiero y operacional para Immermex`
   - **Visibility**: Public o Private
   - **NO marques** "Add README" (ya existe)
4. Haz clic en "Create repository"

### 2. Conectar Repositorio Local con GitHub
Después de crear el repo, ejecuta estos comandos:

```bash
# Agregar el repositorio remoto (reemplaza TU_USUARIO con tu username de GitHub)
git remote add origin https://github.com/TU_USUARIO/immermex-dashboard.git

# Subir el código
git branch -M main
git push -u origin main
```

### 3. Verificar que Funcione
```bash
# Clonar en otra carpeta para probar
cd ..
git clone https://github.com/TU_USUARIO/immermex-dashboard.git immermex-test
cd immermex-test

# Ejecutar el sistema
start.bat  # En Windows
./start.sh  # En Linux/Mac
```

## 📁 Estructura del Proyecto Subido:

```
immermex-dashboard/
├── backend/                 # API FastAPI
│   ├── simple_main.py      # Servidor principal
│   ├── requirements.txt    # Dependencias Python
│   └── *.csv              # Datos de ejemplo
├── frontend/               # Aplicación React
│   ├── src/components/    # Componentes React
│   ├── package.json       # Dependencias Node.js
│   └── tailwind.config.js # Configuración Tailwind
├── start.bat              # Script Windows
├── start.sh               # Script Linux/Mac
├── README.md              # Documentación
└── .gitignore             # Archivos a ignorar
```

## 🎯 URLs del Sistema:
- **Dashboard**: http://localhost:3000
- **Backend API**: http://localhost:8000
- **Documentación**: http://localhost:8000/docs

## ✅ Listo para Usar:
Una vez subido, cualquier persona puede:
1. Clonar el repo
2. Ejecutar `start.bat` (Windows) o `./start.sh` (Linux/Mac)
3. Acceder al dashboard en http://localhost:3000
