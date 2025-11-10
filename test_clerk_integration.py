#!/usr/bin/env python3
"""
Script de prueba para verificar la integración con Clerk
"""

import requests
import json

BASE_URL = "http://localhost:8000"

def test_without_auth():
    """Probar sin autenticación - Usuario anónimo"""
    print("\n" + "="*60)
    print("🧪 TEST 1: Usuario Anónimo (sin token)")
    print("="*60)
    
    payload = {
        "question": "¿Qué es la geomecánica?",
        "category": "geomecanica",
        "format": "plain"
    }
    
    response = requests.post(f"{BASE_URL}/ask", json=payload)
    
    if response.status_code == 200:
        data = response.json()
        print("✅ Pregunta procesada correctamente")
        print(f"📝 Pregunta: {data['question']}")
        print(f"🤖 Respuesta: {data['answer_plain'][:200]}...")
        print(f"🔑 Session ID: {data.get('session_id', 'Sin sesión')}")
        print(f"🔐 Autenticado: {data.get('authenticated', False)}")
    else:
        print(f"❌ Error: {response.status_code}")
        print(response.text)


def test_with_auth(token):
    """Probar con autenticación - Usuario logueado"""
    print("\n" + "="*60)
    print("🧪 TEST 2: Usuario Autenticado (con token)")
    print("="*60)
    
    headers = {
        "Authorization": f"Bearer {token}"
    }
    
    payload = {
        "question": "¿Cuáles son los principales tipos de rocas?",
        "category": "geomecanica",
        "format": "plain"
    }
    
    response = requests.post(f"{BASE_URL}/ask", json=payload, headers=headers)
    
    if response.status_code == 200:
        data = response.json()
        print("✅ Pregunta procesada correctamente")
        print(f"📝 Pregunta: {data['question']}")
        print(f"🤖 Respuesta: {data['answer_plain'][:200]}...")
        print(f"🔑 Session ID: {data.get('session_id', 'Sin sesión')}")
        print(f"🔐 Autenticado: {data.get('authenticated', False)}")
        print(f"📧 Email: {data.get('user_email', 'N/A')}")
        print(f"👤 User ID: {data.get('user_id', 'N/A')}")
    else:
        print(f"❌ Error: {response.status_code}")
        print(response.text)


def test_get_history(token):
    """Probar obtención de historial"""
    print("\n" + "="*60)
    print("🧪 TEST 3: Obtener Historial del Usuario")
    print("="*60)
    
    headers = {
        "Authorization": f"Bearer {token}"
    }
    
    response = requests.get(f"{BASE_URL}/my-history?limit=10", headers=headers)
    
    if response.status_code == 200:
        data = response.json()
        print("✅ Historial obtenido correctamente")
        print(f"📧 Usuario: {data['user_email']}")
        print(f"📊 Total mensajes: {data['total_messages']}")
        print(f"\n📜 Últimos mensajes:")
        
        for msg in data['history'][:5]:  # Mostrar últimos 5
            role_icon = "👤" if msg['role'] == 'user' else "🤖"
            print(f"\n{role_icon} {msg['role'].upper()}:")
            print(f"   {msg['content'][:150]}...")
            print(f"   ⏰ {msg['timestamp']}")
    else:
        print(f"❌ Error: {response.status_code}")
        print(response.text)


def test_get_conversations(token):
    """Probar listado de conversaciones"""
    print("\n" + "="*60)
    print("🧪 TEST 4: Listar Conversaciones del Usuario")
    print("="*60)
    
    headers = {
        "Authorization": f"Bearer {token}"
    }
    
    response = requests.get(f"{BASE_URL}/my-conversations", headers=headers)
    
    if response.status_code == 200:
        data = response.json()
        print("✅ Conversaciones obtenidas correctamente")
        print(f"📧 Usuario: {data['user_email']}")
        print(f"💬 Total conversaciones: {data['total']}")
        
        for conv in data['conversations'][:3]:  # Mostrar primeras 3
            print(f"\n📝 Session: {conv['session_id']}")
            print(f"   📊 Mensajes: {conv['message_count']}")
            print(f"   📅 Creado: {conv['created_at']}")
            print(f"   🕐 Actualizado: {conv['updated_at']}")
            print(f"   💬 Último: {conv['last_message']}")
    else:
        print(f"❌ Error: {response.status_code}")
        print(response.text)


def test_health():
    """Probar endpoint de salud"""
    print("\n" + "="*60)
    print("🧪 TEST 0: Health Check")
    print("="*60)
    
    try:
        response = requests.get(f"{BASE_URL}/health")
        if response.status_code == 200:
            print("✅ Servidor funcionando correctamente")
            print(f"📊 Respuesta: {response.json()}")
        else:
            print(f"⚠️ Servidor respondió con código: {response.status_code}")
    except requests.exceptions.ConnectionError:
        print("❌ No se puede conectar al servidor")
        print("💡 Asegúrate de que el servidor esté corriendo:")
        print("   uvicorn main:app --reload")
        return False
    
    return True


if __name__ == "__main__":
    print("\n" + "="*60)
    print("🚀 PRUEBAS DE INTEGRACIÓN CLERK + RAG")
    print("="*60)
    
    # Verificar que el servidor esté corriendo
    if not test_health():
        exit(1)
    
    # Test 1: Sin autenticación
    test_without_auth()
    
    # Test 2-4: Con autenticación
    print("\n" + "="*60)
    print("🔑 PRUEBAS CON AUTENTICACIÓN")
    print("="*60)
    print("\nPara probar con autenticación necesitas un token JWT de Clerk.")
    print("\nOpciones:")
    print("1. Obtener token desde tu aplicación frontend")
    print("2. Usar Clerk Dashboard → API Keys → Generate JWT")
    print("3. Pegar un token aquí manualmente")
    
    token = input("\n🔐 Ingresa tu token JWT de Clerk (o Enter para omitir): ").strip()
    
    if token:
        test_with_auth(token)
        test_get_history(token)
        test_get_conversations(token)
    else:
        print("\n⏭️  Omitiendo pruebas con autenticación")
    
    print("\n" + "="*60)
    print("✅ Pruebas completadas")
    print("="*60)
    print("\n💡 Próximos pasos:")
    print("1. Implementar frontend con Clerk (ver FRONTEND_HISTORIAL_USUARIO.md)")
    print("2. Probar flujo completo desde el navegador")
    print("3. Verificar que cada usuario ve solo su historial")
    print()
