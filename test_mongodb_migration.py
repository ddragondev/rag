#!/usr/bin/env python3
"""
Script de prueba para verificar la migración a MongoDB
"""

import requests
import json
import time

BASE_URL = "http://localhost:8000"

def print_header(title):
    """Imprime encabezado formateado."""
    print("\n" + "="*60)
    print(f"  {title}")
    print("="*60)

def test_mongodb_health():
    """Prueba la salud de MongoDB."""
    print_header("🏥 Verificando Salud de MongoDB")
    
    try:
        response = requests.get(f"{BASE_URL}/mongodb/health")
        data = response.json()
        
        print(f"✅ Status: {data.get('status')}")
        print(f"📊 Colecciones:")
        for col, count in data.get('collections', {}).items():
            print(f"   - {col}: {count} documentos")
        
        return data.get('status') == 'healthy'
    except Exception as e:
        print(f"❌ Error: {e}")
        return False

def test_cache_stats():
    """Prueba las estadísticas del caché."""
    print_header("📊 Estadísticas del Caché")
    
    try:
        response = requests.get(f"{BASE_URL}/cache/stats")
        data = response.json()
        
        print(f"📦 Total entradas: {data.get('total_entries', 0)}")
        print(f"🔧 Vectorstores: {data.get('vectorstore_cache_size', 0)}")
        
        categories = data.get('categories', [])
        if categories:
            print(f"\n📁 Por categoría:")
            for cat in categories:
                print(f"   - {cat.get('_id')}: {cat.get('count')} entradas ({cat.get('total_hits')} hits)")
        
        return True
    except Exception as e:
        print(f"❌ Error: {e}")
        return False

def test_categories():
    """Prueba la lista de categorías."""
    print_header("📁 Categorías Disponibles")
    
    try:
        response = requests.get(f"{BASE_URL}/categories")
        data = response.json()
        
        categories = data.get('categories', {})
        print(f"📊 Total categorías: {len(categories)}")
        
        for name, info in categories.items():
            print(f"\n📂 {name}")
            print(f"   Nombre: {info.get('display_name', 'N/A')}")
            print(f"   Descripción: {info.get('description', 'N/A')[:60]}...")
            print(f"   Archivos: {info.get('file_count', 0)}")
            if info.get('has_custom_prompt'):
                print(f"   ✓ Tiene prompts personalizados")
        
        return len(categories) > 0
    except Exception as e:
        print(f"❌ Error: {e}")
        return False

def test_question():
    """Prueba una pregunta simple."""
    print_header("💬 Prueba de Pregunta")
    
    # Primera pregunta (sin caché)
    print("\n🔄 Primera pregunta (sin caché)...")
    start_time = time.time()
    
    try:
        payload = {
            "question": "¿Qué es la geomecánica?",
            "category": "geomecanica",
            "format": "plain"
        }
        
        response = requests.post(f"{BASE_URL}/ask", json=payload)
        elapsed = time.time() - start_time
        
        if response.status_code == 200:
            data = response.json()
            print(f"✅ Respuesta recibida en {elapsed:.2f}s")
            print(f"📝 Respuesta: {data.get('answer_plain', '')[:150]}...")
        else:
            print(f"❌ Error {response.status_code}: {response.text}")
            return False
        
        # Segunda pregunta (con caché)
        print("\n⚡ Segunda pregunta (debería usar caché)...")
        start_time = time.time()
        
        response = requests.post(f"{BASE_URL}/ask", json=payload)
        elapsed = time.time() - start_time
        
        if response.status_code == 200:
            print(f"✅ Respuesta recibida en {elapsed:.2f}s")
            if elapsed < 0.5:
                print("🎉 ¡Caché funcionando! Respuesta instantánea")
            else:
                print("⚠️ Caché podría no estar funcionando (tiempo > 0.5s)")
        
        return True
        
    except Exception as e:
        print(f"❌ Error: {e}")
        return False

def test_conversations():
    """Prueba el sistema conversacional."""
    print_header("💭 Prueba de Conversaciones")
    
    session_id = "test-session-123"
    
    try:
        # Primera pregunta en conversación
        print(f"\n📤 Pregunta 1 (sesión: {session_id})...")
        payload = {
            "question": "¿Qué es la estabilidad de taludes?",
            "category": "geomecanica",
            "format": "plain",
            "session_id": session_id
        }
        
        response = requests.post(f"{BASE_URL}/ask", json=payload)
        if response.status_code != 200:
            print(f"❌ Error en primera pregunta")
            return False
        
        print("✅ Pregunta 1 guardada")
        
        # Segunda pregunta con contexto
        print(f"\n📤 Pregunta 2 (con contexto)...")
        payload["question"] = "¿Y cómo se analiza?"
        
        response = requests.post(f"{BASE_URL}/ask", json=payload)
        if response.status_code != 200:
            print(f"❌ Error en segunda pregunta")
            return False
        
        print("✅ Pregunta 2 guardada")
        
        # Obtener historial
        print(f"\n📜 Obteniendo historial...")
        response = requests.get(f"{BASE_URL}/conversations/{session_id}")
        
        if response.status_code == 200:
            data = response.json()
            history = data.get('history', [])
            print(f"✅ Historial obtenido: {len(history)} mensajes")
            
            for i, msg in enumerate(history, 1):
                role = "👤 Usuario" if msg['role'] == 'user' else "🤖 Asistente"
                content = msg['content'][:60]
                print(f"   {i}. {role}: {content}...")
        else:
            print(f"⚠️ No se pudo obtener historial")
        
        # Limpiar conversación de prueba
        print(f"\n🗑️ Limpiando conversación de prueba...")
        requests.delete(f"{BASE_URL}/conversations/{session_id}")
        print("✅ Conversación limpiada")
        
        return True
        
    except Exception as e:
        print(f"❌ Error: {e}")
        return False

def test_metrics():
    """Prueba las métricas de MongoDB."""
    print_header("📈 Métricas de MongoDB")
    
    try:
        response = requests.get(f"{BASE_URL}/mongodb/metrics?hours=1")
        data = response.json()
        
        total = data.get('total_metrics', 0)
        print(f"📊 Métricas registradas (última hora): {total}")
        
        if total > 0:
            print("✅ Sistema de métricas funcionando")
        else:
            print("ℹ️ No hay métricas recientes (es normal si acabas de migrar)")
        
        return True
    except Exception as e:
        print(f"❌ Error: {e}")
        return False

def main():
    """Ejecuta todas las pruebas."""
    print("\n" + "🚀 PRUEBAS DE MIGRACIÓN A MONGODB".center(60, "="))
    print("Este script verifica que la migración fue exitosa")
    
    results = {
        "MongoDB Health": test_mongodb_health(),
        "Cache Stats": test_cache_stats(),
        "Categories": test_categories(),
        "Question & Cache": test_question(),
        "Conversations": test_conversations(),
        "Metrics": test_metrics()
    }
    
    # Resumen
    print_header("📊 RESUMEN DE PRUEBAS")
    
    passed = sum(1 for v in results.values() if v)
    total = len(results)
    
    for test, result in results.items():
        status = "✅ PASS" if result else "❌ FAIL"
        print(f"{status} - {test}")
    
    print(f"\n{'='*60}")
    print(f"  Resultado: {passed}/{total} pruebas exitosas")
    print(f"{'='*60}")
    
    if passed == total:
        print("\n🎉 ¡TODAS LAS PRUEBAS PASARON!")
        print("✅ La migración a MongoDB fue exitosa")
        print("💡 El sistema está listo para usar")
    else:
        print("\n⚠️ Algunas pruebas fallaron")
        print("📖 Revisa la GUIA_MIGRACION_MONGO.md para troubleshooting")
    
    print()

if __name__ == "__main__":
    try:
        main()
    except KeyboardInterrupt:
        print("\n\n👋 Pruebas interrumpidas por el usuario")
    except Exception as e:
        print(f"\n❌ Error inesperado: {e}")
