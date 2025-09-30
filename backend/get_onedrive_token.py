"""
Script para obtener el refresh token inicial de Microsoft OneDrive
Ejecuta este script una vez para configurar la autenticación
"""

import requests
import webbrowser
from urllib.parse import urlparse, parse_qs
import json

def get_refresh_token():
    """Obtiene el refresh token inicial para OneDrive"""
    
    # Configura estas variables con tus credenciales de Azure
    CLIENT_ID = input("Ingresa tu Client ID de Azure: ")
    CLIENT_SECRET = input("Ingresa tu Client Secret de Azure: ")
    TENANT_ID = input("Ingresa tu Tenant ID de Azure (o 'common'): ") or "common"
    
    # URL de autorización
    auth_url = f"https://login.microsoftonline.com/{TENANT_ID}/oauth2/v2.0/authorize"
    
    # Parámetros de autorización
    params = {
        "client_id": CLIENT_ID,
        "response_type": "code",
        "redirect_uri": "http://localhost:8080/auth/callback",
        "scope": "https://graph.microsoft.com/Files.Read offline_access",
        "response_mode": "query"
    }
    
    # Construir URL completa
    auth_url_with_params = f"{auth_url}?{'&'.join([f'{k}={v}' for k, v in params.items()])}"
    
    print("\n" + "="*60)
    print("PASO 1: Autorización")
    print("="*60)
    print("Se abrirá tu navegador para autorizar la aplicación.")
    print("Después de autorizar, serás redirigido a una página de error.")
    print("NO TE PREOCUPES, esto es normal.")
    print("\nCopia la URL completa de la página de error y pégala aquí.")
    print("="*60)
    
    # Abrir navegador
    webbrowser.open(auth_url_with_params)
    
    # Obtener código de autorización del usuario
    print("\nPega aquí la URL completa de la página de error:")
    callback_url = input("URL: ").strip()
    
    # Extraer código de la URL
    try:
        parsed_url = urlparse(callback_url)
        query_params = parse_qs(parsed_url.query)
        
        if 'code' in query_params:
            auth_code = query_params['code'][0]
            print(f"\n✓ Código de autorización obtenido: {auth_code[:20]}...")
        else:
            print("❌ No se encontró código de autorización en la URL")
            return None
            
    except Exception as e:
        print(f"❌ Error al procesar la URL: {e}")
        return None
    
    # Intercambiar código por tokens
    print("\n" + "="*60)
    print("PASO 2: Intercambio de tokens")
    print("="*60)
    
    token_url = f"https://login.microsoftonline.com/{TENANT_ID}/oauth2/v2.0/token"
    
    token_data = {
        "client_id": CLIENT_ID,
        "client_secret": CLIENT_SECRET,
        "code": auth_code,
        "redirect_uri": "http://localhost:8080/auth/callback",
        "grant_type": "authorization_code",
        "scope": "https://graph.microsoft.com/Files.Read offline_access"
    }
    
    try:
        response = requests.post(token_url, data=token_data)
        
        if response.status_code == 200:
            tokens = response.json()
            
            print("✓ Tokens obtenidos exitosamente!")
            print(f"Access Token: {tokens['access_token'][:20]}...")
            print(f"Refresh Token: {tokens['refresh_token'][:20]}...")
            
            # Guardar tokens en archivo
            token_info = {
                "client_id": CLIENT_ID,
                "client_secret": CLIENT_SECRET,
                "tenant_id": TENANT_ID,
                "refresh_token": tokens['refresh_token'],
                "access_token": tokens['access_token'],
                "expires_in": tokens.get('expires_in', 3600)
            }
            
            with open("onedrive_tokens.json", "w") as f:
                json.dump(token_info, f, indent=2)
            
            print("\n" + "="*60)
            print("CONFIGURACIÓN COMPLETADA")
            print("="*60)
            print("Los tokens se han guardado en 'onedrive_tokens.json'")
            print("\nAhora agrega estas variables a tu archivo .env:")
            print(f"ONEDRIVE_CLIENT_ID={CLIENT_ID}")
            print(f"ONEDRIVE_CLIENT_SECRET={CLIENT_SECRET}")
            print(f"ONEDRIVE_TENANT_ID={TENANT_ID}")
            print(f"ONEDRIVE_REFRESH_TOKEN={tokens['refresh_token']}")
            print("\n¡Ya puedes usar el servicio de OneDrive!")
            
            return tokens['refresh_token']
            
        else:
            print(f"❌ Error al obtener tokens: {response.status_code}")
            print(f"Respuesta: {response.text}")
            return None
            
    except Exception as e:
        print(f"❌ Error durante el intercambio de tokens: {e}")
        return None

def test_connection():
    """Prueba la conexión con OneDrive usando los tokens guardados"""
    try:
        with open("onedrive_tokens.json", "r") as f:
            token_info = json.load(f)
        
        # Probar acceso a OneDrive
        headers = {
            "Authorization": f"Bearer {token_info['access_token']}"
        }
        
        response = requests.get(
            "https://graph.microsoft.com/v1.0/me/drive/root",
            headers=headers
        )
        
        if response.status_code == 200:
            print("✓ Conexión con OneDrive exitosa!")
            data = response.json()
            print(f"✓ Acceso a OneDrive de: {data.get('owner', {}).get('user', {}).get('displayName', 'Usuario')}")
            return True
        else:
            print(f"❌ Error en la conexión: {response.status_code}")
            print(f"Respuesta: {response.text}")
            return False
            
    except FileNotFoundError:
        print("❌ No se encontró el archivo 'onedrive_tokens.json'")
        print("Ejecuta primero get_refresh_token()")
        return False
    except Exception as e:
        print(f"❌ Error al probar la conexión: {e}")
        return False

if __name__ == "__main__":
    print("Microsoft OneDrive Token Generator")
    print("="*40)
    
    choice = input("¿Qué quieres hacer?\n1. Obtener refresh token\n2. Probar conexión\nElige (1 o 2): ")
    
    if choice == "1":
        get_refresh_token()
    elif choice == "2":
        test_connection()
    else:
        print("Opción no válida")
