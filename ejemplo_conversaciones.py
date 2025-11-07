"""
Ejemplo de uso de la API de Conversaciones
Demuestra cómo mantener contexto conversacional
"""

import requests
import json
import time

BASE_URL = "http://localhost:8000"

def print_response(title, response):
    """Imprime respuesta de forma legible."""
    print(f"\n{'='*60}")
    print(f"📋 {title}")
    print(f"{'='*60}")
    if isinstance(response, dict):
        print(json.dumps(response, indent=2, ensure_ascii=False))
    else:
        print(response)
    print()

def ejemplo_conversacion_basica():
    """Ejemplo básico de conversación con contexto."""
    print("\n🎯 EJEMPLO 1: Conversación Básica con Contexto")
    print("=" * 60)
    
    session_id = f"demo_{int(time.time())}"
    
    # Primera pregunta
    print("\n👤 Usuario: ¿Qué es CAP?")
    response1 = requests.post(f"{BASE_URL}/ask", json={
        "question": "¿Qué es CAP?",
        "category": "compliance",
        "format": "plain",
        "session_id": session_id
    })
    
    data1 = response1.json()
    print(f"🤖 Asistente: {data1.get('answer_plain', '')[:200]}...")
    
    # Segunda pregunta (con contexto)
    time.sleep(1)
    print("\n👤 Usuario: ¿Cuál es su directorio?")
    response2 = requests.post(f"{BASE_URL}/ask", json={
        "question": "¿Cuál es su directorio?",  # "su" se refiere a CAP
        "category": "compliance",
        "format": "plain",
        "session_id": session_id
    })
    
    data2 = response2.json()
    print(f"🤖 Asistente: {data2.get('answer_plain', '')[:200]}...")
    
    # Tercera pregunta (más contexto)
    time.sleep(1)
    print("\n👤 Usuario: ¿Cuántos miembros tiene?")
    response3 = requests.post(f"{BASE_URL}/ask", json={
        "question": "¿Cuántos miembros tiene?",  # Se refiere al directorio
        "category": "compliance",
        "format": "plain",
        "session_id": session_id
    })
    
    data3 = response3.json()
    print(f"🤖 Asistente: {data3.get('answer_plain', '')[:200]}...")
    
    # Ver historial completo
    print("\n📜 Historial completo de la conversación:")
    history = requests.get(f"{BASE_URL}/conversations/{session_id}")
    print_response("Historial", history.json())
    
    return session_id

def ejemplo_listar_conversaciones():
    """Ejemplo de listado de conversaciones activas."""
    print("\n🎯 EJEMPLO 2: Listar Todas las Conversaciones")
    print("=" * 60)
    
    response = requests.get(f"{BASE_URL}/conversations")
    data = response.json()
    
    print(f"\n📊 Total de conversaciones activas: {data['total_conversations']}")
    
    for conv in data['conversations']:
        print(f"\n🗨️  Sesión: {conv['session_id']}")
        print(f"   📝 Mensajes: {conv['message_count']} ({conv['interaction_count']} interacciones)")
        print(f"   💬 Preview: {conv['preview']}")
        print(f"   ❓ Última pregunta: {conv['last_question']}")

def ejemplo_recuperar_conversacion(session_id):
    """Ejemplo de recuperar una conversación existente."""
    print("\n🎯 EJEMPLO 3: Recuperar Conversación Existente")
    print("=" * 60)
    
    # Obtener historial
    response = requests.get(f"{BASE_URL}/conversations/{session_id}")
    data = response.json()
    
    print(f"\n📱 Sesión recuperada: {session_id}")
    print(f"📊 Total de mensajes: {data['message_count']}")
    
    # Continuar la conversación
    print("\n👤 Usuario: ¿Qué más puedes decirme sobre ellos?")
    response = requests.post(f"{BASE_URL}/ask", json={
        "question": "¿Qué más puedes decirme sobre ellos?",  # Contexto: sobre CAP/directorio
        "category": "compliance",
        "format": "plain",
        "session_id": session_id
    })
    
    data = response.json()
    print(f"🤖 Asistente: {data.get('answer_plain', '')[:200]}...")
    
    print("\n✅ La conversación mantiene TODO el contexto anterior!")

def ejemplo_multiples_categorias():
    """Ejemplo de conversaciones en diferentes categorías."""
    print("\n🎯 EJEMPLO 4: Conversaciones en Diferentes Categorías")
    print("=" * 60)
    
    # Sesión para compliance
    session_compliance = f"compliance_{int(time.time())}"
    print("\n📁 Categoría: Compliance")
    print("👤 Usuario: ¿Qué es la prevención de delitos?")
    
    response1 = requests.post(f"{BASE_URL}/ask", json={
        "question": "¿Qué es la prevención de delitos?",
        "category": "compliance",
        "format": "plain",
        "session_id": session_compliance
    })
    print(f"🤖 Asistente: {response1.json().get('answer_plain', '')[:150]}...")
    
    # Sesión para geomecánica
    time.sleep(1)
    session_geo = f"geo_{int(time.time())}"
    print("\n📁 Categoría: Geomecánica")
    print("👤 Usuario: ¿Qué es la geomecánica?")
    
    response2 = requests.post(f"{BASE_URL}/ask", json={
        "question": "¿Qué es la geomecánica?",
        "category": "geomecanica",
        "format": "plain",
        "session_id": session_geo
    })
    print(f"🤖 Asistente: {response2.json().get('answer_plain', '')[:150]}...")
    
    print("\n✅ Cada sesión mantiene su propio contexto independiente!")

def ejemplo_limpiar_conversacion(session_id):
    """Ejemplo de eliminar una conversación."""
    print("\n🎯 EJEMPLO 5: Limpiar Conversación")
    print("=" * 60)
    
    print(f"\n🗑️  Eliminando sesión: {session_id}")
    response = requests.delete(f"{BASE_URL}/conversations/{session_id}")
    print_response("Resultado", response.json())

def ejemplo_comparacion_con_sin_sesion():
    """Compara comportamiento con y sin session_id."""
    print("\n🎯 EJEMPLO 6: Con vs Sin Contexto")
    print("=" * 60)
    
    # CON contexto
    print("\n✅ CON CONTEXTO (usando session_id):")
    session_id = f"test_{int(time.time())}"
    
    print("👤 Pregunta 1: ¿Qué es CAP?")
    requests.post(f"{BASE_URL}/ask", json={
        "question": "¿Qué es CAP?",
        "category": "compliance",
        "format": "plain",
        "session_id": session_id
    })
    
    time.sleep(1)
    print("👤 Pregunta 2: ¿Cuál es su directorio?")
    response_con = requests.post(f"{BASE_URL}/ask", json={
        "question": "¿Cuál es su directorio?",
        "category": "compliance",
        "format": "plain",
        "session_id": session_id
    })
    print(f"🤖 {response_con.json().get('answer_plain', '')[:150]}...")
    
    # SIN contexto
    print("\n❌ SIN CONTEXTO (sin session_id):")
    print("👤 Pregunta: ¿Cuál es su directorio?")
    response_sin = requests.post(f"{BASE_URL}/ask", json={
        "question": "¿Cuál es su directorio?",
        "category": "compliance",
        "format": "plain"
        # No incluimos session_id
    })
    print(f"🤖 {response_sin.json().get('answer_plain', '')[:150]}...")
    print("\n⚠️  Sin contexto, la IA no sabe a qué se refiere 'su'")

def main():
    """Ejecuta todos los ejemplos."""
    print("""
    ╔════════════════════════════════════════════════════════════╗
    ║  🎯 EJEMPLOS DE USO - API DE CONVERSACIONES               ║
    ║  Sistema RAG con Memoria Conversacional                   ║
    ╚════════════════════════════════════════════════════════════╝
    """)
    
    try:
        # Ejemplo 1: Conversación básica
        session_id = ejemplo_conversacion_basica()
        
        input("\n⏸️  Presiona ENTER para continuar...")
        
        # Ejemplo 2: Listar conversaciones
        ejemplo_listar_conversaciones()
        
        input("\n⏸️  Presiona ENTER para continuar...")
        
        # Ejemplo 3: Recuperar conversación
        ejemplo_recuperar_conversacion(session_id)
        
        input("\n⏸️  Presiona ENTER para continuar...")
        
        # Ejemplo 4: Múltiples categorías
        ejemplo_multiples_categorias()
        
        input("\n⏸️  Presiona ENTER para continuar...")
        
        # Ejemplo 5: Comparación
        ejemplo_comparacion_con_sin_sesion()
        
        input("\n⏸️  Presiona ENTER para continuar...")
        
        # Ejemplo 6: Limpiar
        ejemplo_limpiar_conversacion(session_id)
        
        print("\n" + "="*60)
        print("✅ Todos los ejemplos completados!")
        print("="*60)
        
    except requests.exceptions.ConnectionError:
        print("\n❌ ERROR: No se puede conectar al servidor.")
        print("   Asegúrate de que el servidor esté corriendo:")
        print("   uvicorn main:app --reload")
    except Exception as e:
        print(f"\n❌ ERROR: {str(e)}")

if __name__ == "__main__":
    main()
