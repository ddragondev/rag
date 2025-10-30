#!/usr/bin/env python3
"""
Test rápido para la categoría compliance
"""
import requests
import json

BASE_URL = "http://localhost:8000"

def test_compliance():
    print("\n" + "="*70)
    print("  TEST: Categoría Compliance")
    print("="*70 + "\n")
    
    payload = {
        "category": "compliance",
        "question": "¿Qué es compliance?",
        "format": "plain"
    }
    
    print(f"📤 Request:")
    print(json.dumps(payload, indent=2, ensure_ascii=False))
    print(f"\n🔄 Enviando solicitud...")
    
    try:
        response = requests.post(
            f"{BASE_URL}/ask",
            json=payload,
            timeout=120
        )
        
        print(f"\n📊 Status Code: {response.status_code}")
        
        if response.status_code == 200:
            data = response.json()
            print(f"\n✅ Respuesta exitosa!\n")
            print("="*70)
            print("RESPUESTA:")
            print("="*70)
            print(data.get('answer_plain', 'No disponible'))
            print("\n" + "="*70)
            print("FUENTES:")
            print("="*70)
            print(data.get('sources_plain', 'No disponible'))
            print("\n" + "="*70)
            
        else:
            print(f"\n❌ Error en la respuesta:")
            print(json.dumps(response.json(), indent=2, ensure_ascii=False))
            
    except requests.exceptions.Timeout:
        print("\n❌ Timeout: La solicitud tardó demasiado")
    except requests.exceptions.ConnectionError:
        print("\n❌ Error de conexión: El servidor no está disponible")
        print("💡 Asegúrate de que el servidor esté corriendo:")
        print("   uvicorn main:app --reload")
    except Exception as e:
        print(f"\n❌ Error inesperado: {e}")

if __name__ == "__main__":
    test_compliance()
