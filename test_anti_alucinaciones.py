"""
🛡️ Test: Sistema Anti-Alucinaciones

Prueba que el sistema NO responda preguntas fuera de contexto.
"""

import requests
import json

BASE_URL = "http://localhost:8000"

# Preguntas de prueba
TESTS = [
    {
        "name": "Pregunta claramente OFF-TOPIC (Filosofía)",
        "question": "¿Qué es la filosofía?",
        "expected": "off_topic",  # Debe rechazar
        "category": "geomecanica"
    },
    {
        "name": "Pregunta OFF-TOPIC (Cocina)",
        "question": "¿Cómo se hace un pastel de chocolate?",
        "expected": "off_topic",
        "category": "geomecanica"
    },
    {
        "name": "Pregunta OFF-TOPIC (Deportes)",
        "question": "¿Cuáles son las reglas del fútbol?",
        "expected": "off_topic",
        "category": "geomecanica"
    },
    {
        "name": "Pregunta OFF-TOPIC (Programación)",
        "question": "¿Cómo programar en Python?",
        "expected": "off_topic",
        "category": "geomecanica"
    },
    {
        "name": "Pregunta ON-TOPIC (Geomecánica)",
        "question": "¿Qué es la geomecánica?",
        "expected": "on_topic",  # Debe responder
        "category": "geomecanica"
    },
    {
        "name": "Pregunta ON-TOPIC (Rocas)",
        "question": "¿Qué tipos de rocas existen?",
        "expected": "on_topic",
        "category": "geomecanica"
    },
    {
        "name": "Pregunta ON-TOPIC (Minería)",
        "question": "¿Qué es la fortificación en minería?",
        "expected": "on_topic",
        "category": "geomecanica"
    },
    {
        "name": "Pregunta EDGE CASE (Parcialmente relacionada)",
        "question": "¿Qué es la resistencia?",  # Muy genérica
        "expected": "on_topic",  # Probablemente permitida
        "category": "geomecanica"
    }
]


def test_question(test_case):
    """Prueba una pregunta específica."""
    print(f"\n{'='*70}")
    print(f"🧪 TEST: {test_case['name']}")
    print(f"{'='*70}")
    print(f"❓ Pregunta: '{test_case['question']}'")
    print(f"🎯 Esperado: {test_case['expected']}")
    
    response = requests.post(f"{BASE_URL}/ask", json={
        'question': test_case['question'],
        'category': test_case['category'],
        'format': 'plain'
    })
    
    if response.status_code != 200:
        print(f"❌ Error HTTP: {response.status_code}")
        return False
    
    data = response.json()
    answer = data.get('answer_plain', '')
    warning = data.get('warning', '')
    
    # Verificar si fue rechazada
    is_rejected = (
        '❌' in answer or 
        'no parece estar relacionada' in answer.lower() or
        'no está relacionado' in answer.lower() or
        warning == 'off_topic_question'
    )
    
    # Verificar si fue respondida del contexto
    is_from_context = (
        'no encontré información' in answer.lower() or
        (not is_rejected and len(answer) > 50)
    )
    
    print(f"\n📊 RESULTADO:")
    print(f"   Rechazada: {is_rejected}")
    print(f"   Respondida: {is_from_context}")
    print(f"   Warning: {warning if warning else 'None'}")
    
    print(f"\n💬 RESPUESTA:")
    print(f"   {answer[:200]}..." if len(answer) > 200 else f"   {answer}")
    
    # Evaluar resultado
    if test_case['expected'] == 'off_topic':
        success = is_rejected
        if success:
            print(f"\n✅ CORRECTO: Pregunta OFF-TOPIC rechazada exitosamente")
        else:
            print(f"\n❌ FALLO: Pregunta OFF-TOPIC NO fue rechazada (alucinación)")
    else:  # on_topic
        success = not is_rejected and is_from_context
        if success:
            print(f"\n✅ CORRECTO: Pregunta ON-TOPIC respondida del contexto")
        else:
            print(f"\n⚠️  ADVERTENCIA: Pregunta ON-TOPIC no respondida correctamente")
    
    return success


def run_all_tests():
    """Ejecuta todos los tests."""
    print("\n" + "="*70)
    print("🛡️ SISTEMA ANTI-ALUCINACIONES - TESTS DE VALIDACIÓN")
    print("="*70)
    
    results = []
    for test in TESTS:
        try:
            success = test_question(test)
            results.append({
                'test': test['name'],
                'passed': success
            })
        except Exception as e:
            print(f"\n❌ Error ejecutando test: {e}")
            results.append({
                'test': test['name'],
                'passed': False
            })
    
    # Resumen final
    print("\n" + "="*70)
    print("📊 RESUMEN DE RESULTADOS")
    print("="*70)
    
    passed = sum(1 for r in results if r['passed'])
    total = len(results)
    percentage = (passed / total) * 100
    
    print(f"\n✅ Tests pasados: {passed}/{total} ({percentage:.1f}%)")
    print(f"❌ Tests fallados: {total - passed}/{total}")
    
    print(f"\n📋 DETALLE:")
    for r in results:
        status = "✅" if r['passed'] else "❌"
        print(f"   {status} {r['test']}")
    
    if percentage >= 75:
        print(f"\n🎉 EXCELENTE: El sistema anti-alucinaciones funciona correctamente")
    elif percentage >= 50:
        print(f"\n⚠️  MEJORABLE: El sistema necesita ajustes")
    else:
        print(f"\n❌ CRÍTICO: El sistema requiere revisión urgente")
    
    print("\n" + "="*70)
    
    return results


if __name__ == "__main__":
    try:
        results = run_all_tests()
        
        print("\n💡 RECOMENDACIONES:")
        passed = sum(1 for r in results if r['passed'])
        if passed == len(results):
            print("   ✅ Todos los tests pasaron. Sistema funcionando óptimamente.")
        else:
            print("   ⚠️  Algunos tests fallaron. Considera ajustar:")
            print("      1. Keywords en is_question_relevant_to_category()")
            print("      2. Instrucciones en los prompts")
            print("      3. Threshold de relevancia del contexto")
        
    except requests.exceptions.ConnectionError:
        print("\n❌ Error: No se puede conectar a la API")
        print("   Asegúrate de que el servidor esté corriendo:")
        print("   uvicorn main:app --reload")
    except KeyboardInterrupt:
        print("\n\n⚠️  Tests interrumpidos por el usuario")
    except Exception as e:
        print(f"\n❌ Error inesperado: {e}")
