# 🎥 Ejemplos de Chat con Video

## 📚 Contenido

1. [Ejemplo más simple (cURL)](#1-ejemplo-más-simple-curl)
2. [Ejemplo con Python (Una pregunta)](#2-ejemplo-con-python-una-pregunta)
3. [Ejemplo con Python (Múltiples preguntas)](#3-ejemplo-con-python-múltiples-preguntas)
4. [Chat Interactivo](#4-chat-interactivo)

---

## 1. Ejemplo más simple (cURL)

### Una sola pregunta:

```bash
curl -X POST http://localhost:8000/ask-video \
  -H "Content-Type: application/json" \
  -d '{
    "question": "¿De qué trata este módulo?",
    "video_id": "modulo_1",
    "category": "geomecanica",
    "format": "plain"
  }'
```

### Para ver solo la respuesta (sin JSON):

```bash
curl -X POST http://localhost:8000/ask-video \
  -H "Content-Type: application/json" \
  -d '{
    "question": "¿De qué trata este módulo?",
    "video_id": "modulo_1",
    "category": "geomecanica",
    "format": "plain"
  }' 2>/dev/null | python3 -c "import sys,json; print(json.load(sys.stdin)['answer_plain'])"
```

---

## 2. Ejemplo con Python (Una pregunta)

### Código mínimo:

```python
import requests

# Hacer una pregunta a un video
response = requests.post('http://localhost:8000/ask-video', json={
    'question': '¿De qué trata este módulo?',
    'video_id': 'modulo_1',
    'category': 'geomecanica',
    'format': 'plain'
})

# Mostrar respuesta
print(response.json()['answer_plain'])
```

### Ejecutar:

```bash
python3 -c "
import requests
r = requests.post('http://localhost:8000/ask-video', json={
    'question': '¿De qué trata este módulo?',
    'video_id': 'modulo_1',
    'format': 'plain'
})
print(r.json()['answer_plain'])
"
```

---

## 3. Ejemplo con Python (Múltiples preguntas)

### Archivo: `ejemplo_chat_video.py`

```python
import requests

BASE_URL = "http://localhost:8000"
VIDEO_ID = "modulo_1"

def chatear(pregunta):
    """Hace una pregunta al video."""
    response = requests.post(f"{BASE_URL}/ask-video", json={
        "question": pregunta,
        "video_id": VIDEO_ID,
        "category": "geomecanica",
        "format": "plain"
    })
    return response.json()['answer_plain']

# Hacer varias preguntas
preguntas = [
    "¿De qué trata este módulo?",
    "¿Cuáles son los conceptos principales?",
    "Resume lo más importante en 3 puntos"
]

for i, pregunta in enumerate(preguntas, 1):
    print(f"\n{'='*70}")
    print(f"❓ PREGUNTA {i}: {pregunta}")
    print('='*70)

    respuesta = chatear(pregunta)
    print(f"\n💡 RESPUESTA:\n{respuesta}\n")
```

### Ejecutar:

```bash
python ejemplo_chat_video.py
```

---

## 4. Chat Interactivo

### El más completo - Archivo: `chat_interactivo.py`

Este script permite:

- ✅ Ver videos disponibles
- ✅ Seleccionar el video que quieres consultar
- ✅ Hacer preguntas ilimitadas
- ✅ Cambiar de video sin salir

```python
import requests

BASE_URL = "http://localhost:8000"

def hacer_pregunta(video_id, pregunta):
    response = requests.post(f"{BASE_URL}/ask-video", json={
        "question": pregunta,
        "video_id": video_id,
        "category": "geomecanica",
        "format": "plain"
    })
    return response.json()['answer_plain'].split('\n---')[0]

# Seleccionar video
video = "modulo_1"

# Loop de chat
while True:
    pregunta = input("\n❓ Tu pregunta (o 'salir'): ").strip()

    if pregunta.lower() in ['salir', 'exit']:
        break

    respuesta = hacer_pregunta(video, pregunta)
    print(f"\n💡 {respuesta}\n")
```

### Ejecutar versión completa:

```bash
python chat_interactivo.py
```

---

## 🎯 Casos de Uso Rápidos

### 1. Pregunta rápida desde terminal

```bash
# Cambiar "modulo_1" por el video que quieras
VIDEO="modulo_1"
PREGUNTA="¿De qué trata este módulo?"

curl -X POST http://localhost:8000/ask-video \
  -H "Content-Type: application/json" \
  -d "{\"question\":\"$PREGUNTA\",\"video_id\":\"$VIDEO\",\"format\":\"plain\"}" \
  2>/dev/null | python3 -c "import sys,json; print(json.load(sys.stdin)['answer_plain'])"
```

### 2. Ver videos disponibles

```bash
curl http://localhost:8000/videos/geomecanica 2>/dev/null | python3 -m json.tool
```

### 3. Consultar todos los módulos con la misma pregunta

```bash
for i in {1..5}; do
  echo "=== MÓDULO $i ==="
  curl -X POST http://localhost:8000/ask-video \
    -H "Content-Type: application/json" \
    -d "{\"question\":\"Resume este módulo brevemente\",\"video_id\":\"modulo_$i\",\"format\":\"plain\"}" \
    2>/dev/null | python3 -c "import sys,json; print(json.load(sys.stdin)['answer_plain'].split('\n---')[0])"
  echo ""
done
```

---

## 📋 Formato de Respuesta

### Con `format: "plain"` (recomendado):

```json
{
  "question": "¿De qué trata este módulo?",
  "video_id": "modulo_1",
  "category": "geomecanica",
  "format": "plain",
  "answer_plain": "El Módulo 1 trata sobre...\n\n---\n📹 Fuente:\n• Video: modulo_1 (...)"
}
```

### Con `format: "html"`:

```json
{
  "question": "¿De qué trata este módulo?",
  "video_id": "modulo_1",
  "category": "geomecanica",
  "format": "html",
  "answer_html": "<div><h2>Respuesta del Video MODULO_1</h2><p>El Módulo 1...</p>..."
}
```

### Con `format: "both"`:

```json
{
  "question": "¿De qué trata este módulo?",
  "video_id": "modulo_1",
  "category": "geomecanica",
  "format": "both",
  "answer_plain": "El Módulo 1 trata sobre...",
  "answer_html": "<div><h2>Respuesta del Video MODULO_1</h2>..."
}
```

---

## ✨ Ejemplos Avanzados

### Función reutilizable en Python:

```python
import requests
from typing import Optional

def consultar_video(
    video_id: str,
    pregunta: str,
    categoria: str = "geomecanica",
    solo_respuesta: bool = True
) -> str:
    """
    Consulta un video específico.

    Args:
        video_id: ID del video (ej: "modulo_1")
        pregunta: La pregunta a hacer
        categoria: Categoría del video (default: "geomecanica")
        solo_respuesta: Si True, retorna solo la respuesta sin fuentes

    Returns:
        La respuesta del video
    """
    response = requests.post('http://localhost:8000/ask-video', json={
        'question': pregunta,
        'video_id': video_id,
        'category': categoria,
        'format': 'plain'
    })

    if response.status_code == 200:
        respuesta = response.json()['answer_plain']
        if solo_respuesta:
            # Quitar la sección de fuentes
            respuesta = respuesta.split('\n---')[0]
        return respuesta
    else:
        return f"Error: {response.json().get('detail', 'Error desconocido')}"

# Uso:
respuesta = consultar_video("modulo_1", "¿De qué trata este módulo?")
print(respuesta)
```

### Chat con historial:

```python
import requests

def chat_con_historial(video_id: str):
    """Chat que mantiene historial de preguntas y respuestas."""
    historial = []

    print(f"🎥 Chateando con: {video_id}")
    print("Escribe 'historial' para ver conversación previa")
    print("Escribe 'salir' para terminar\n")

    while True:
        pregunta = input("❓ Pregunta: ").strip()

        if pregunta.lower() == 'salir':
            break

        if pregunta.lower() == 'historial':
            print("\n📜 Historial:")
            for i, (p, r) in enumerate(historial, 1):
                print(f"\n{i}. P: {p}")
                print(f"   R: {r[:100]}...")
            continue

        response = requests.post('http://localhost:8000/ask-video', json={
            'question': pregunta,
            'video_id': video_id,
            'format': 'plain'
        })

        respuesta = response.json()['answer_plain'].split('\n---')[0]
        historial.append((pregunta, respuesta))

        print(f"\n💡 {respuesta}\n")

# Uso:
chat_con_historial("modulo_1")
```

---

## 🚀 Scripts Incluidos

1. **`ejemplo_chat_video.py`** - Múltiples preguntas predefinidas
2. **`ejemplo_chat_video.sh`** - Versión en Bash con cURL
3. **`chat_interactivo.py`** - Chat interactivo completo

### Ejecutar:

```bash
# Python con preguntas predefinidas
python ejemplo_chat_video.py

# Bash con cURL
bash ejemplo_chat_video.sh

# Chat interactivo
python chat_interactivo.py
```

---

## 📝 Notas

- El parámetro `category` es opcional, por defecto es `"geomecanica"`
- El parámetro `format` es opcional, por defecto es `"both"`
- La respuesta incluye fuentes al final (después de `---`)
- Para obtener solo la respuesta sin fuentes, usa `.split('\n---')[0]`

---

**Fecha:** 24 de octubre de 2025  
**Archivos de ejemplo incluidos:**

- `ejemplo_chat_video.py`
- `ejemplo_chat_video.sh`
- `chat_interactivo.py`
