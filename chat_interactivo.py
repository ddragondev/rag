"""
🎥 Chat Interactivo con Video

Ejemplo simple para chatear con un video específico de forma interactiva.
"""

import requests
import sys

# Configuración
BASE_URL = "http://localhost:8000"

def listar_videos():
    """Muestra los videos disponibles."""
    try:
        response = requests.get(f"{BASE_URL}/videos/geomecanica")
        if response.status_code == 200:
            data = response.json()
            return list(data['videos'].keys())
        return []
    except:
        return []


def hacer_pregunta(video_id: str, pregunta: str):
    """Hace una pregunta al video."""
    payload = {
        "question": pregunta,
        "video_id": video_id,
        "category": "geomecanica",
        "format": "plain"
    }
    
    try:
        response = requests.post(f"{BASE_URL}/ask-video", json=payload)
        
        if response.status_code == 200:
            data = response.json()
            # Extraer solo la respuesta sin las fuentes
            respuesta_completa = data.get('answer_plain', '')
            respuesta = respuesta_completa.split('\n---')[0]  # Quitar la sección de fuentes
            return respuesta
        else:
            error = response.json().get('detail', 'Error desconocido')
            return f"❌ Error: {error}"
    except Exception as e:
        return f"❌ Error de conexión: {e}"


def main():
    print("\n" + "="*70)
    print("🎥 CHAT INTERACTIVO CON VIDEO")
    print("="*70 + "\n")
    
    # Paso 1: Listar videos disponibles
    print("📹 Videos disponibles:")
    videos = listar_videos()
    
    if not videos:
        print("❌ No se pudieron obtener los videos.")
        print("   Asegúrate de que el servidor esté corriendo:")
        print("   uvicorn main:app --reload")
        return
    
    for i, video_id in enumerate(videos, 1):
        print(f"   {i}. {video_id}")
    
    # Paso 2: Seleccionar video
    print("\n" + "-"*70)
    while True:
        try:
            seleccion = input(f"\n👉 Selecciona un video (1-{len(videos)}) o Enter para modulo_1: ").strip()
            
            if seleccion == "":
                video_seleccionado = "modulo_1"
                break
            
            num = int(seleccion)
            if 1 <= num <= len(videos):
                video_seleccionado = videos[num - 1]
                break
            else:
                print(f"⚠️  Por favor ingresa un número entre 1 y {len(videos)}")
        except ValueError:
            print("⚠️  Por favor ingresa un número válido")
    
    print(f"\n✅ Video seleccionado: {video_seleccionado}")
    print("\n" + "="*70)
    print(f"💬 CHATEANDO CON: {video_seleccionado.upper()}")
    print("="*70)
    print("\n💡 Tip: Escribe 'salir' o 'exit' para terminar")
    print("💡 Tip: Escribe 'cambiar' para elegir otro video\n")
    
    # Paso 3: Loop de preguntas
    while True:
        print("-"*70)
        pregunta = input("\n❓ Tu pregunta: ").strip()
        
        if not pregunta:
            continue
        
        if pregunta.lower() in ['salir', 'exit', 'quit']:
            print("\n👋 ¡Hasta luego!")
            break
        
        if pregunta.lower() == 'cambiar':
            main()  # Reiniciar para elegir otro video
            return
        
        print("\n⏳ Pensando...\n")
        respuesta = hacer_pregunta(video_seleccionado, pregunta)
        
        print("💡 RESPUESTA:")
        print("-"*70)
        print(respuesta)
        print()


if __name__ == "__main__":
    try:
        main()
        print("\n" + "="*70)
        print("✅ Chat finalizado")
        print("="*70 + "\n")
    except KeyboardInterrupt:
        print("\n\n👋 Chat interrumpido. ¡Hasta luego!\n")
    except Exception as e:
        print(f"\n❌ Error inesperado: {e}\n")
