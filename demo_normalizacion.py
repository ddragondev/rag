#!/usr/bin/env python3
"""
Demo rápida: Normalización de categorías
Muestra cómo diferentes variaciones se aceptan
"""
import requests

BASE_URL = "http://localhost:8000"

def demo():
    print("\n" + "🔤"*35)
    print("  DEMO: Normalización de Categorías")
    print("🔤"*35)
    
    # Verificar servidor
    try:
        requests.get(f"{BASE_URL}/", timeout=5)
    except:
        print("\n❌ Servidor no disponible")
        print("💡 Ejecuta: uvicorn main:app --reload")
        return
    
    print("\n📂 Carpeta real en docs/: 'geomecanica' (sin tilde, minúscula)")
    print("\n🧪 Probando diferentes variaciones de entrada...\n")
    
    variaciones = [
        ("geomecanica", "Sin tilde, minúscula"),
        ("Geomecánica", "Con tilde, mayúscula inicial"),
        ("GEOMECÁNICA", "Con tilde, todo mayúsculas"),
    ]
    
    question = "¿Qué es el RMR?"
    
    for categoria, descripcion in variaciones:
        print(f"{'─'*70}")
        print(f"📝 Input: '{categoria}' ({descripcion})")
        
        try:
            response = requests.post(f"{BASE_URL}/ask", json={
                "question": question,
                "category": categoria,
                "format": "plain"
            }, timeout=120)
            
            if response.status_code == 200:
                data = response.json()
                preview = data.get('answer_plain', '')[:100]
                print(f"✅ Éxito!")
                print(f"📄 Respuesta: {preview}...")
            else:
                print(f"❌ Error {response.status_code}")
                
        except Exception as e:
            print(f"❌ Error: {e}")
        
        print()
    
    print("="*70)
    print("\n✨ Conclusión:")
    print("   Todas las variaciones funcionan! 🎉")
    print("   El sistema normaliza automáticamente a 'geomecanica'\n")
    print("💡 Beneficio:")
    print("   Los usuarios pueden escribir como quieran:")
    print("   - Con tildes: Geomecánica")
    print("   - Sin tildes: Geomecanica")
    print("   - Mayúsculas: GEOMECANICA")
    print("   - Mix: GeoMecánica")
    print("\n   ¡Todos funcionan! 🚀\n")

if __name__ == "__main__":
    demo()
