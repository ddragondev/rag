"""
Script de prueba para verificar las respuestas en HTML y texto plano
"""
import requests
import json
import time

# Configuración
BASE_URL = "http://localhost:8000"

def print_separator(title):
    """Imprime un separador visual."""
    print("\n" + "="*80)
    print(f"  {title}")
    print("="*80 + "\n")

def test_ask_endpoint():
    """Prueba el endpoint /ask con respuestas en HTML y texto plano."""
    print_separator("TEST: Endpoint /ask (Respuesta completa)")
    
    url = f"{BASE_URL}/ask"
    payload = {
        "question": "¿Qué es la fortificación en minería?",
        "category": "geomecanica"
    }
    
    print(f"📤 Enviando pregunta: {payload['question']}")
    print(f"📁 Categoría: {payload['category']}")
    
    start_time = time.time()
    response = requests.post(url, json=payload, timeout=120)
    elapsed_time = time.time() - start_time
    
    if response.status_code != 200:
        print(f"❌ Error: {response.status_code}")
        print(response.text)
        return None
    
    data = response.json()
    
    print(f"\n⏱️  Tiempo de respuesta: {elapsed_time:.2f}s")
    print(f"\n📊 Estadísticas:")
    print(f"   - HTML length: {len(data.get('answer', ''))} caracteres")
    print(f"   - Plain text length: {len(data.get('answer_plain', ''))} caracteres")
    
    # Mostrar respuesta en texto plano
    print_separator("RESPUESTA EN TEXTO PLANO")
    print(data.get('answer_plain', 'No disponible'))
    
    # Mostrar fuentes en texto plano
    print_separator("FUENTES (Texto Plano)")
    print(data.get('sources_plain', 'No disponible'))
    
    # Mostrar respuesta en HTML (primeros 500 caracteres)
    print_separator("RESPUESTA EN HTML (Preview)")
    html_preview = data.get('answer', 'No disponible')[:500]
    print(html_preview)
    if len(data.get('answer', '')) > 500:
        print(f"\n... (+ {len(data['answer']) - 500} caracteres más)")
    
    # Mostrar fuentes en HTML
    print_separator("FUENTES (HTML)")
    print(data.get('sources', 'No disponible'))
    
    return data

def test_comparison():
    """Compara ambos formatos de respuesta."""
    print_separator("COMPARACIÓN DE FORMATOS")
    
    url = f"{BASE_URL}/ask"
    payload = {
        "question": "¿Qué es el RMR?",
        "category": "geomecanica"
    }
    
    print(f"Pregunta de prueba: {payload['question']}\n")
    
    response = requests.post(url, json=payload, timeout=120)
    if response.status_code != 200:
        print(f"❌ Error: {response.status_code}")
        return
    
    data = response.json()
    
    # Análisis
    html_size = len(data.get('answer', ''))
    plain_size = len(data.get('answer_plain', ''))
    size_diff = html_size - plain_size
    percentage = (size_diff / html_size * 100) if html_size > 0 else 0
    
    print(f"📏 Tamaño HTML:        {html_size:,} caracteres")
    print(f"📏 Tamaño Texto Plano: {plain_size:,} caracteres")
    print(f"📉 Diferencia:         {size_diff:,} caracteres ({percentage:.1f}% overhead)")
    
    # Verificar contenido
    print(f"\n✅ Tiene respuesta HTML: {'Sí' if data.get('answer') else 'No'}")
    print(f"✅ Tiene respuesta Plain: {'Sí' if data.get('answer_plain') else 'No'}")
    print(f"✅ Tiene fuentes HTML: {'Sí' if data.get('sources') else 'No'}")
    print(f"✅ Tiene fuentes Plain: {'Sí' if data.get('sources_plain') else 'No'}")

def test_categories():
    """Lista las categorías disponibles."""
    print_separator("CATEGORÍAS DISPONIBLES")
    
    url = f"{BASE_URL}/categories"
    response = requests.get(url)
    
    if response.status_code == 200:
        data = response.json()
        categories = data.get('categories', [])
        
        if categories:
            print("📚 Categorías encontradas:")
            for cat in categories:
                print(f"   • {cat}")
        else:
            print("⚠️  No se encontraron categorías")
    else:
        print(f"❌ Error: {response.status_code}")

def main():
    """Función principal."""
    print("\n" + "🚀"*40)
    print("  PRUEBA DE RESPUESTAS HTML Y TEXTO PLANO")
    print("🚀"*40)
    
    try:
        # Verificar que el servidor está corriendo
        response = requests.get(f"{BASE_URL}/", timeout=5)
        if response.status_code != 200:
            print("❌ El servidor no está respondiendo correctamente")
            return
    except requests.exceptions.RequestException:
        print("❌ No se puede conectar al servidor")
        print("💡 Asegúrate de que el servidor esté corriendo:")
        print("   uvicorn main:app --reload")
        return
    
    # Ejecutar pruebas
    test_categories()
    test_ask_endpoint()
    test_comparison()
    
    print_separator("✅ PRUEBAS COMPLETADAS")
    print("💡 Revisa los resultados arriba para verificar que ambos formatos funcionan correctamente.")

if __name__ == "__main__":
    main()
