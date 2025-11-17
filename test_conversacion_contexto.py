#!/usr/bin/env python3
"""
Script para probar que el contexto conversacional funciona correctamente
"""

import requests
import time

BASE_URL = "http://localhost:8000"

# Obtén tu token de Clerk desde el frontend
print("="*60)
print("🧪 TEST DE CONTEXTO CONVERSACIONAL")
print("="*60)

TOKEN = input("\n🔐 Pega tu token JWT de Clerk (o Enter para omitir): ").strip()

if not TOKEN:
    print("\n⚠️ Sin token, usando session_id temporal")
    SESSION_ID = f"test_{int(time.time())}"
    headers = {
        "Content-Type": "application/json"
    }
    use_session_id = True
else:
    print("\n✅ Usando autenticación con Clerk")
    headers = {
        "Content-Type": "application/json",
        "Authorization": f"Bearer {TOKEN}"
    }
    use_session_id = False

print("\n" + "="*60)
print("📝 CONVERSACIÓN DE PRUEBA")
print("="*60)

# Pregunta 1
print("\n👤 Usuario: ¿Qué es compliance?")
payload1 = {
    "question": "¿Qué es compliance?",
    "category": "compliance",
    "format": "plain"
}
if use_session_id:
    payload1["session_id"] = SESSION_ID

response1 = requests.post(f"{BASE_URL}/ask", json=payload1, headers=headers)
if response1.status_code == 200:
    data1 = response1.json()
    print(f"🤖 Asistente: {data1['answer_plain'][:200]}...")
    print(f"\n📊 session_id: {data1.get('session_id', 'N/A')}")
else:
    print(f"❌ Error: {response1.status_code} - {response1.text}")
    exit(1)

time.sleep(1)

# Pregunta 2 - Requiere contexto
print("\n👤 Usuario: ¿Qué me dijiste recién?")
payload2 = {
    "question": "¿Qué me dijiste recién?",
    "category": "compliance",
    "format": "plain"
}
if use_session_id:
    payload2["session_id"] = SESSION_ID

response2 = requests.post(f"{BASE_URL}/ask", json=payload2, headers=headers)
if response2.status_code == 200:
    data2 = response2.json()
    answer2 = data2['answer_plain']
    print(f"🤖 Asistente: {answer2[:300]}...")
    
    # Verificar si tiene contexto
    print("\n" + "="*60)
    print("🔍 ANÁLISIS DE CONTEXTO")
    print("="*60)
    
    # Buscar palabras clave de la primera respuesta en la segunda
    keywords = ["compliance", "cumplimiento", "leyes", "regulaciones", "políticas"]
    found_keywords = [kw for kw in keywords if kw.lower() in answer2.lower()]
    
    if len(found_keywords) >= 2:
        print("✅ La respuesta tiene contexto (menciona conceptos de la pregunta anterior)")
        print(f"   Palabras clave encontradas: {', '.join(found_keywords)}")
    else:
        print("❌ La respuesta NO parece tener contexto")
        print("   Es muy genérica o no hace referencia a la conversación previa")
    
    # Verificar si es una respuesta genérica
    generic_phrases = [
        "estoy aquí para ayudarte",
        "consulta específica",
        "no dudes en preguntar"
    ]
    is_generic = any(phrase in answer2.lower() for phrase in generic_phrases)
    
    if is_generic:
        print("⚠️ La respuesta parece ser el saludo genérico (sin contexto real)")
    
else:
    print(f"❌ Error: {response2.status_code} - {response2.text}")
    exit(1)

time.sleep(1)

# Pregunta 3 - Continuación
print("\n👤 Usuario: ¿Me lo puedes explicar de otra forma?")
payload3 = {
    "question": "¿Me lo puedes explicar de otra forma?",
    "category": "compliance",
    "format": "plain"
}
if use_session_id:
    payload3["session_id"] = SESSION_ID

response3 = requests.post(f"{BASE_URL}/ask", json=payload3, headers=headers)
if response3.status_code == 200:
    data3 = response3.json()
    answer3 = data3['answer_plain']
    print(f"🤖 Asistente: {answer3[:300]}...")
    
    # Verificar contexto
    if len([kw for kw in keywords if kw.lower() in answer3.lower()]) >= 2:
        print("\n✅ Mantiene el contexto en la tercera pregunta")
    else:
        print("\n❌ Perdió el contexto en la tercera pregunta")
else:
    print(f"❌ Error: {response3.status_code} - {response3.text}")

print("\n" + "="*60)
print("✅ TEST COMPLETADO")
print("="*60)
print("\n💡 Revisa los logs del servidor para ver:")
print("   - 🔍 DEBUG: historial tiene X mensajes")
print("   - 💾 Guardado: user/assistant en session...")
print("   - 🤖 DEBUG: Prompt tiene X chars, historial incluido: True")
print()
