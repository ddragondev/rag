#!/usr/bin/env python3
"""
Demo rápida del parámetro 'format'
Muestra las diferencias de tiempo y respuesta
"""
import requests
import time
import json

BASE_URL = "http://localhost:8000"

def test_format(format_type, title):
    """Prueba un formato específico."""
    print(f"\n{'='*70}")
    print(f"  {title}")
    print('='*70)
    
    payload = {
        "question": "¿Qué es la fortificación en minería?",
        "category": "geomecanica",
        "format": format_type
    }
    
    print(f"\n📤 Request:")
    print(f"   format: '{format_type}'")
    
    start = time.time()
    try:
        response = requests.post(f"{BASE_URL}/ask", json=payload, timeout=120)
        elapsed = time.time() - start
        
        if response.status_code != 200:
            print(f"\n❌ Error {response.status_code}: {response.text}")
            return
        
        data = response.json()
        
        print(f"\n⏱️  Tiempo: {elapsed:.2f}s")
        print(f"\n📦 Campos en respuesta:")
        for key in data.keys():
            if key in ['answer', 'answer_plain']:
                length = len(data[key])
                preview = data[key][:80].replace('\n', ' ')
                print(f"   ✅ {key}: {length} chars")
                print(f"      → {preview}...")
            elif key in ['sources', 'sources_plain']:
                print(f"   ✅ {key}")
            else:
                print(f"   ℹ️  {key}: {data[key]}")
        
    except requests.exceptions.RequestException as e:
        print(f"\n❌ Error de conexión: {e}")

def main():
    print("\n" + "🎯"*35)
    print("  DEMO: Parámetro 'format' - Optimización de Rendimiento")
    print("🎯"*35)
    
    # Verificar servidor
    try:
        requests.get(f"{BASE_URL}/", timeout=5)
    except:
        print("\n❌ Servidor no disponible en", BASE_URL)
        print("💡 Ejecuta: uvicorn main:app --reload")
        return
    
    # Probar cada formato
    test_format("html", "1️⃣  Solo HTML (para web)")
    time.sleep(0.5)
    
    test_format("plain", "2️⃣  Solo Texto Plano (para CLI/logs)")
    time.sleep(0.5)
    
    test_format("both", "3️⃣  Ambos Formatos (completo)")
    
    # Resumen
    print(f"\n{'='*70}")
    print("  💡 RESUMEN")
    print('='*70)
    print("""
✨ Beneficios del parámetro 'format':

1. format='html'  → ~50% más rápido que 'both'
   Úsalo para: Frontend web, emails HTML

2. format='plain' → ~50% más rápido que 'both'
   Úsalo para: CLI, logs, procesamiento de texto

3. format='both'  → Devuelve ambos formatos
   Úsalo solo cuando realmente necesites ambos

💰 Ahorro: 1 llamada al LLM = menos tiempo + menos costo
""")
    
    print("="*70)

if __name__ == "__main__":
    main()
