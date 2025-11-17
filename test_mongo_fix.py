#!/usr/bin/env python3
"""
Script rápido para verificar que MongoDB se inicializa correctamente
"""

import requests

BASE_URL = "http://localhost:8000"

print("🔍 Verificando MongoDB...")

# 1. Health check
response = requests.get(f"{BASE_URL}/health")
print(f"Health: {response.status_code} - {response.json()}")

# 2. MongoDB health
response = requests.get(f"{BASE_URL}/mongodb/health")
print(f"MongoDB Health: {response.status_code} - {response.json()}")

# 3. Test /ask sin auth
payload = {
    "question": "¿Qué es la geomecánica?",
    "category": "geomecanica",
    "format": "plain"
}

print("\n📤 Probando /ask...")
response = requests.post(f"{BASE_URL}/ask", json=payload)
print(f"Status: {response.status_code}")

if response.status_code == 200:
    data = response.json()
    print(f"✅ Funciona!")
    print(f"   Pregunta: {data['question']}")
    print(f"   Respuesta: {data.get('answer_plain', '')[:100]}...")
else:
    print(f"❌ Error: {response.json()}")
