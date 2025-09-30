"""
Servicio para integración con Microsoft OneDrive
Maneja autenticación, descarga de archivos y sincronización automática
"""

import os
import requests
import json
import logging
from typing import List, Dict, Optional, Tuple
from datetime import datetime, timedelta
import asyncio
import aiohttp
from dataclasses import dataclass
import hashlib

logger = logging.getLogger(__name__)

@dataclass
class OneDriveFile:
    """Estructura para representar un archivo de OneDrive"""
    id: str
    name: str
    size: int
    last_modified: datetime
    download_url: str
    path: str
    hash: str

class OneDriveService:
    """Servicio para interactuar con Microsoft OneDrive API"""
    
    def __init__(self):
        self.client_id = os.getenv("ONEDRIVE_CLIENT_ID")
        self.client_secret = os.getenv("ONEDRIVE_CLIENT_SECRET")
        self.tenant_id = os.getenv("ONEDRIVE_TENANT_ID", "common")
        self.refresh_token = os.getenv("ONEDRIVE_REFRESH_TOKEN")
        self.access_token = None
        self.token_expires_at = None
        
        # URLs de Microsoft Graph API
        self.base_url = "https://graph.microsoft.com/v1.0"
        self.auth_url = f"https://login.microsoftonline.com/{self.tenant_id}/oauth2/v2.0"
        
        # Carpeta específica para archivos de compras
        self.compras_folder_path = os.getenv("ONEDRIVE_COMPRAS_FOLDER", "/Compras")
        
        if not all([self.client_id, self.client_secret, self.refresh_token]):
            logger.warning("OneDrive credentials not fully configured")
    
    async def get_access_token(self) -> str:
        """Obtiene un token de acceso válido"""
        if self.access_token and self.token_expires_at and datetime.now() < self.token_expires_at:
            return self.access_token
        
        if not self.refresh_token:
            raise ValueError("No refresh token available")
        
        token_url = f"{self.auth_url}/token"
        data = {
            "client_id": self.client_id,
            "client_secret": self.client_secret,
            "refresh_token": self.refresh_token,
            "grant_type": "refresh_token",
            "scope": "https://graph.microsoft.com/Files.Read"
        }
        
        async with aiohttp.ClientSession() as session:
            async with session.post(token_url, data=data) as response:
                if response.status == 200:
                    token_data = await response.json()
                    self.access_token = token_data["access_token"]
                    expires_in = token_data.get("expires_in", 3600)
                    self.token_expires_at = datetime.now() + timedelta(seconds=expires_in - 60)
                    return self.access_token
                else:
                    error_text = await response.text()
                    logger.error(f"Failed to refresh token: {response.status} - {error_text}")
                    raise Exception(f"Token refresh failed: {response.status}")
    
    async def get_folder_id(self, folder_path: str) -> Optional[str]:
        """Obtiene el ID de una carpeta por su ruta"""
        try:
            token = await self.get_access_token()
            headers = {"Authorization": f"Bearer {token}"}
            
            # Convertir ruta a formato de API
            if folder_path.startswith("/"):
                folder_path = folder_path[1:]
            
            url = f"{self.base_url}/me/drive/root:/{folder_path}"
            
            async with aiohttp.ClientSession() as session:
                async with session.get(url, headers=headers) as response:
                    if response.status == 200:
                        data = await response.json()
                        return data["id"]
                    elif response.status == 404:
                        logger.warning(f"Folder not found: {folder_path}")
                        return None
                    else:
                        error_text = await response.text()
                        logger.error(f"Failed to get folder ID: {response.status} - {error_text}")
                        return None
        except Exception as e:
            logger.error(f"Error getting folder ID: {e}")
            return None
    
    async def list_files_in_folder(self, folder_path: str = None) -> List[OneDriveFile]:
        """Lista archivos en una carpeta específica"""
        try:
            folder_path = folder_path or self.compras_folder_path
            folder_id = await self.get_folder_id(folder_path)
            
            if not folder_id:
                logger.warning(f"Could not find folder: {folder_path}")
                return []
            
            token = await self.get_access_token()
            headers = {"Authorization": f"Bearer {token}"}
            
            url = f"{self.base_url}/me/drive/items/{folder_id}/children"
            
            files = []
            async with aiohttp.ClientSession() as session:
                async with session.get(url, headers=headers) as response:
                    if response.status == 200:
                        data = await response.json()
                        
                        for item in data.get("value", []):
                            if "file" in item:  # Es un archivo, no una carpeta
                                file_info = OneDriveFile(
                                    id=item["id"],
                                    name=item["name"],
                                    size=item["size"],
                                    last_modified=datetime.fromisoformat(
                                        item["lastModifiedDateTime"].replace("Z", "+00:00")
                                    ),
                                    download_url=item["@microsoft.graph.downloadUrl"],
                                    path=f"{folder_path}/{item['name']}",
                                    hash=hashlib.md5(f"{item['id']}{item['lastModifiedDateTime']}".encode()).hexdigest()
                                )
                                files.append(file_info)
                        
                        logger.info(f"Found {len(files)} files in folder {folder_path}")
                        return files
                    else:
                        error_text = await response.text()
                        logger.error(f"Failed to list files: {response.status} - {error_text}")
                        return []
        except Exception as e:
            logger.error(f"Error listing files: {e}")
            return []
    
    async def download_file(self, file: OneDriveFile) -> bytes:
        """Descarga un archivo desde OneDrive"""
        try:
            async with aiohttp.ClientSession() as session:
                async with session.get(file.download_url) as response:
                    if response.status == 200:
                        content = await response.read()
                        logger.info(f"Downloaded file: {file.name} ({len(content)} bytes)")
                        return content
                    else:
                        error_text = await response.text()
                        logger.error(f"Failed to download file {file.name}: {response.status} - {error_text}")
                        raise Exception(f"Download failed: {response.status}")
        except Exception as e:
            logger.error(f"Error downloading file {file.name}: {e}")
            raise
    
    async def get_file_content(self, file_path: str) -> bytes:
        """Obtiene el contenido de un archivo específico por ruta"""
        try:
            token = await self.get_access_token()
            headers = {"Authorization": f"Bearer {token}"}
            
            # Convertir ruta a formato de API
            if file_path.startswith("/"):
                file_path = file_path[1:]
            
            url = f"{self.base_url}/me/drive/root:/{file_path}:/content"
            
            async with aiohttp.ClientSession() as session:
                async with session.get(url, headers=headers) as response:
                    if response.status == 200:
                        content = await response.read()
                        logger.info(f"Downloaded file: {file_path} ({len(content)} bytes)")
                        return content
                    else:
                        error_text = await response.text()
                        logger.error(f"Failed to download file {file_path}: {response.status} - {error_text}")
                        raise Exception(f"Download failed: {response.status}")
        except Exception as e:
            logger.error(f"Error downloading file {file_path}: {e}")
            raise
    
    async def get_file_info(self, file_path: str) -> Optional[OneDriveFile]:
        """Obtiene información de un archivo específico"""
        try:
            token = await self.get_access_token()
            headers = {"Authorization": f"Bearer {token}"}
            
            # Convertir ruta a formato de API
            if file_path.startswith("/"):
                file_path = file_path[1:]
            
            url = f"{self.base_url}/me/drive/root:/{file_path}"
            
            async with aiohttp.ClientSession() as session:
                async with session.get(url, headers=headers) as response:
                    if response.status == 200:
                        data = await response.json()
                        
                        file_info = OneDriveFile(
                            id=data["id"],
                            name=data["name"],
                            size=data["size"],
                            last_modified=datetime.fromisoformat(
                                data["lastModifiedDateTime"].replace("Z", "+00:00")
                            ),
                            download_url=data["@microsoft.graph.downloadUrl"],
                            path=file_path,
                            hash=hashlib.md5(f"{data['id']}{data['lastModifiedDateTime']}".encode()).hexdigest()
                        )
                        return file_info
                    elif response.status == 404:
                        logger.warning(f"File not found: {file_path}")
                        return None
                    else:
                        error_text = await response.text()
                        logger.error(f"Failed to get file info: {response.status} - {error_text}")
                        return None
        except Exception as e:
            logger.error(f"Error getting file info: {e}")
            return None

class OneDriveSyncService:
    """Servicio para sincronización automática con OneDrive"""
    
    def __init__(self, onedrive_service: OneDriveService):
        self.onedrive_service = onedrive_service
        self.sync_interval = int(os.getenv("ONEDRIVE_SYNC_INTERVAL", "3600"))  # 1 hora por defecto
        self.last_sync = None
        self.processed_files = set()  # Para evitar procesar archivos duplicados
    
    async def sync_folder(self, folder_path: str = None) -> List[str]:
        """Sincroniza archivos de una carpeta específica"""
        try:
            folder_path = folder_path or self.onedrive_service.compras_folder_path
            files = await self.onedrive_service.list_files_in_folder(folder_path)
            
            new_files = []
            for file in files:
                # Solo procesar archivos nuevos o modificados
                if file.hash not in self.processed_files:
                    new_files.append(file.name)
                    self.processed_files.add(file.hash)
            
            self.last_sync = datetime.now()
            logger.info(f"Sync completed. Found {len(new_files)} new/modified files")
            return new_files
            
        except Exception as e:
            logger.error(f"Error during sync: {e}")
            return []
    
    async def get_new_files(self, folder_path: str = None) -> List[OneDriveFile]:
        """Obtiene archivos nuevos desde la última sincronización"""
        try:
            folder_path = folder_path or self.onedrive_service.compras_folder_path
            files = await self.onedrive_service.list_files_in_folder(folder_path)
            
            new_files = []
            for file in files:
                if file.hash not in self.processed_files:
                    new_files.append(file)
            
            return new_files
            
        except Exception as e:
            logger.error(f"Error getting new files: {e}")
            return []
    
    def should_sync(self) -> bool:
        """Verifica si es necesario sincronizar"""
        if not self.last_sync:
            return True
        
        time_since_sync = datetime.now() - self.last_sync
        return time_since_sync.total_seconds() >= self.sync_interval

# Función de utilidad para obtener credenciales de OneDrive
def get_onedrive_credentials_instructions() -> str:
    """Retorna instrucciones para configurar las credenciales de OneDrive"""
    return """
# INSTRUCCIONES PARA CONFIGURAR MICROSOFT ONEDRIVE API

## 1. Registrar aplicación en Azure Portal

1. Ve a https://portal.azure.com
2. Busca "Azure Active Directory" > "App registrations"
3. Haz clic en "New registration"
4. Configura:
   - Name: "Immermex OneDrive Integration"
   - Supported account types: "Accounts in this organizational directory only"
   - Redirect URI: "http://localhost:8080/auth/callback" (para desarrollo)

## 2. Configurar permisos

1. En tu aplicación, ve a "API permissions"
2. Haz clic en "Add a permission"
3. Selecciona "Microsoft Graph"
4. Selecciona "Delegated permissions"
5. Agrega estos permisos:
   - Files.Read
   - Files.ReadWrite
   - User.Read

## 3. Generar client secret

1. Ve a "Certificates & secrets"
2. Haz clic en "New client secret"
3. Copia el valor del secret (solo se muestra una vez)

## 4. Configurar variables de entorno

Agrega estas variables a tu archivo .env:

ONEDRIVE_CLIENT_ID=tu_client_id_aqui
ONEDRIVE_CLIENT_SECRET=tu_client_secret_aqui
ONEDRIVE_TENANT_ID=tu_tenant_id_aqui
ONEDRIVE_REFRESH_TOKEN=tu_refresh_token_aqui
ONEDRIVE_COMPRAS_FOLDER=/Compras
ONEDRIVE_SYNC_INTERVAL=3600

## 5. Obtener refresh token

Para obtener el refresh token inicial, puedes usar este script:

```python
import requests

def get_refresh_token():
    client_id = "tu_client_id"
    client_secret = "tu_client_secret"
    tenant_id = "tu_tenant_id"
    
    auth_url = f"https://login.microsoftonline.com/{tenant_id}/oauth2/v2.0/authorize"
    params = {
        "client_id": client_id,
        "response_type": "code",
        "redirect_uri": "http://localhost:8080/auth/callback",
        "scope": "https://graph.microsoft.com/Files.Read offline_access",
        "response_mode": "query"
    }
    
    print("Ve a esta URL para autorizar:")
    print(f"{auth_url}?{'&'.join([f'{k}={v}' for k, v in params.items()])}")
    
    # Después de autorizar, obtendrás un código que puedes intercambiar por tokens
```

## 6. Crear carpeta en OneDrive

1. Ve a tu OneDrive
2. Crea una carpeta llamada "Compras"
3. Sube tus archivos de compras allí
4. Los archivos deben estar en formato Excel (.xlsx, .xls)
"""
