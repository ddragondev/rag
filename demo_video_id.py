"""
Demo visual del sistema de consulta de videos por ID

Muestra cómo usar el nuevo endpoint /ask-video
"""

import requests
import json
from colorama import init, Fore, Style

# Inicializar colorama para colores en terminal
init(autoreset=True)

BASE_URL = "http://localhost:8000"

def print_header(text):
    """Imprime un encabezado destacado."""
    print(f"\n{Fore.CYAN}{'='*70}")
    print(f"{Fore.CYAN}{Style.BRIGHT}{text}")
    print(f"{Fore.CYAN}{'='*70}{Style.RESET_ALL}\n")


def print_success(text):
    """Imprime texto de éxito."""
    print(f"{Fore.GREEN}✓{Style.RESET_ALL} {text}")


def print_info(text):
    """Imprime texto informativo."""
    print(f"{Fore.BLUE}ℹ{Style.RESET_ALL} {text}")


def print_video_info(video_id, filename):
    """Imprime información de un video."""
    print(f"{Fore.YELLOW}📹 {video_id}{Style.RESET_ALL}")
    print(f"   {Fore.WHITE}{filename[:65]}...{Style.RESET_ALL}")


def demo_list_videos():
    """Demuestra cómo listar videos."""
    print_header("🎥 DEMO 1: Listar Videos Disponibles")
    
    print_info(f"GET {BASE_URL}/videos/geomecanica\n")
    
    try:
        response = requests.get(f"{BASE_URL}/videos/geomecanica")
        
        if response.status_code == 200:
            data = response.json()
            
            print_success(f"Categoría: {data['category']}")
            print_success(f"Total de videos: {data['total_videos']}\n")
            
            print(f"{Fore.YELLOW}Videos disponibles:{Style.RESET_ALL}")
            for video_id, info in data['videos'].items():
                print_video_info(video_id, info['filename'])
            
            return list(data['videos'].keys())
        else:
            print(f"{Fore.RED}✗ Error: {response.status_code}{Style.RESET_ALL}")
            return []
            
    except Exception as e:
        print(f"{Fore.RED}✗ Error de conexión: {e}{Style.RESET_ALL}")
        return []


def demo_ask_video(video_id):
    """Demuestra cómo consultar un video específico."""
    print_header(f"🎥 DEMO 2: Consultar Video '{video_id}'")
    
    payload = {
        "question": "¿Cuáles son los conceptos principales que se cubren en este módulo?",
        "video_id": video_id,
        "category": "geomecanica",
        "format": "plain"
    }
    
    print_info(f"POST {BASE_URL}/ask-video")
    print(f"\n{Fore.WHITE}Payload:{Style.RESET_ALL}")
    print(json.dumps(payload, indent=2, ensure_ascii=False))
    
    print(f"\n{Fore.YELLOW}⏳ Enviando consulta...{Style.RESET_ALL}\n")
    
    try:
        response = requests.post(f"{BASE_URL}/ask-video", json=payload)
        
        if response.status_code == 200:
            data = response.json()
            
            print_success("Respuesta recibida\n")
            print(f"{Fore.CYAN}{'─'*70}{Style.RESET_ALL}")
            print(f"{Fore.WHITE}{data.get('answer_plain', 'Sin respuesta')}{Style.RESET_ALL}")
            print(f"{Fore.CYAN}{'─'*70}{Style.RESET_ALL}")
        else:
            print(f"{Fore.RED}✗ Error: {response.status_code}{Style.RESET_ALL}")
            print(response.json())
            
    except Exception as e:
        print(f"{Fore.RED}✗ Error: {e}{Style.RESET_ALL}")


def demo_compare_formats(video_id):
    """Demuestra los diferentes formatos de respuesta."""
    print_header(f"🎥 DEMO 3: Formatos de Respuesta (Video '{video_id}')")
    
    question = "Resume brevemente este módulo"
    
    formats = ["plain", "html", "both"]
    
    for fmt in formats:
        print(f"\n{Fore.YELLOW}📄 Formato: {fmt}{Style.RESET_ALL}")
        print(f"{Fore.CYAN}{'─'*70}{Style.RESET_ALL}")
        
        payload = {
            "question": question,
            "video_id": video_id,
            "category": "geomecanica",
            "format": fmt
        }
        
        try:
            response = requests.post(f"{BASE_URL}/ask-video", json=payload)
            
            if response.status_code == 200:
                data = response.json()
                
                if fmt == "plain" or fmt == "both":
                    if 'answer_plain' in data:
                        plain = data['answer_plain']
                        print(f"\n{Fore.GREEN}✓ answer_plain:{Style.RESET_ALL} {len(plain)} caracteres")
                        print(f"{Fore.WHITE}{plain[:150]}...{Style.RESET_ALL}")
                
                if fmt == "html" or fmt == "both":
                    if 'answer_html' in data:
                        html = data['answer_html']
                        print(f"\n{Fore.GREEN}✓ answer_html:{Style.RESET_ALL} {len(html)} caracteres")
                        print(f"{Fore.WHITE}{html[:150]}...{Style.RESET_ALL}")
                        
        except Exception as e:
            print(f"{Fore.RED}✗ Error: {e}{Style.RESET_ALL}")
        
        print(f"{Fore.CYAN}{'─'*70}{Style.RESET_ALL}")


def demo_multiple_videos():
    """Demuestra cómo consultar múltiples videos con la misma pregunta."""
    print_header("🎥 DEMO 4: Misma Pregunta a Diferentes Videos")
    
    question = "¿Qué es lo más importante de este módulo?"
    
    print_info(f"Pregunta: '{question}'")
    print_info(f"Videos: modulo_1, modulo_2, modulo_3\n")
    
    for i in range(1, 4):
        video_id = f"modulo_{i}"
        
        print(f"\n{Fore.YELLOW}📹 {video_id.upper()}{Style.RESET_ALL}")
        print(f"{Fore.CYAN}{'─'*70}{Style.RESET_ALL}")
        
        payload = {
            "question": question,
            "video_id": video_id,
            "category": "geomecanica",
            "format": "plain"
        }
        
        try:
            response = requests.post(f"{BASE_URL}/ask-video", json=payload)
            
            if response.status_code == 200:
                data = response.json()
                answer = data.get('answer_plain', '').split('\n---')[0]  # Solo respuesta, sin fuentes
                print(f"{Fore.WHITE}{answer[:250]}...{Style.RESET_ALL}")
            else:
                print(f"{Fore.RED}✗ Error{Style.RESET_ALL}")
                
        except Exception as e:
            print(f"{Fore.RED}✗ Error: {e}{Style.RESET_ALL}")


def demo_invalid_video():
    """Demuestra el manejo de errores con video_id inválido."""
    print_header("🎥 DEMO 5: Manejo de Errores (Video Inválido)")
    
    payload = {
        "question": "¿Qué contiene este módulo?",
        "video_id": "modulo_999",
        "category": "geomecanica",
        "format": "plain"
    }
    
    print_info(f"POST {BASE_URL}/ask-video")
    print(f"\n{Fore.WHITE}Payload (video_id inválido):{Style.RESET_ALL}")
    print(json.dumps(payload, indent=2, ensure_ascii=False))
    
    print(f"\n{Fore.YELLOW}⏳ Enviando consulta...{Style.RESET_ALL}\n")
    
    try:
        response = requests.post(f"{BASE_URL}/ask-video", json=payload)
        
        if response.status_code == 404:
            error_data = response.json()
            print(f"{Fore.GREEN}✓ Error manejado correctamente (404){Style.RESET_ALL}")
            print(f"\n{Fore.RED}Error:{Style.RESET_ALL} {error_data.get('detail', '')}")
        else:
            print(f"{Fore.YELLOW}⚠ Código inesperado: {response.status_code}{Style.RESET_ALL}")
            
    except Exception as e:
        print(f"{Fore.RED}✗ Error: {e}{Style.RESET_ALL}")


if __name__ == "__main__":
    print(f"\n{Fore.MAGENTA}{Style.BRIGHT}")
    print("╔═══════════════════════════════════════════════════════════════════╗")
    print("║                                                                   ║")
    print("║       🎥 DEMO: Sistema de Consulta de Videos por ID 🎥          ║")
    print("║                                                                   ║")
    print("╚═══════════════════════════════════════════════════════════════════╝")
    print(f"{Style.RESET_ALL}")
    
    try:
        # Demo 1: Listar videos
        available_videos = demo_list_videos()
        
        if available_videos:
            # Demo 2: Consultar un video
            demo_ask_video(available_videos[0])
            
            # Demo 3: Diferentes formatos
            demo_compare_formats(available_videos[0])
            
            # Demo 4: Múltiples videos
            demo_multiple_videos()
            
            # Demo 5: Error handling
            demo_invalid_video()
        
        print(f"\n{Fore.MAGENTA}{Style.BRIGHT}")
        print("╔═══════════════════════════════════════════════════════════════════╗")
        print("║                                                                   ║")
        print("║                    ✅ DEMOS COMPLETADOS ✅                        ║")
        print("║                                                                   ║")
        print("╚═══════════════════════════════════════════════════════════════════╝")
        print(f"{Style.RESET_ALL}\n")
        
    except requests.exceptions.ConnectionError:
        print(f"\n{Fore.RED}✗ Error de conexión{Style.RESET_ALL}")
        print(f"{Fore.YELLOW}Asegúrate de que el servidor esté corriendo:{Style.RESET_ALL}")
        print(f"  uvicorn main:app --reload")
    except Exception as e:
        print(f"\n{Fore.RED}✗ Error inesperado: {e}{Style.RESET_ALL}")
