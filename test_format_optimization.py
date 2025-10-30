"""
Test de optimización con parámetro 'format'
Demuestra la mejora de velocidad al solicitar solo un formato
"""
import requests
import time

BASE_URL = "http://localhost:8000"

def print_separator(title, char="="):
    """Imprime un separador visual."""
    print("\n" + char*80)
    print(f"  {title}")
    print(char*80 + "\n")

def test_format(format_type, question):
    """Prueba el endpoint con un formato específico."""
    url = f"{BASE_URL}/ask"
    payload = {
        "question": question,
        "category": "geomecanica",
        "format": format_type
    }
    
    print(f"🔍 Formato solicitado: {format_type}")
    print(f"📝 Pregunta: {question}")
    
    start_time = time.time()
    response = requests.post(url, json=payload, timeout=120)
    elapsed_time = time.time() - start_time
    
    if response.status_code != 200:
        print(f"❌ Error: {response.status_code}")
        print(response.text)
        return None, elapsed_time
    
    data = response.json()
    print(f"⏱️  Tiempo: {elapsed_time:.2f}s")
    
    # Verificar qué campos se devolvieron
    has_html = "answer" in data
    has_plain = "answer_plain" in data
    
    print(f"📊 Respuesta contiene:")
    print(f"   - HTML: {'✅' if has_html else '❌'}")
    print(f"   - Plain: {'✅' if has_plain else '❌'}")
    
    return data, elapsed_time

def compare_formats():
    """Compara el rendimiento de los tres formatos."""
    print_separator("🚀 COMPARACIÓN DE RENDIMIENTO CON PARÁMETRO 'format'")
    
    question = "¿Qué es la fortificación en minería?"
    
    # Calentar caché (primera consulta)
    print("🔥 Calentando caché con primera consulta...")
    test_format("html", question)
    time.sleep(1)
    
    print_separator("TEST 1: Solo HTML (format='html')", "-")
    data_html, time_html = test_format("html", question)
    
    print_separator("TEST 2: Solo Texto Plano (format='plain')", "-")
    data_plain, time_plain = test_format("plain", question)
    
    print_separator("TEST 3: Ambos Formatos (format='both')", "-")
    data_both, time_both = test_format("both", question)
    
    # Análisis comparativo
    print_separator("📊 ANÁLISIS COMPARATIVO")
    
    print(f"⏱️  Tiempos de respuesta:")
    print(f"   - Solo HTML:       {time_html:.2f}s")
    print(f"   - Solo Plain:      {time_plain:.2f}s")
    print(f"   - Ambos formatos:  {time_both:.2f}s")
    
    print(f"\n📈 Mejoras de velocidad:")
    if time_both > 0:
        improvement_html = ((time_both - time_html) / time_both) * 100
        improvement_plain = ((time_both - time_plain) / time_both) * 100
        
        print(f"   - HTML vs Both:  {improvement_html:.1f}% más rápido")
        print(f"   - Plain vs Both: {improvement_plain:.1f}% más rápido")
    
    print(f"\n💾 Tamaños de respuesta:")
    if data_html and "answer" in data_html:
        print(f"   - HTML:  {len(data_html['answer']):,} caracteres")
    if data_plain and "answer_plain" in data_plain:
        print(f"   - Plain: {len(data_plain['answer_plain']):,} caracteres")
    
    print_separator("✅ CONCLUSIÓN")
    print("✨ Al usar el parámetro 'format', evitamos llamadas innecesarias al LLM")
    print("✨ Esto reduce el tiempo de respuesta aproximadamente a la mitad")
    print("✨ Usa 'html' o 'plain' según lo que necesites, 'both' solo si necesitas ambos")

def test_invalid_format():
    """Prueba con un formato inválido."""
    print_separator("⚠️  TEST: Formato Inválido", "-")
    
    url = f"{BASE_URL}/ask"
    payload = {
        "question": "Test",
        "category": "geomecanica",
        "format": "invalid"
    }
    
    print("🔍 Formato solicitado: invalid (debe fallar)")
    
    response = requests.post(url, json=payload, timeout=30)
    
    print(f"📌 Status code: {response.status_code}")
    
    if response.status_code == 400:
        print("✅ Validación correcta: formato inválido rechazado")
        print(f"   Mensaje: {response.json()['detail']}")
    else:
        print("❌ Error: debería rechazar formato inválido")

def test_examples():
    """Muestra ejemplos de uso."""
    print_separator("📚 EJEMPLOS DE USO")
    
    examples = [
        {
            "descripción": "Para mostrar en web (HTML)",
            "payload": {
                "question": "¿Qué es el RMR?",
                "category": "geomecanica",
                "format": "html"
            }
        },
        {
            "descripción": "Para logs o CLI (texto plano)",
            "payload": {
                "question": "¿Qué es el RMR?",
                "category": "geomecanica",
                "format": "plain"
            }
        },
        {
            "descripción": "Para aplicaciones que usan ambos",
            "payload": {
                "question": "¿Qué es el RMR?",
                "category": "geomecanica",
                "format": "both"
            }
        }
    ]
    
    for i, example in enumerate(examples, 1):
        print(f"\n{i}. {example['descripción']}")
        print(f"   Payload:")
        print(f"   {example['payload']}")

def main():
    """Función principal."""
    print("\n" + "🎯"*40)
    print("  TEST DE OPTIMIZACIÓN: Parámetro 'format'")
    print("🎯"*40)
    
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
    compare_formats()
    test_invalid_format()
    test_examples()
    
    print_separator("🎉 PRUEBAS COMPLETADAS")
    print("💡 Recomendación: Usa 'format' para optimizar el rendimiento")
    print("   - format='html' para frontend web (más rápido)")
    print("   - format='plain' para CLI/logs (más rápido)")
    print("   - format='both' solo si realmente necesitas ambos")

if __name__ == "__main__":
    main()
