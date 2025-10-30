"""
🎥 Ejemplo Simple: Chat con un Video Específico

Este script muestra cómo hacer múltiples preguntas a un mismo video.
"""

import requests

# Configuración
BASE_URL = "http://localhost:8000"
VIDEO_ID = "modulo_1"  # Cambia esto por el video que quieras consultar
CATEGORY = "geomecanica"

def chatear_con_video(video_id: str, pregunta: str, formato: str = "plain"):
    """
    Hace una pregunta a un video específico.
    
    Args:
        video_id: ID del video (ej: "modulo_1")
        pregunta: La pregunta que quieres hacer
        formato: "plain", "html", o "both" (default: "plain")
    
    Returns:
        La respuesta del video
    """
    payload = {
        "question": pregunta,
        "video_id": video_id,
        "category": CATEGORY,
        "format": formato
    }
    
    response = requests.post(f"{BASE_URL}/ask-video", json=payload)
    
    if response.status_code == 200:
        data = response.json()
        return data.get('answer_plain', data.get('answer_html', 'Sin respuesta'))
    else:
        return f"❌ Error: {response.json().get('detail', 'Error desconocido')}"


# ============================================
# 🎯 EJEMPLO DE USO
# ============================================

if __name__ == "__main__":
    print("=" * 70)
    print(f"🎥 CHAT CON VIDEO: {VIDEO_ID.upper()}")
    print("=" * 70)
    
    # Lista de preguntas para el video
    preguntas = [
        "¿De qué trata este módulo?",
        "¿Cuáles son los conceptos principales?",
        "¿Qué ejemplos se mencionan?",
        "Resume lo más importante en 3 puntos"
    ]
    
    # Hacer cada pregunta
    for i, pregunta in enumerate(preguntas, 1):
        print(f"\n{'─'*70}")
        print(f"❓ PREGUNTA {i}: {pregunta}")
        print('─'*70)
        
        respuesta = chatear_con_video(VIDEO_ID, pregunta)
        
        print(f"\n💡 RESPUESTA:\n")
        print(respuesta)
        print()
    
    print("=" * 70)
    print("✅ Chat completado")
    print("=" * 70)
