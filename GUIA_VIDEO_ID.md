# 🎥 Guía Rápida: Consultar Videos por ID

## 📋 Resumen

Ahora puedes consultar videos específicos usando su ID. El sistema:

- ✅ Carga solo la transcripción del video solicitado
- ✅ Usa caché para respuestas rápidas
- ✅ Soporta los mismos formatos que PDFs (html/plain/both)
- ✅ Proporciona contexto específico del video

---

## 🚀 Uso Rápido

### 1️⃣ Ver videos disponibles

```bash
curl http://localhost:8000/videos/geomecanica
```

**Respuesta:**

```json
{
  "category": "geomecanica",
  "total_videos": 5,
  "videos": {
    "modulo_1": {
      "filename": "Modulo_1_-_Profundicemos_en_las_Generalidades_de_Geomecanica_Academi_esp.txt",
      "path": "videos/geomecanica/Modulo_1_-_Profundicemos_en_las_Generalidades_de_Geomecanica_Academi_esp.txt"
    },
    "modulo_2": {
      "filename": "Modulo_2_-_Causas_o_factores_de_las_caidas_de_rocas_spa.txt",
      "path": "videos/geomecanica/Modulo_2_-_Causas_o_factores_de_las_caidas_de_rocas_spa.txt"
    },
    ...
  }
}
```

---

### 2️⃣ Consultar un video específico

```bash
curl -X POST http://localhost:8000/ask-video \
  -H "Content-Type: application/json" \
  -d '{
    "question": "¿Cuáles son los conceptos principales que se cubren?",
    "video_id": "modulo_1",
    "category": "geomecanica",
    "format": "plain"
  }'
```

**Respuesta:**

```json
{
  "question": "¿Cuáles son los conceptos principales que se cubren?",
  "video_id": "modulo_1",
  "category": "geomecanica",
  "format": "plain",
  "answer_plain": "El Módulo 1 cubre los siguientes conceptos principales:\n\n1. Introducción a la Geomecánica Básica...\n\n---\n📹 Fuente:\n• Video: modulo_1 (videos/geomecanica/Modulo_1_-_Profundicemos_en_las_Generalidades_de_Geomecanica_Academi_esp.txt)"
}
```

---

## 📡 Endpoints Disponibles

### 1. Listar Videos

**GET** `/videos/{category}`

Retorna todos los videos disponibles en una categoría.

**Parámetros:**

- `category` (path): Categoría de videos (ej: "geomecanica")

**Ejemplo:**

```bash
curl http://localhost:8000/videos/geomecanica
```

---

### 2. Consultar Video

**POST** `/ask-video`

Consulta un video específico por su ID.

**Body JSON:**

```json
{
  "question": "¿Qué es la geomecánica?",
  "video_id": "modulo_1",
  "category": "geomecanica", // Opcional, default: "geomecanica"
  "format": "plain" // Opcional: "html", "plain", "both" (default: "both")
}
```

**Respuesta con format="plain":**

```json
{
  "question": "...",
  "video_id": "modulo_1",
  "category": "geomecanica",
  "format": "plain",
  "answer_plain": "Respuesta en texto plano...\n\n---\n📹 Fuente:\n• Video: modulo_1 (...)"
}
```

**Respuesta con format="html":**

```json
{
  "question": "...",
  "video_id": "modulo_1",
  "category": "geomecanica",
  "format": "html",
  "answer_html": "<div><h2>Respuesta del Video MODULO_1</h2>...</div>"
}
```

**Respuesta con format="both":**

```json
{
  "question": "...",
  "video_id": "modulo_1",
  "category": "geomecanica",
  "format": "both",
  "answer_plain": "Respuesta en texto plano...",
  "answer_html": "<div><h2>Respuesta del Video MODULO_1</h2>...</div>"
}
```

---

## 🎯 IDs de Videos

Los IDs de videos se generan automáticamente desde los nombres de archivo:

| Archivo                                                                                       | Video ID   |
| --------------------------------------------------------------------------------------------- | ---------- |
| `Modulo_1_-_Profundicemos_en_las_Generalidades_de_Geomecanica_Academi_esp.txt`                | `modulo_1` |
| `Modulo_2_-_Causas_o_factores_de_las_caidas_de_rocas_spa.txt`                                 | `modulo_2` |
| `Modulo_3_-_Tipos_de_calidades_de_macizos_Rocosos_spa.txt`                                    | `modulo_3` |
| `Modulo_4_-_Condiciones_Geomecanicas_en_labores_mineras_spa.txt`                              | `modulo_4` |
| `Modulo_5_-_Profundices_en_los_errores_comunes_en_el_control_del_terreno_subterraneo_spa.txt` | `modulo_5` |

---

## 🐍 Uso con Python

### Listar videos disponibles

```python
import requests

response = requests.get('http://localhost:8000/videos/geomecanica')
data = response.json()

print(f"Total de videos: {data['total_videos']}")
for video_id in data['videos'].keys():
    print(f"  - {video_id}")
```

### Consultar un video

```python
import requests

response = requests.post('http://localhost:8000/ask-video', json={
    'question': '¿Qué es la geomecánica?',
    'video_id': 'modulo_1',
    'category': 'geomecanica',
    'format': 'plain'
})

data = response.json()
print(data['answer_plain'])
```

### Consultar múltiples videos

```python
import requests

# Obtener lista de videos
videos_response = requests.get('http://localhost:8000/videos/geomecanica')
video_ids = list(videos_response.json()['videos'].keys())

# Consultar cada video
question = "¿Cuáles son los puntos principales?"

for video_id in video_ids[:3]:  # Primeros 3 videos
    print(f"\n{'='*60}")
    print(f"📹 Video: {video_id}")
    print('='*60)

    response = requests.post('http://localhost:8000/ask-video', json={
        'question': question,
        'video_id': video_id,
        'format': 'plain'
    })

    answer = response.json()['answer_plain']
    print(answer[:300] + "...")
```

---

## ⚡ Ventajas vs Consulta General

### Consulta General de PDFs (`/ask`)

```bash
curl -X POST http://localhost:8000/ask \
  -H "Content-Type: application/json" \
  -d '{
    "question": "¿Qué es la geomecánica?",
    "category": "geomecanica",
    "format": "plain"
  }'
```

- ✅ Busca en **todos los PDFs** de la categoría
- ✅ Respuesta más completa y general
- ⚠️ Puede ser más lenta (más documentos)

### Consulta por Video ID (`/ask-video`)

```bash
curl -X POST http://localhost:8000/ask-video \
  -H "Content-Type: application/json" \
  -d '{
    "question": "¿Qué es la geomecánica?",
    "video_id": "modulo_1",
    "category": "geomecanica",
    "format": "plain"
  }'
```

- ✅ Busca solo en **un video específico**
- ✅ Respuesta contextualizada al video
- ✅ Más rápida (menos documentos)
- ✅ Útil cuando sabes el video exacto

---

## 🧪 Pruebas

Ejecuta el script de prueba incluido:

```bash
python test_video_api.py
```

**El script prueba:**

1. ✅ Listar videos disponibles
2. ✅ Consulta con formato plain
3. ✅ Consulta con formato HTML
4. ✅ Consulta con ambos formatos
5. ✅ Manejo de video_id inválido
6. ✅ Comparación PDFs vs Videos

---

## 📂 Estructura de Archivos

```
videos/
└── geomecanica/
    ├── Modulo_1_-_Profundicemos_en_las_Generalidades_de_Geomecanica_Academi_esp.txt
    ├── Modulo_2_-_Causas_o_factores_de_las_caidas_de_rocas_spa.txt
    ├── Modulo_3_-_Tipos_de_calidades_de_macizos_Rocosos_spa.txt
    ├── Modulo_4_-_Condiciones_Geomecanicas_en_labores_mineras_spa.txt
    └── Modulo_5_-_Profundices_en_los_errores_comunes_en_el_control_del_terreno_subterraneo_spa.txt

chroma_db/
├── video_geomecanica_modulo_1/  ← Caché del módulo 1
├── video_geomecanica_modulo_2/  ← Caché del módulo 2
└── ...
```

---

## ❓ Errores Comunes

### Error: "Video ID not found"

```json
{
  "detail": "Video ID 'modulo_99' not found. Available IDs: ['modulo_1', 'modulo_2', 'modulo_3', 'modulo_4', 'modulo_5']"
}
```

**Solución:** Verifica los IDs disponibles con `GET /videos/geomecanica`

---

### Error: "No videos found in category"

```json
{
  "detail": "No videos found in category 'otra_categoria'"
}
```

**Solución:** Asegúrate de que la carpeta `videos/categoria` existe y tiene archivos `.txt`

---

## 🎯 Casos de Uso

### 1. Sistema de preguntas sobre cursos

```python
# Usuario selecciona un módulo específico
modulo_seleccionado = "modulo_3"

response = requests.post('http://localhost:8000/ask-video', json={
    'question': pregunta_usuario,
    'video_id': modulo_seleccionado,
    'format': 'html'
})
```

### 2. Comparar respuestas entre módulos

```python
question = "¿Qué tipos de rocas se mencionan?"

for i in range(1, 6):
    video_id = f"modulo_{i}"
    response = requests.post('http://localhost:8000/ask-video', json={
        'question': question,
        'video_id': video_id,
        'format': 'plain'
    })
    print(f"\nMódulo {i}:")
    print(response.json()['answer_plain'][:200])
```

### 3. Chat contextual de videos

```python
# Mantener conversación sobre un video específico
video_actual = "modulo_1"

preguntas = [
    "¿De qué trata este módulo?",
    "¿Cuáles son los conceptos clave?",
    "¿Qué ejemplos se mencionan?"
]

for pregunta in preguntas:
    response = requests.post('http://localhost:8000/ask-video', json={
        'question': pregunta,
        'video_id': video_actual,
        'format': 'plain'
    })
    print(f"\nP: {pregunta}")
    print(f"R: {response.json()['answer_plain']}\n")
```

---

## 🚀 Próximas Mejoras

- [ ] Endpoint para buscar en múltiples videos a la vez
- [ ] Soporte para timestamps en las respuestas
- [ ] Endpoint para agregar nuevas transcripciones
- [ ] Sistema de recomendación de videos relacionados
- [ ] Búsqueda semántica entre videos

---

**Fecha:** 24 de octubre de 2025  
**Estado:** ✅ Funcional y probado
