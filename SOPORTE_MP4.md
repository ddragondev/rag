# 🎥 Soporte para Videos MP4 - Guía Completa

## 🎯 Cómo Funciona

La integración de MP4 con el sistema RAG funciona en **3 pasos**:

1. **Extracción de audio** del video (usando ffmpeg)
2. **Transcripción** del audio con Whisper de OpenAI
3. **Indexación** de la transcripción en el vectorstore (igual que PDFs)

---

## 📋 Requisitos Previos

### 1. Instalar ffmpeg

#### macOS:

```bash
brew install ffmpeg
```

#### Linux (Ubuntu/Debian):

```bash
sudo apt update
sudo apt install ffmpeg
```

#### Windows:

```bash
choco install ffmpeg
# O descargar desde https://ffmpeg.org/download.html
```

### 2. Verificar instalación:

```bash
ffmpeg -version
```

### 3. Instalar dependencia adicional:

```bash
pip install openai
```

---

## 🚀 Uso Básico

### Opción 1: Procesar un solo video

```python
from mp4_processor import MP4Processor
import os
from dotenv import load_dotenv

load_dotenv()
processor = MP4Processor(os.getenv("OPENAI_API_KEY"))

# Procesar video
documents = processor.process_video("docs/compliance/video_compliance.mp4")

print(f"Transcripción: {documents[0].page_content[:200]}...")
```

### Opción 2: Procesar carpeta completa

```python
from mp4_processor import load_mp4_documents
import os

# Procesar todos los MP4 de una carpeta
documents = load_mp4_documents(
    directory="docs/compliance",
    openai_api_key=os.getenv("OPENAI_API_KEY")
)

print(f"Procesados {len(documents)} videos")
```

---

## 🔧 Integrar con el Sistema Actual

### Modificar `main.py` para soportar MP4

Agrega esta función después de `load_documents_from_category`:

```python
from mp4_processor import load_mp4_documents

def load_documents_from_category_mixed(category: str):
    """
    Carga PDFs y MP4s de una categoría.
    """
    category = normalize_category(category)
    docs_path = f"docs/{category}"

    if not os.path.exists(docs_path):
        raise HTTPException(status_code=404, detail=f"Category '{category}' not found.")

    all_documents = []

    # 1. Cargar PDFs (código existente)
    pdf_files = glob.glob(os.path.join(docs_path, "*.pdf"))
    for pdf_file in pdf_files:
        loader = PyPDFLoader(pdf_file)
        all_documents.extend(loader.load())

    # 2. Cargar MP4s (NUEVO)
    mp4_files = glob.glob(os.path.join(docs_path, "*.mp4"))
    if mp4_files:
        api_key = os.getenv("OPENAI_API_KEY")
        mp4_docs = load_mp4_documents(docs_path, api_key)
        all_documents.extend(mp4_docs)

    if not all_documents:
        raise HTTPException(
            status_code=404,
            detail=f"No PDF or MP4 files found in category '{category}'."
        )

    return all_documents
```

Luego actualiza `get_or_create_vectorstore` para usar esta función:

```python
# Reemplaza esta línea:
documents = load_documents_from_category(category)

# Por esta:
documents = load_documents_from_category_mixed(category)
```

---

## 📂 Estructura de Carpetas

```
docs/
├── compliance/
│   ├── documento1.pdf
│   ├── documento2.pdf
│   ├── video_compliance.mp4      ← Nuevo
│   └── capacitacion.mp4           ← Nuevo
└── geomecanica/
    ├── clase1.pdf
    └── tutorial_rmr.mp4            ← Nuevo
```

---

## 💻 Ejemplos de Uso

### Ejemplo 1: Consulta simple con video

```bash
curl -X POST http://localhost:8000/ask \
  -H "Content-Type: application/json" \
  -d '{
    "category": "compliance",
    "question": "¿Qué se mencionó sobre las políticas de seguridad en el video?",
    "format": "plain"
  }'
```

### Ejemplo 2: Script Python

```python
import requests

response = requests.post('http://localhost:8000/ask', json={
    'question': '¿Qué temas se cubrieron en los videos de capacitación?',
    'category': 'compliance',
    'format': 'plain'
})

print(response.json()['answer_plain'])
```

---

## ⚙️ Opciones Avanzadas

### 1. Extraer también frames visuales

```python
# Con análisis visual de frames
docs = processor.process_video(
    "video.mp4",
    extract_visual=True,  # Activar extracción de frames
    fps=0.1  # 1 frame cada 10 segundos
)
```

### 2. Personalizar FPS de frames

```python
# Más frames (más detalle, más lento)
docs = processor.process_video("video.mp4", extract_visual=True, fps=1)  # 1 por segundo

# Menos frames (menos detalle, más rápido)
docs = processor.process_video("video.mp4", extract_visual=True, fps=0.05)  # 1 cada 20s
```

### 3. Análisis con GPT-4 Vision (próximamente)

Puedes extender el procesador para analizar frames con GPT-4 Vision:

```python
def analyze_frame_with_vision(self, frame_path: str) -> str:
    """Analiza un frame con GPT-4 Vision."""
    import base64

    with open(frame_path, "rb") as image_file:
        base64_image = base64.b64encode(image_file.read()).decode('utf-8')

    response = self.client.chat.completions.create(
        model="gpt-4-vision-preview",
        messages=[{
            "role": "user",
            "content": [
                {"type": "text", "text": "Describe qué ves en esta imagen del video"},
                {
                    "type": "image_url",
                    "image_url": {"url": f"data:image/jpeg;base64,{base64_image}"}
                }
            ]
        }],
        max_tokens=300
    )

    return response.choices[0].message.content
```

---

## 📊 Metadatos de Videos

Cada documento de video incluye metadatos útiles:

```python
{
    "source": "docs/compliance/video.mp4",
    "type": "video_transcription",
    "video_name": "video",
    "duration": 245.5  # segundos
}
```

---

## 💰 Costos

### Whisper API:

- **$0.006 por minuto** de audio
- Ejemplo: Video de 10 minutos = $0.06

### Comparación:

| Duración Video | Costo Whisper |
| -------------- | ------------- |
| 5 minutos      | $0.03         |
| 10 minutos     | $0.06         |
| 30 minutos     | $0.18         |
| 1 hora         | $0.36         |

---

## ⚡ Optimizaciones

### 1. Caché de transcripciones

Para evitar procesar videos repetidamente:

```python
import json
import hashlib

def get_cached_transcription(video_path: str) -> Optional[str]:
    """Busca transcripción en caché."""
    cache_dir = "cache/transcriptions"
    os.makedirs(cache_dir, exist_ok=True)

    # Hash del archivo para identificarlo
    with open(video_path, 'rb') as f:
        file_hash = hashlib.md5(f.read()).hexdigest()

    cache_file = os.path.join(cache_dir, f"{file_hash}.json")

    if os.path.exists(cache_file):
        with open(cache_file, 'r') as f:
            return json.load(f)['transcription']

    return None

def cache_transcription(video_path: str, transcription: str):
    """Guarda transcripción en caché."""
    cache_dir = "cache/transcriptions"

    with open(video_path, 'rb') as f:
        file_hash = hashlib.md5(f.read()).hexdigest()

    cache_file = os.path.join(cache_dir, f"{file_hash}.json")

    with open(cache_file, 'w') as f:
        json.dump({'transcription': transcription}, f)
```

### 2. Procesamiento en background

Para videos largos, procesar en background:

```python
from fastapi import BackgroundTasks

@app.post("/process-video")
async def process_video(
    category: str,
    video_filename: str,
    background_tasks: BackgroundTasks
):
    """Procesa un video en background."""
    background_tasks.add_task(
        process_video_async,
        category,
        video_filename
    )
    return {"status": "processing", "message": "Video being processed in background"}
```

---

## 🚨 Límites y Consideraciones

### Límites de Whisper API:

- **Tamaño máximo:** 25 MB por archivo
- **Formatos:** MP3, MP4, MPEG, MPGA, M4A, WAV, WEBM

### Solución para videos grandes:

```python
def split_audio(audio_path: str, chunk_duration: int = 600) -> List[str]:
    """Divide audio en chunks de X segundos (default: 10 min)."""
    output_pattern = audio_path.replace('.mp3', '_chunk_%03d.mp3')

    command = [
        'ffmpeg',
        '-i', audio_path,
        '-f', 'segment',
        '-segment_time', str(chunk_duration),
        '-c', 'copy',
        output_pattern
    ]

    subprocess.run(command, check=True)
    # Retornar lista de chunks creados
```

---

## 🧪 Testing

### Script de prueba:

```bash
# 1. Crear carpeta de prueba
mkdir -p docs/test_videos

# 2. Copiar un video de prueba
cp tu_video.mp4 docs/test_videos/

# 3. Ejecutar procesador
python mp4_processor.py
```

### Test completo con la API:

```bash
# 1. Agregar video a categoría existente
cp video.mp4 docs/compliance/

# 2. Reiniciar servidor (para reindexar)
# El servidor detectará el nuevo MP4 automáticamente

# 3. Consultar
curl -X POST http://localhost:8000/ask \
  -d '{"category": "compliance", "question": "Resume el video", "format": "plain"}'
```

---

## 📝 Notas Importantes

1. **Primera vez es lenta:** Extraer audio + transcribir puede tomar tiempo
2. **Caché funciona:** Una vez procesado, las consultas son igual de rápidas que PDFs
3. **Mixto funciona:** Puedes tener PDFs y MP4s en la misma categoría
4. **Idiomas:** Whisper soporta múltiples idiomas automáticamente

---

## 🎯 Casos de Uso

### ✅ Ideal para:

- Transcripciones de reuniones
- Videos de capacitación
- Tutoriales grabados
- Conferencias
- Entrevistas

### ⚠️ No ideal para:

- Videos muy largos (>2 horas, mejor dividir)
- Videos sin audio
- Contenido puramente visual sin narración

---

## 🔜 Próximas Mejoras

- [ ] Análisis automático de frames con GPT-4 Vision
- [ ] Detección de capítulos/secciones en el video
- [ ] Timestamps en las respuestas
- [ ] Soporte para subtítulos existentes (SRT)
- [ ] Procesamiento paralelo de múltiples videos

---

**Fecha de creación:** 24 de octubre de 2025  
**Estado:** ✅ Funcional (requiere ffmpeg + OpenAI API)
