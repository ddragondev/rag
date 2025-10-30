# 📄 Resumen de Cambios: Respuesta en Texto Plano

## ✅ Cambios Implementados

### 1. **Endpoint `/ask` Actualizado**

Ahora devuelve **4 campos** en lugar de 2:

#### Antes:

```json
{
  "question": "...",
  "category": "...",
  "answer": "<p>Respuesta en HTML...</p>",
  "sources": "<ul><li>Fuente 1</li></ul>"
}
```

#### Después:

```json
{
  "question": "...",
  "category": "...",
  "answer": "<p>Respuesta en HTML...</p>",
  "answer_plain": "Respuesta en texto plano...",
  "sources": "<ul><li>Fuente 1</li></ul>",
  "sources_plain": "• Fuente 1\n• Fuente 2"
}
```

---

### 2. **Endpoint `/ask-stream` Actualizado**

Ahora envía streams para ambos formatos:

#### Eventos SSE:

1. `metadata` - Incluye `sources` y `sources_plain`
2. `html_start` - Inicia stream HTML
3. `html_content` - Chunks de HTML
4. `html_end` - Finaliza stream HTML
5. `plain_start` - Inicia stream texto plano
6. `plain_content` - Chunks de texto plano
7. `done` - Finalización completa

---

## 🎯 Casos de Uso

### Usar `answer` (HTML):

- ✅ Renderizar en páginas web
- ✅ Mostrar contenido con estilos Tailwind
- ✅ Interfaz visual rica

### Usar `answer_plain` (Texto Plano):

- ✅ Consola / CLI
- ✅ Logs del sistema
- ✅ Emails en texto plano
- ✅ Procesamiento posterior (NLP, análisis)
- ✅ Copiar/pegar fácil
- ✅ Accesibilidad (lectores de pantalla)

---

## 📊 Impacto en Rendimiento

⚠️ **IMPORTANTE:** Ahora se realizan **2 llamadas al LLM** en lugar de 1:

- 1ª llamada: Generar respuesta en HTML
- 2ª llamada: Generar respuesta en texto plano

### Tiempos estimados:

- **Antes:** ~5 segundos (con caché)
- **Ahora:** ~10 segundos (con caché, ambas respuestas)

### Optimización recomendada:

Si solo necesitas un formato, puedes:

1. **Crear endpoints separados:**

   - `/ask-html` - Solo respuesta HTML
   - `/ask-plain` - Solo respuesta texto plano
   - `/ask-both` - Ambas respuestas (actual)

2. **Agregar parámetro opcional:**
   ```json
   {
     "question": "...",
     "category": "...",
     "format": "both" // "html" | "plain" | "both"
   }
   ```

---

## 🔧 Código de los Cambios

### Principales modificaciones en `main.py`:

```python
# Dos prompts diferentes
prompt_plain = (
    f"Contexto:\n{context}\n\n"
    f"Pregunta: {question}\n\n"
    f"Responde de forma clara y estructurada en texto plano. "
    f"Solo proporciona el contenido, sin comentarios adicionales.\n\n"
)

prompt_html = (
    f"Contexto:\n{context}\n\n"
    f"Pregunta: {question}\n\n"
    f"Responde en formato HTML con clases de Tailwind (<p>, <strong>, <ul>). "
    f"Solo proporciona el contenido, sin comentarios adicionales.\n\n"
)

# Obtener ambas respuestas
plain_answer = llm.invoke(prompt_plain).content
html_answer = llm.invoke(prompt_html).content

# Formatear fuentes en ambos formatos
sources_html = "".join(f"<li>{source}</li>" for source in sources_info)
sources_plain = "\n".join(f"• {source}" for source in sources_info)
```

---

## 📝 Ejemplos de Uso

### Python:

```python
import requests

response = requests.post('http://localhost:8000/ask', json={
    "question": "¿Qué es el RMR?",
    "category": "geomecanica"
})

data = response.json()

# Usar respuesta HTML
print("HTML:", data['answer'])

# Usar respuesta texto plano
print("TEXTO:", data['answer_plain'])

# Usar fuentes texto plano
print("FUENTES:\n", data['sources_plain'])
```

### cURL:

```bash
curl -X POST http://localhost:8000/ask \
  -H "Content-Type: application/json" \
  -d '{"question": "¿Qué es la geomecánica?", "category": "geomecanica"}' \
  | jq '.answer_plain'
```

### JavaScript:

```javascript
const response = await fetch("http://localhost:8000/ask", {
  method: "POST",
  headers: { "Content-Type": "application/json" },
  body: JSON.stringify({
    question: "¿Qué es la fortificación?",
    category: "geomecanica",
  }),
});

const data = await response.json();

// Mostrar HTML
document.getElementById("html").innerHTML = data.answer;

// Mostrar texto plano
document.getElementById("plain").textContent = data.answer_plain;
```

---

## ⚡ Optimizaciones Futuras Sugeridas

### 1. **Generar texto plano desde HTML** (más rápido)

En lugar de 2 llamadas al LLM, hacer 1 y convertir:

```python
import html2text

# Solo 1 llamada al LLM
html_answer = llm.invoke(prompt_html).content

# Convertir HTML a texto plano
h = html2text.HTML2Text()
h.ignore_links = False
plain_answer = h.handle(html_answer)
```

**Instalación:**

```bash
pip install html2text
```

**Ventaja:** ~50% más rápido (solo 1 llamada al LLM)
**Desventaja:** El texto plano es derivado del HTML, no optimizado

---

### 2. **Parámetro de formato seleccionable**

```python
class QuestionRequest(BaseModel):
    question: str
    category: str
    format: str = "both"  # "html", "plain", or "both"

@app.post("/ask")
async def ask_question(question_request: QuestionRequest):
    # ... código de contexto ...

    result = {
        "question": question,
        "category": category
    }

    if question_request.format in ["html", "both"]:
        html_answer = llm.invoke(prompt_html).content
        result["answer"] = html_answer
        result["sources"] = f"<ul>{sources_html}</ul>"

    if question_request.format in ["plain", "both"]:
        plain_answer = llm.invoke(prompt_plain).content
        result["answer_plain"] = plain_answer
        result["sources_plain"] = sources_plain

    return result
```

**Uso:**

```bash
# Solo HTML (más rápido)
curl -X POST http://localhost:8000/ask \
  -H "Content-Type: application/json" \
  -d '{"question": "...", "category": "...", "format": "html"}'

# Solo texto plano (más rápido)
curl -X POST http://localhost:8000/ask \
  -H "Content-Type: application/json" \
  -d '{"question": "...", "category": "...", "format": "plain"}'

# Ambos (actual)
curl -X POST http://localhost:8000/ask \
  -H "Content-Type: application/json" \
  -d '{"question": "...", "category": "...", "format": "both"}'
```

---

## 📚 Archivos Creados/Modificados

### Modificados:

- ✅ `main.py` - Lógica principal actualizada
- ✅ `OPTIMIZACIONES.md` - Documentación de optimizaciones

### Nuevos:

- ✅ `API_EXAMPLES.md` - Ejemplos completos de uso
- ✅ `test_plain_text.py` - Script de prueba
- ✅ `CHANGELOG.md` - Este archivo

---

## 🚀 Estado Actual

✅ **Servidor funcionando** en http://localhost:8000  
✅ **Ambos formatos disponibles** (HTML + texto plano)  
✅ **Caché persistente activo** (84% más rápido)  
✅ **Streaming disponible** (TTFB mejorado)  
⚠️ **Rendimiento:** 2x más lento por generar ambos formatos

---

## 💡 Próximos Pasos Recomendados

1. **Decidir estrategia de formatos:**

   - [ ] Mantener ambos siempre (actual)
   - [ ] Hacer formato opcional (parámetro `format`)
   - [ ] Convertir HTML a texto (html2text)

2. **Probar rendimiento:**

   - [ ] Ejecutar `test_plain_text.py`
   - [ ] Comparar tiempos antes/después
   - [ ] Medir uso real por los clientes

3. **Documentar para usuarios:**
   - [ ] Actualizar README.md
   - [ ] Agregar ejemplos al /docs de Swagger
   - [ ] Comunicar cambios a usuarios

---

**Fecha de implementación:** 23 de octubre de 2025  
**Impacto:** Funcionalidad agregada ✅ | Rendimiento: -50% ⚠️
