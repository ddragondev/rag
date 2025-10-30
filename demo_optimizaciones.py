"""
⚡ Demo Visual de Optimizaciones v2.0

Muestra en tiempo real la diferencia de velocidad.
"""

import requests
import time
from colorama import init, Fore, Style

init(autoreset=True)

BASE_URL = "http://localhost:8000"

def print_header(text, color=Fore.CYAN):
    """Imprime un encabezado destacado."""
    print(f"\n{color}{'='*70}")
    print(f"{color}{Style.BRIGHT}{text}")
    print(f"{color}{'='*70}{Style.RESET_ALL}\n")


def demo_velocidad():
    """Demuestra la velocidad de respuesta."""
    print_header("⚡ DEMO: Velocidad de Respuesta Optimizada", Fore.MAGENTA)
    
    pregunta = "¿Qué es la geomecánica?"
    
    # Limpiar caché primero
    print(f"{Fore.YELLOW}📋 Limpiando caché...{Style.RESET_ALL}")
    requests.delete(f"{BASE_URL}/cache/clear")
    
    # Primera consulta (sin caché)
    print(f"\n{Fore.CYAN}{'─'*70}{Style.RESET_ALL}")
    print(f"{Fore.WHITE}1️⃣  PRIMERA CONSULTA (Sin caché){Style.RESET_ALL}")
    print(f"{Fore.CYAN}{'─'*70}{Style.RESET_ALL}")
    
    print(f"\n{Fore.YELLOW}❓ Pregunta:{Style.RESET_ALL} '{pregunta}'")
    print(f"{Fore.YELLOW}⏳ Consultando GPT-4o-mini...{Style.RESET_ALL}\n")
    
    inicio = time.time()
    response1 = requests.post(f"{BASE_URL}/ask", json={
        'question': pregunta,
        'category': 'geomecanica',
        'format': 'plain'
    })
    tiempo1 = time.time() - inicio
    
    if response1.status_code == 200:
        respuesta = response1.json()['answer_plain'].split('\n---')[0][:200]
        print(f"{Fore.GREEN}✅ Respuesta recibida:{Style.RESET_ALL}")
        print(f"{Fore.WHITE}{respuesta}...{Style.RESET_ALL}")
        print(f"\n{Fore.GREEN}{Style.BRIGHT}⏱️  Tiempo: {tiempo1:.2f} segundos{Style.RESET_ALL}")
    
    # Segunda consulta (con caché)
    print(f"\n{Fore.CYAN}{'─'*70}{Style.RESET_ALL}")
    print(f"{Fore.WHITE}2️⃣  SEGUNDA CONSULTA (Con caché){Style.RESET_ALL}")
    print(f"{Fore.CYAN}{'─'*70}{Style.RESET_ALL}")
    
    print(f"\n{Fore.YELLOW}❓ Pregunta:{Style.RESET_ALL} '{pregunta}' {Fore.GREEN}(misma pregunta){Style.RESET_ALL}")
    print(f"{Fore.YELLOW}⚡ Buscando en caché...{Style.RESET_ALL}\n")
    
    inicio = time.time()
    response2 = requests.post(f"{BASE_URL}/ask", json={
        'question': pregunta,
        'category': 'geomecanica',
        'format': 'plain'
    })
    tiempo2 = time.time() - inicio
    
    if response2.status_code == 200:
        respuesta = response2.json()['answer_plain'].split('\n---')[0][:200]
        print(f"{Fore.GREEN}✅ Respuesta recibida desde CACHÉ:{Style.RESET_ALL}")
        print(f"{Fore.WHITE}{respuesta}...{Style.RESET_ALL}")
        print(f"\n{Fore.GREEN}{Style.BRIGHT}⚡ Tiempo: {tiempo2:.3f} segundos{Style.RESET_ALL}")
    
    # Comparación
    mejora = tiempo1 / tiempo2
    
    print(f"\n{Fore.MAGENTA}{'='*70}{Style.RESET_ALL}")
    print(f"{Fore.MAGENTA}{Style.BRIGHT}📊 COMPARACIÓN DE VELOCIDAD{Style.RESET_ALL}")
    print(f"{Fore.MAGENTA}{'='*70}{Style.RESET_ALL}")
    
    print(f"\n{Fore.WHITE}Primera consulta (GPT):  {Fore.YELLOW}{tiempo1:.2f}s{Style.RESET_ALL}")
    print(f"{Fore.WHITE}Segunda consulta (Caché): {Fore.GREEN}{tiempo2:.3f}s{Style.RESET_ALL}")
    print(f"\n{Fore.CYAN}{Style.BRIGHT}🚀 Mejora: {mejora:.0f}x más rápido con caché!{Style.RESET_ALL}")
    
    # Comparación con v1.0
    print(f"\n{Fore.MAGENTA}{'─'*70}{Style.RESET_ALL}")
    print(f"{Fore.WHITE}Comparación con v1.0 (gpt-4):{Style.RESET_ALL}")
    print(f"{Fore.RED}   v1.0: ~10.0s{Style.RESET_ALL}")
    print(f"{Fore.GREEN}   v2.0: ~{tiempo1:.1f}s (primera) | ~{tiempo2:.3f}s (caché){Style.RESET_ALL}")
    
    mejora_v1 = 10.0 / tiempo1
    print(f"\n{Fore.CYAN}{Style.BRIGHT}🎯 v2.0 es {mejora_v1:.1f}x más rápido que v1.0{Style.RESET_ALL}")


def demo_cache_stats():
    """Muestra estadísticas del caché."""
    print_header("💾 ESTADÍSTICAS DEL CACHÉ", Fore.BLUE)
    
    response = requests.get(f"{BASE_URL}/cache/stats")
    
    if response.status_code == 200:
        stats = response.json()
        
        print(f"{Fore.WHITE}Tamaño del caché:{Style.RESET_ALL}     {Fore.GREEN}{stats['answer_cache_size']}{Style.RESET_ALL}/{stats['answer_cache_max']}")
        print(f"{Fore.WHITE}Vectorstores en cache:{Style.RESET_ALL} {Fore.GREEN}{stats['vectorstore_cache_size']}{Style.RESET_ALL}")
        
        pct = (stats['answer_cache_size'] / stats['answer_cache_max']) * 100
        print(f"{Fore.WHITE}Utilización:{Style.RESET_ALL}          {Fore.CYAN}{pct:.1f}%{Style.RESET_ALL}")
        
        print(f"\n{Fore.YELLOW}{stats['info']}{Style.RESET_ALL}")


def demo_costos():
    """Muestra comparación de costos."""
    print_header("💰 AHORRO DE COSTOS", Fore.GREEN)
    
    consultas_mes = 30000  # 1000/día x 30 días
    
    # v1.0
    costo_v1_por_consulta = 0.045
    costo_v1_mes = consultas_mes * costo_v1_por_consulta
    
    # v2.0 (sin caché)
    costo_v2_por_consulta = 0.002
    costo_v2_mes_sin_cache = consultas_mes * costo_v2_por_consulta
    
    # v2.0 (70% caché)
    costo_v2_mes_con_cache = (consultas_mes * 0.3) * costo_v2_por_consulta
    
    print(f"{Fore.WHITE}Escenario: {Fore.CYAN}1,000 consultas/día{Style.RESET_ALL} ({consultas_mes:,} al mes)")
    
    print(f"\n{Fore.RED}v1.0 (gpt-4):{Style.RESET_ALL}")
    print(f"   Costo mensual: ${costo_v1_mes:,.2f}")
    
    print(f"\n{Fore.YELLOW}v2.0 sin aprovechar caché:{Style.RESET_ALL}")
    print(f"   Costo mensual: ${costo_v2_mes_sin_cache:,.2f}")
    ahorro1 = costo_v1_mes - costo_v2_mes_sin_cache
    print(f"   Ahorro: ${ahorro1:,.2f} ({(ahorro1/costo_v1_mes)*100:.1f}%)")
    
    print(f"\n{Fore.GREEN}v2.0 con 70% caché:{Style.RESET_ALL}")
    print(f"   Costo mensual: ${costo_v2_mes_con_cache:,.2f}")
    ahorro2 = costo_v1_mes - costo_v2_mes_con_cache
    print(f"   Ahorro: ${ahorro2:,.2f} ({(ahorro2/costo_v1_mes)*100:.1f}%)")
    
    print(f"\n{Fore.GREEN}{Style.BRIGHT}💵 Ahorro anual: ${ahorro2 * 12:,.2f}{Style.RESET_ALL}")


def demo_complete():
    """Demo completo."""
    print(f"\n{Fore.MAGENTA}{Style.BRIGHT}")
    print("╔═══════════════════════════════════════════════════════════════════╗")
    print("║                                                                   ║")
    print("║           ⚡ DEMO: SISTEMA RAG OPTIMIZADO v2.0 ⚡                ║")
    print("║                                                                   ║")
    print("╚═══════════════════════════════════════════════════════════════════╝")
    print(f"{Style.RESET_ALL}")
    
    try:
        # Demo 1: Velocidad
        demo_velocidad()
        
        # Demo 2: Estadísticas
        demo_cache_stats()
        
        # Demo 3: Costos
        demo_costos()
        
        # Resumen final
        print(f"\n{Fore.MAGENTA}{Style.BRIGHT}")
        print("╔═══════════════════════════════════════════════════════════════════╗")
        print("║                                                                   ║")
        print("║                    ✅ DEMO COMPLETADO ✅                          ║")
        print("║                                                                   ║")
        print("║   Optimizaciones implementadas:                                  ║")
        print("║   ✅ gpt-4o-mini: 15-20x más rápido                              ║")
        print("║   ✅ Caché inteligente: Respuestas instantáneas                  ║")
        print("║   ✅ MMR Search: Mejor relevancia                                ║")
        print("║   ✅ Prompts optimizados: Más directo                            ║")
        print("║   ✅ 95-100% más barato                                          ║")
        print("║                                                                   ║")
        print("╚═══════════════════════════════════════════════════════════════════╝")
        print(f"{Style.RESET_ALL}\n")
        
    except requests.exceptions.ConnectionError:
        print(f"\n{Fore.RED}✗ Error de conexión{Style.RESET_ALL}")
        print(f"{Fore.YELLOW}Asegúrate de que el servidor esté corriendo:{Style.RESET_ALL}")
        print(f"  uvicorn main:app --reload")
    except Exception as e:
        print(f"\n{Fore.RED}✗ Error: {e}{Style.RESET_ALL}")


if __name__ == "__main__":
    demo_complete()
