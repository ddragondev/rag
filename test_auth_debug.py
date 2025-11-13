#!/usr/bin/env python3
"""
Script de diagnóstico para depurar problemas de autenticación con Clerk
"""

import requests
import json
import os
from dotenv import load_dotenv

load_dotenv()

BASE_URL = "http://localhost:8000"

def test_health():
    """Test básico de salud del servidor"""
    print("\n" + "="*60)
    print("🏥 TEST: Health Check")
    print("="*60)
    
    try:
        # Probar endpoint raíz primero
        response = requests.get(f"{BASE_URL}/")
        print(f"Status: {response.status_code}")
        if response.status_code == 200:
            print(f"✅ Servidor funcionando correctamente")
            return True
        else:
            print(f"Response: {response.text[:200]}")
            return True  # Servidor responde aunque sea con otro código
    except Exception as e:
        print(f"❌ Error: {e}")
        return False


def test_ask_without_auth():
    """Test /ask sin autenticación"""
    print("\n" + "="*60)
    print("🧪 TEST: /ask SIN autenticación")
    print("="*60)
    
    payload = {
        "question": "test question",
        "category": "geomecanica",
        "format": "plain"
    }
    
    try:
        response = requests.post(f"{BASE_URL}/ask", json=payload)
        print(f"Status: {response.status_code}")
        
        if response.status_code == 200:
            data = response.json()
            print(f"✅ Funciona sin auth")
            print(f"   authenticated: {data.get('authenticated', False)}")
            print(f"   session_id: {data.get('session_id', 'None')}")
        else:
            print(f"❌ Error: {response.text}")
    except Exception as e:
        print(f"❌ Error: {e}")


def test_ask_with_auth(token):
    """Test /ask con autenticación"""
    print("\n" + "="*60)
    print("🧪 TEST: /ask CON autenticación")
    print("="*60)
    
    headers = {
        "Authorization": f"Bearer {token}",
        "Content-Type": "application/json"
    }
    
    payload = {
        "question": "test question with auth",
        "category": "geomecanica",
        "format": "plain"
    }
    
    try:
        response = requests.post(f"{BASE_URL}/ask", json=payload, headers=headers)
        print(f"Status: {response.status_code}")
        
        if response.status_code == 200:
            data = response.json()
            print(f"✅ Funciona con auth")
            print(f"   authenticated: {data.get('authenticated', False)}")
            print(f"   user_id: {data.get('user_id', 'None')}")
            print(f"   user_email: {data.get('user_email', 'None')}")
        else:
            print(f"❌ Error: {response.text}")
    except Exception as e:
        print(f"❌ Error: {e}")


def test_my_history(token):
    """Test /my-history con autenticación"""
    print("\n" + "="*60)
    print("🧪 TEST: /my-history CON autenticación")
    print("="*60)
    
    headers = {
        "Authorization": f"Bearer {token}"
    }
    
    try:
        response = requests.get(f"{BASE_URL}/my-history", headers=headers)
        print(f"Status: {response.status_code}")
        print(f"Headers enviados: {headers}")
        
        if response.status_code == 200:
            data = response.json()
            print(f"✅ Funciona correctamente")
            print(f"   user_email: {data.get('user_email', 'None')}")
            print(f"   total_messages: {data.get('total_messages', 0)}")
        elif response.status_code == 401:
            print(f"❌ Error 401: No autenticado")
            print(f"Response: {response.text}")
            print(f"\n🔍 Debugging:")
            print(f"   Token length: {len(token)}")
            print(f"   Token start: {token[:50]}...")
            print(f"   Token end: ...{token[-50:]}")
        else:
            print(f"❌ Error {response.status_code}: {response.text}")
    except Exception as e:
        print(f"❌ Error: {e}")


def test_my_conversations(token):
    """Test /my-conversations con autenticación"""
    print("\n" + "="*60)
    print("🧪 TEST: /my-conversations CON autenticación")
    print("="*60)
    
    headers = {
        "Authorization": f"Bearer {token}"
    }
    
    try:
        response = requests.get(f"{BASE_URL}/my-conversations", headers=headers)
        print(f"Status: {response.status_code}")
        
        if response.status_code == 200:
            data = response.json()
            print(f"✅ Funciona correctamente")
            print(f"   user_email: {data.get('user_email', 'None')}")
            print(f"   total: {data.get('total', 0)}")
        elif response.status_code == 401:
            print(f"❌ Error 401: No autenticado")
            print(f"Response: {response.text}")
        else:
            print(f"❌ Error {response.status_code}: {response.text}")
    except Exception as e:
        print(f"❌ Error: {e}")


def verify_clerk_config():
    """Verificar configuración de Clerk"""
    print("\n" + "="*60)
    print("🔍 VERIFICACIÓN: Configuración de Clerk")
    print("="*60)
    
    pub_key = os.getenv("CLERK_PUBLISHABLE_KEY")
    secret_key = os.getenv("CLERK_SECRET_KEY")
    
    print(f"CLERK_PUBLISHABLE_KEY: {'✅ Configurada' if pub_key else '❌ NO configurada'}")
    if pub_key:
        print(f"   Valor: {pub_key[:20]}...{pub_key[-10:]}")
    
    print(f"CLERK_SECRET_KEY: {'✅ Configurada' if secret_key else '❌ NO configurada'}")
    if secret_key:
        print(f"   Valor: {secret_key[:20]}...{secret_key[-10:]}")
    
    return bool(pub_key and secret_key)


def decode_jwt_manually(token):
    """Decodificar JWT manualmente para ver su contenido"""
    print("\n" + "="*60)
    print("🔍 ANÁLISIS: Contenido del JWT")
    print("="*60)
    
    try:
        import base64
        
        # Dividir el token
        parts = token.split('.')
        if len(parts) != 3:
            print(f"❌ Token mal formado (debe tener 3 partes, tiene {len(parts)})")
            return
        
        # Decodificar header
        header = parts[0]
        # Agregar padding si es necesario
        header += '=' * (4 - len(header) % 4)
        header_decoded = base64.urlsafe_b64decode(header)
        print(f"📋 Header:")
        print(f"   {json.loads(header_decoded)}")
        
        # Decodificar payload
        payload = parts[1]
        payload += '=' * (4 - len(payload) % 4)
        payload_decoded = base64.urlsafe_b64decode(payload)
        payload_json = json.loads(payload_decoded)
        
        print(f"\n📦 Payload:")
        print(f"   sub (user_id): {payload_json.get('sub', 'NO ENCONTRADO')}")
        print(f"   email: {payload_json.get('email', 'NO ENCONTRADO')}")
        print(f"   iss (issuer): {payload_json.get('iss', 'NO ENCONTRADO')}")
        print(f"   exp (expiration): {payload_json.get('exp', 'NO ENCONTRADO')}")
        print(f"   iat (issued at): {payload_json.get('iat', 'NO ENCONTRADO')}")
        
        # Verificar expiración
        import time
        exp = payload_json.get('exp')
        if exp:
            if time.time() > exp:
                print(f"   ⚠️ TOKEN EXPIRADO!")
            else:
                remaining = exp - time.time()
                print(f"   ✅ Token válido por {int(remaining/60)} minutos más")
        
        print(f"\n📄 Payload completo:")
        print(f"   {json.dumps(payload_json, indent=2)}")
        
    except Exception as e:
        print(f"❌ Error al decodificar: {e}")


if __name__ == "__main__":
    print("\n" + "="*60)
    print("🚀 DIAGNÓSTICO DE AUTENTICACIÓN CLERK")
    print("="*60)
    
    # 1. Verificar servidor
    if not test_health():
        print("\n❌ El servidor no responde. Verifica que esté corriendo.")
        exit(1)
    
    # 2. Verificar configuración
    if not verify_clerk_config():
        print("\n❌ Configuración de Clerk incompleta en .env")
        exit(1)
    
    # 3. Test sin auth
    test_ask_without_auth()
    
    # 4. Solicitar token
    print("\n" + "="*60)
    print("🔑 TOKEN JWT REQUERIDO")
    print("="*60)
    print("\nPara continuar con las pruebas de autenticación, necesitas un token JWT de Clerk.")
    print("\n📝 Cómo obtener el token:")
    print("1. Abre tu aplicación frontend")
    print("2. Abre las DevTools del navegador (F12)")
    print("3. Ve a la pestaña 'Console'")
    print("4. Ejecuta: await window.Clerk.session.getToken()")
    print("5. Copia el token y pégalo aquí")
    print("\nO desde React:")
    print("   const { getToken } = useAuth();")
    print("   const token = await getToken();")
    print("   console.log(token);")
    
    token = input("\n🔐 Pega tu token JWT aquí (o Enter para omitir): ").strip()
    
    if not token:
        print("\n⏭️  Omitiendo pruebas con autenticación")
        exit(0)
    
    # 5. Analizar token
    decode_jwt_manually(token)
    
    # 6. Test con auth
    test_ask_with_auth(token)
    test_my_history(token)
    test_my_conversations(token)
    
    print("\n" + "="*60)
    print("✅ DIAGNÓSTICO COMPLETADO")
    print("="*60)
    print("\n💡 Si /my-history y /my-conversations siguen dando 401:")
    print("1. Verifica que CLERK_PUBLISHABLE_KEY sea correcta")
    print("2. Verifica que el token no haya expirado")
    print("3. Verifica que el token sea del mismo proyecto Clerk")
    print("4. Revisa los logs del servidor para más detalles")
    print()
