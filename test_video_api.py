"""
Script de prueba para el endpoint /ask-video

Prueba las consultas a videos específicos por ID.
"""

import requests
import json

# URL base de la API
BASE_URL = "http://localhost:8000"

def test_list_videos():
    """Prueba el endpoint para listar videos disponibles."""
    print("=" * 60)
    print("🎥 TEST 1: Listar videos disponibles")
    print("=" * 60)
    
    response = requests.get(f"{BASE_URL}/videos/geomecanica")
    
    if response.status_code == 200:
        data = response.json()
        print(f"✅ Categoría: {data['category']}")
        print(f"✅ Total de videos: {data['total_videos']}")
        print("\n📹 Videos disponibles:")
        
        for video_id, info in data['videos'].items():
            print(f"\n   ID: {video_id}")
            print(f"   Archivo: {info['filename'][:60]}...")
        
        return list(data['videos'].keys())
    else:
        print(f"❌ Error: {response.status_code}")
        print(response.json())
        return []


def test_ask_video(video_id: str):
    """Prueba una consulta a un video específico."""
    print("\n" + "=" * 60)
    print(f"🎥 TEST 2: Consultar video {video_id}")
    print("=" * 60)
    
    # Test con formato plain
    payload = {
        "question": "¿Cuáles son los conceptos principales que se cubren en este módulo?",
        "video_id": video_id,
        "category": "geomecanica",
        "format": "plain"
    }
    
    print(f"\n📝 Pregunta: {payload['question']}")
    print(f"📹 Video ID: {video_id}")
    print(f"📂 Categoría: {payload['category']}")
    print("\n⏳ Consultando...")
    
    response = requests.post(f"{BASE_URL}/ask-video", json=payload)
    
    if response.status_code == 200:
        data = response.json()
        print("\n✅ Respuesta recibida:")
        print("-" * 60)
        print(data.get('answer_plain', 'No hay respuesta en texto plano'))
        print("-" * 60)
    else:
        print(f"\n❌ Error: {response.status_code}")
        print(response.json())


def test_ask_video_html(video_id: str):
    """Prueba una consulta con formato HTML."""
    print("\n" + "=" * 60)
    print(f"🎥 TEST 3: Consultar video {video_id} (formato HTML)")
    print("=" * 60)
    
    payload = {
        "question": "Resume los puntos más importantes de este módulo",
        "video_id": video_id,
        "category": "geomecanica",
        "format": "html"
    }
    
    print(f"\n📝 Pregunta: {payload['question']}")
    print(f"📹 Video ID: {video_id}")
    print("\n⏳ Consultando...")
    
    response = requests.post(f"{BASE_URL}/ask-video", json=payload)
    
    if response.status_code == 200:
        data = response.json()
        print("\n✅ Respuesta HTML recibida:")
        print("-" * 60)
        # Mostrar solo primeros 500 caracteres del HTML
        html = data.get('answer_html', 'No hay respuesta HTML')
        print(html[:500] + "...")
        print("-" * 60)
    else:
        print(f"\n❌ Error: {response.status_code}")
        print(response.json())


def test_ask_video_both(video_id: str):
    """Prueba una consulta con ambos formatos."""
    print("\n" + "=" * 60)
    print(f"🎥 TEST 4: Consultar video {video_id} (ambos formatos)")
    print("=" * 60)
    
    payload = {
        "question": "¿Qué es la geomecánica según este módulo?",
        "video_id": video_id,
        "category": "geomecanica",
        "format": "both"
    }
    
    print(f"\n📝 Pregunta: {payload['question']}")
    print(f"📹 Video ID: {video_id}")
    print("\n⏳ Consultando...")
    
    response = requests.post(f"{BASE_URL}/ask-video", json=payload)
    
    if response.status_code == 200:
        data = response.json()
        print("\n✅ Respuesta recibida en ambos formatos:")
        print("\n📄 TEXTO PLANO:")
        print("-" * 60)
        print(data.get('answer_plain', 'No hay respuesta en texto plano')[:300] + "...")
        print("-" * 60)
        print("\n🌐 HTML:")
        print("-" * 60)
        print(data.get('answer_html', 'No hay respuesta HTML')[:300] + "...")
        print("-" * 60)
    else:
        print(f"\n❌ Error: {response.status_code}")
        print(response.json())


def test_invalid_video_id():
    """Prueba con un video_id inválido."""
    print("\n" + "=" * 60)
    print("🎥 TEST 5: Probar con video_id inválido")
    print("=" * 60)
    
    payload = {
        "question": "¿Qué contiene este video?",
        "video_id": "modulo_999",
        "category": "geomecanica",
        "format": "plain"
    }
    
    print(f"\n📹 Video ID inválido: {payload['video_id']}")
    print("⏳ Consultando...")
    
    response = requests.post(f"{BASE_URL}/ask-video", json=payload)
    
    if response.status_code == 404:
        print("\n✅ Error manejado correctamente:")
        error_data = response.json()
        print(f"   Mensaje: {error_data.get('detail', 'Error desconocido')}")
    else:
        print(f"\n⚠️ Respuesta inesperada: {response.status_code}")
        print(response.json())


def test_compare_with_pdf():
    """Compara una consulta al endpoint de PDFs vs Videos."""
    print("\n" + "=" * 60)
    print("🎥 TEST 6: Comparar PDF vs Video")
    print("=" * 60)
    
    question = "¿Qué es la geomecánica?"
    
    # Consultar PDFs
    print("\n📚 Consultando PDFs...")
    pdf_payload = {
        "question": question,
        "category": "geomecanica",
        "format": "plain"
    }
    pdf_response = requests.post(f"{BASE_URL}/ask", json=pdf_payload)
    
    # Consultar Video
    print("📹 Consultando Video (módulo_1)...")
    video_payload = {
        "question": question,
        "video_id": "modulo_1",
        "category": "geomecanica",
        "format": "plain"
    }
    video_response = requests.post(f"{BASE_URL}/ask-video", json=video_payload)
    
    if pdf_response.status_code == 200 and video_response.status_code == 200:
        print("\n✅ Ambas consultas exitosas\n")
        
        print("📚 RESPUESTA DE PDFs:")
        print("-" * 60)
        print(pdf_response.json().get('answer_plain', '')[:400] + "...")
        print("-" * 60)
        
        print("\n📹 RESPUESTA DE VIDEO:")
        print("-" * 60)
        print(video_response.json().get('answer_plain', '')[:400] + "...")
        print("-" * 60)
    else:
        print("\n❌ Una o ambas consultas fallaron")


if __name__ == "__main__":
    print("\n🚀 Iniciando pruebas del sistema de consulta de videos")
    print("=" * 60)
    
    try:
        # Test 1: Listar videos disponibles
        available_videos = test_list_videos()
        
        if available_videos:
            # Test 2-4: Consultar el primer video
            first_video = available_videos[0]
            test_ask_video(first_video)
            test_ask_video_html(first_video)
            test_ask_video_both(first_video)
            
            # Test 5: Video inválido
            test_invalid_video_id()
            
            # Test 6: Comparar PDFs vs Videos
            test_compare_with_pdf()
        else:
            print("\n⚠️ No se encontraron videos para probar")
        
        print("\n" + "=" * 60)
        print("✅ Pruebas completadas")
        print("=" * 60)
        
    except requests.exceptions.ConnectionError:
        print("\n❌ Error: No se puede conectar a la API")
        print("   Asegúrate de que el servidor esté corriendo en http://localhost:8000")
    except Exception as e:
        print(f"\n❌ Error inesperado: {e}")
