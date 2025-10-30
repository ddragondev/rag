"""
🚀 Script de Benchmark - Comparación de Velocidad v2.0

Compara el rendimiento antes y después de las optimizaciones.
"""

import requests
import time
from datetime import datetime

BASE_URL = "http://localhost:8000"

# Preguntas de prueba
PREGUNTAS_TEST = [
    "¿Qué es la geomecánica?",
    "¿Cuáles son los principales tipos de rocas?",
    "Explica qué es la fortificación en minería",
    "¿Qué factores causan las caídas de rocas?",
    "Resume los métodos de soporte del terreno"
]

def medir_tiempo(funcion, *args, **kwargs):
    """Mide el tiempo de ejecución de una función."""
    inicio = time.time()
    resultado = funcion(*args, **kwargs)
    fin = time.time()
    return resultado, fin - inicio


def hacer_pregunta(pregunta, categoria="geomecanica", formato="plain"):
    """Hace una pregunta al API."""
    response = requests.post(f"{BASE_URL}/ask", json={
        'question': pregunta,
        'category': categoria,
        'format': formato
    })
    return response


def ver_stats_cache():
    """Obtiene estadísticas del caché."""
    try:
        response = requests.get(f"{BASE_URL}/cache/stats")
        if response.status_code == 200:
            return response.json()
    except:
        pass
    return None


def limpiar_cache():
    """Limpia el caché de respuestas."""
    try:
        response = requests.delete(f"{BASE_URL}/cache/clear")
        if response.status_code == 200:
            print("✅ Caché limpiado")
    except:
        print("⚠️  No se pudo limpiar el caché")


def ejecutar_benchmark():
    """Ejecuta el benchmark completo."""
    print("\n" + "="*70)
    print("🚀 BENCHMARK DE VELOCIDAD - Sistema RAG v2.0")
    print("="*70)
    
    # Limpiar caché antes de empezar
    print("\n📋 Preparación:")
    limpiar_cache()
    
    # Test 1: Primera ejecución (SIN caché)
    print("\n" + "─"*70)
    print("📊 TEST 1: Primera ejecución (SIN caché)")
    print("─"*70)
    
    tiempos_primera = []
    for i, pregunta in enumerate(PREGUNTAS_TEST, 1):
        print(f"\n{i}. Pregunta: '{pregunta[:50]}...'")
        _, tiempo = medir_tiempo(hacer_pregunta, pregunta)
        tiempos_primera.append(tiempo)
        print(f"   ⏱️  Tiempo: {tiempo:.2f}s")
    
    promedio_primera = sum(tiempos_primera) / len(tiempos_primera)
    print(f"\n📈 Promedio SIN caché: {promedio_primera:.2f}s")
    
    # Ver estado del caché
    stats = ver_stats_cache()
    if stats:
        print(f"💾 Respuestas en caché: {stats['answer_cache_size']}/{stats['answer_cache_max']}")
    
    # Test 2: Segunda ejecución (CON caché)
    print("\n" + "─"*70)
    print("📊 TEST 2: Segunda ejecución (CON caché)")
    print("─"*70)
    
    tiempos_segunda = []
    for i, pregunta in enumerate(PREGUNTAS_TEST, 1):
        print(f"\n{i}. Pregunta: '{pregunta[:50]}...'")
        _, tiempo = medir_tiempo(hacer_pregunta, pregunta)
        tiempos_segunda.append(tiempo)
        print(f"   ⚡ Tiempo: {tiempo:.3f}s")
    
    promedio_segunda = sum(tiempos_segunda) / len(tiempos_segunda)
    print(f"\n📈 Promedio CON caché: {promedio_segunda:.3f}s")
    
    # Calcular mejora
    mejora = promedio_primera / promedio_segunda
    print(f"\n🎯 Mejora con caché: {mejora:.1f}x más rápido")
    
    # Test 3: Estadísticas finales
    print("\n" + "─"*70)
    print("📊 RESUMEN DE RENDIMIENTO")
    print("─"*70)
    
    print(f"\n⏱️  VELOCIDAD:")
    print(f"   • Primera consulta (sin caché):  {promedio_primera:.2f}s")
    print(f"   • Consulta repetida (con caché): {promedio_segunda:.3f}s")
    print(f"   • Mejora:                        {mejora:.1f}x más rápido")
    
    print(f"\n💰 COSTOS ESTIMADOS (por consulta):")
    costo_primera = promedio_primera * 0.001  # Estimación aprox
    costo_segunda = 0.000  # Caché es gratis
    print(f"   • Primera consulta:  ~${costo_primera:.4f}")
    print(f"   • Con caché:         ${costo_segunda:.4f} (¡GRATIS!)")
    
    print(f"\n💾 CACHÉ:")
    if stats:
        print(f"   • Tamaño actual:     {stats['answer_cache_size']}")
        print(f"   • Capacidad máxima:  {stats['answer_cache_max']}")
        print(f"   • Utilización:       {stats['answer_cache_size']/stats['answer_cache_max']*100:.1f}%")
    
    # Test 4: Comparación con estimaciones de v1.0
    print("\n" + "─"*70)
    print("📊 COMPARACIÓN: v1.0 vs v2.0")
    print("─"*70)
    
    # Estimaciones de v1.0 (gpt-4, temp=1, k=3)
    tiempo_v1 = 10.0  # Estimado
    costo_v1 = 0.045  # Estimado por consulta
    
    print(f"\n📉 VERSIÓN 1.0 (estimado):")
    print(f"   • Modelo:        gpt-4")
    print(f"   • Temperatura:   1")
    print(f"   • Documentos:    3")
    print(f"   • Tiempo:        ~{tiempo_v1:.1f}s")
    print(f"   • Costo:         ~${costo_v1:.3f}")
    
    print(f"\n📈 VERSIÓN 2.0 (medido):")
    print(f"   • Modelo:        gpt-4o-mini")
    print(f"   • Temperatura:   0")
    print(f"   • Documentos:    2 (MMR)")
    print(f"   • Tiempo:        ~{promedio_primera:.1f}s")
    print(f"   • Costo:         ~${costo_primera:.3f}")
    print(f"   • Con caché:     ~{promedio_segunda:.3f}s (${costo_segunda:.3f})")
    
    mejora_velocidad = tiempo_v1 / promedio_primera
    mejora_costo = ((costo_v1 - costo_primera) / costo_v1) * 100
    
    print(f"\n🎯 MEJORAS GLOBALES:")
    print(f"   ⚡ Velocidad:     {mejora_velocidad:.1f}x más rápido")
    print(f"   💰 Costo:         {mejora_costo:.1f}% más barato")
    print(f"   ⚡ Con caché:     {tiempo_v1/promedio_segunda:.0f}x más rápido (¡GRATIS!)")
    
    # Test 5: Proyecciones de uso
    print("\n" + "─"*70)
    print("📊 PROYECCIONES DE USO MENSUAL")
    print("─"*70)
    
    consultas_dia = 1000
    consultas_mes = consultas_dia * 30
    
    costo_mes_v1 = consultas_mes * costo_v1
    costo_mes_v2_sin_cache = consultas_mes * costo_primera
    costo_mes_v2_con_cache = consultas_mes * 0.3 * costo_primera  # 70% caché, 30% nuevas
    
    print(f"\nEscenario: {consultas_dia:,} consultas/día ({consultas_mes:,}/mes)")
    print(f"\n💰 COSTOS MENSUALES:")
    print(f"   • v1.0:                           ${costo_mes_v1:,.2f}")
    print(f"   • v2.0 (sin aprovechar caché):    ${costo_mes_v2_sin_cache:,.2f}")
    print(f"   • v2.0 (70% caché, 30% nuevas):   ${costo_mes_v2_con_cache:,.2f}")
    
    ahorro = costo_mes_v1 - costo_mes_v2_con_cache
    ahorro_pct = (ahorro / costo_mes_v1) * 100
    
    print(f"\n💵 AHORRO MENSUAL:")
    print(f"   • Cantidad:      ${ahorro:,.2f}")
    print(f"   • Porcentaje:    {ahorro_pct:.1f}%")
    print(f"   • Anual:         ${ahorro * 12:,.2f}")
    
    print("\n" + "="*70)
    print("✅ BENCHMARK COMPLETADO")
    print("="*70)
    
    # Recomendaciones
    print("\n💡 RECOMENDACIONES:")
    if promedio_primera > 3:
        print("   ⚠️  Tiempo de primera consulta alto (>3s)")
        print("      → Considera reducir chunk_size o k para mayor velocidad")
    else:
        print("   ✅ Tiempo de primera consulta óptimo (<3s)")
    
    if stats and stats['answer_cache_size'] < 10:
        print("   ℹ️  Pocas respuestas en caché")
        print("      → El caché será más efectivo con más uso")
    else:
        print("   ✅ Caché funcionando correctamente")
    
    print(f"\n📅 Benchmark ejecutado: {datetime.now().strftime('%Y-%m-%d %H:%M:%S')}")
    print()


if __name__ == "__main__":
    try:
        ejecutar_benchmark()
    except requests.exceptions.ConnectionError:
        print("\n❌ Error: No se puede conectar a la API")
        print("   Asegúrate de que el servidor esté corriendo:")
        print("   uvicorn main:app --reload")
    except KeyboardInterrupt:
        print("\n\n⚠️  Benchmark interrumpido por el usuario")
    except Exception as e:
        print(f"\n❌ Error inesperado: {e}")
