#!/usr/bin/env python3
"""
Ejemplo rápido: Mostrar la diferencia entre HTML y texto plano
"""
import requests
import json

def quick_test():
    print("\n" + "="*80)
    print("  EJEMPLO RÁPIDO: HTML vs TEXTO PLANO")
    print("="*80 + "\n")
    
    url = "http://localhost:8000/ask"
    payload = {
        "question": "¿Qué es el RMR en mecánica de rocas?",
        "category": "geomecanica"
    }
    
    print(f"🔍 Pregunta: {payload['question']}\n")
    print("⏳ Consultando API...\n")
    
    try:
        response = requests.post(url, json=payload, timeout=120)
        
        if response.status_code != 200:
            print(f"❌ Error {response.status_code}")
            return
        
        data = response.json()
        
        # Mostrar respuesta en TEXTO PLANO
        print("┌" + "─"*78 + "┐")
        print("│" + " "*25 + "📝 TEXTO PLANO" + " "*40 + "│")
        print("└" + "─"*78 + "┘\n")
        print(data.get('answer_plain', 'No disponible'))
        
        print("\n\n")
        
        # Mostrar respuesta en HTML
        print("┌" + "─"*78 + "┐")
        print("│" + " "*28 + "🌐 HTML" + " "*43 + "│")
        print("└" + "─"*78 + "┘\n")
        print(data.get('answer', 'No disponible'))
        
        print("\n\n")
        
        # Mostrar fuentes en TEXTO PLANO
        print("┌" + "─"*78 + "┐")
        print("│" + " "*25 + "📚 FUENTES" + " "*43 + "│")
        print("└" + "─"*78 + "┘\n")
        print(data.get('sources_plain', 'No disponible'))
        
        print("\n" + "="*80)
        print("✅ Ambos formatos disponibles!")
        print("="*80 + "\n")
        
    except requests.exceptions.RequestException as e:
        print(f"❌ Error de conexión: {e}")
        print("\n💡 Asegúrate de que el servidor esté corriendo:")
        print("   uvicorn main:app --reload")

if __name__ == "__main__":
    quick_test()
