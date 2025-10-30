#!/usr/bin/env python3
"""
Script de prueba para comparar el rendimiento de la API optimizada
"""
import requests
import time
import json

BASE_URL = "http://localhost:8000"

def test_normal_endpoint():
    """Prueba el endpoint normal /ask"""
    print("\n" + "="*60)
    print("🧪 Probando endpoint /ask (respuesta completa)")
    print("="*60)
    
    payload = {
        "question": "¿Qué es la fortificación en minería?",
        "category": "geomecanica"
    }
    
    print(f"\n📤 Enviando pregunta: {payload['question']}")
    print(f"📁 Categoría: {payload['category']}")
    
    start = time.time()
    response = requests.post(f"{BASE_URL}/ask", json=payload)
    elapsed = time.time() - start
    
    if response.status_code == 200:
        data = response.json()
        print(f"\n✅ Respuesta recibida en {elapsed:.2f} segundos")
        print(f"\n📝 Respuesta (primeros 200 caracteres):")
        print(data['answer'][:200] + "...")
        print(f"\n📚 Fuentes:")
        print(data['sources'])
    else:
        print(f"\n❌ Error {response.status_code}: {response.text}")
    
    return elapsed


def test_stream_endpoint():
    """Prueba el endpoint con streaming /ask-stream"""
    print("\n" + "="*60)
    print("🌊 Probando endpoint /ask-stream (respuesta progresiva)")
    print("="*60)
    
    payload = {
        "question": "¿Qué es la fortificación en minería?",
        "category": "geomecanica"
    }
    
    print(f"\n📤 Enviando pregunta: {payload['question']}")
    print(f"📁 Categoría: {payload['category']}")
    
    start = time.time()
    first_chunk_time = None
    answer = ""
    sources = ""
    
    response = requests.post(f"{BASE_URL}/ask-stream", json=payload, stream=True)
    
    print(f"\n📥 Recibiendo respuesta en tiempo real...")
    print("-" * 60)
    
    for line in response.iter_lines():
        if line:
            line = line.decode('utf-8')
            if line.startswith('data: '):
                data = json.loads(line[6:])
                
                if data['type'] == 'metadata':
                    sources = data['sources']
                elif data['type'] == 'content':
                    if first_chunk_time is None:
                        first_chunk_time = time.time() - start
                        print(f"\n⚡ Primer chunk recibido en {first_chunk_time:.2f} segundos (TTFB)")
                        print("\n📝 Contenido:\n")
                    answer += data['content']
                    print(data['content'], end='', flush=True)
                elif data['type'] == 'done':
                    total_time = time.time() - start
                    print(f"\n\n✅ Respuesta completa en {total_time:.2f} segundos")
                    print(f"\n📚 Fuentes:")
                    print(sources)
                    return first_chunk_time, total_time


def test_categories():
    """Prueba el endpoint /categories"""
    print("\n" + "="*60)
    print("📂 Probando endpoint /categories")
    print("="*60)
    
    response = requests.get(f"{BASE_URL}/categories")
    
    if response.status_code == 200:
        data = response.json()
        print(f"\n✅ Categorías disponibles:")
        for cat in data['categories']:
            print(f"  - {cat}")
    else:
        print(f"\n❌ Error {response.status_code}: {response.text}")


def main():
    print("\n" + "🚀"*30)
    print("   PRUEBA DE RENDIMIENTO - API RAG OPTIMIZADA")
    print("🚀"*30)
    
    # Probar categorías
    test_categories()
    
    # Primera consulta (creará el cache)
    print("\n\n" + "💾"*30)
    print("   PRIMERA CONSULTA - Creando cache")
    print("💾"*30)
    time1 = test_normal_endpoint()
    
    # Segunda consulta (usará el cache)
    print("\n\n" + "⚡"*30)
    print("   SEGUNDA CONSULTA - Usando cache")
    print("⚡"*30)
    time2 = test_normal_endpoint()
    
    # Consulta con streaming
    print("\n\n" + "🌊"*30)
    print("   CONSULTA CON STREAMING - Usando cache")
    print("🌊"*30)
    ttfb, total = test_stream_endpoint()
    
    # Resumen
    print("\n\n" + "📊"*30)
    print("   RESUMEN DE RENDIMIENTO")
    print("📊"*30)
    print(f"\n📌 Primera consulta (sin cache):    {time1:.2f}s")
    print(f"📌 Segunda consulta (con cache):     {time2:.2f}s")
    print(f"📌 Mejora de velocidad:              {((time1 - time2) / time1 * 100):.1f}%")
    print(f"\n🌊 Streaming TTFB:                   {ttfb:.2f}s")
    print(f"🌊 Streaming tiempo total:           {total:.2f}s")
    print(f"🌊 Percepción de rapidez:            {((time2 - ttfb) / time2 * 100):.1f}% más rápido")
    
    print("\n" + "✨"*30)
    print("   ¡Pruebas completadas!")
    print("✨"*30 + "\n")


if __name__ == "__main__":
    try:
        main()
    except requests.exceptions.ConnectionError:
        print("\n❌ Error: No se pudo conectar al servidor")
        print("   Asegúrate de que el servidor esté corriendo en http://localhost:8000")
    except KeyboardInterrupt:
        print("\n\n⚠️  Pruebas interrumpidas por el usuario")
