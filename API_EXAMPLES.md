# 📚 Ejemplos de Uso de la API

## 🎯 Endpoint: `/ask` (Respuesta Completa)

### Características:

- ✅ Respuesta completa en HTML
- ✅ Respuesta completa en texto plano
- ✅ Fuentes en ambos formatos
- ✅ Más rápido con caché

### Ejemplo con cURL:

```bash
curl -X POST http://localhost:8000/ask \
  -H "Content-Type: application/json" \
  -d '{
    "question": "¿Qué es la mecánica de rocas?",
    "category": "geomecanica"
  }'
```

### Respuesta Esperada:

```json
{
  "question": "¿Qué es la mecánica de rocas?",
  "category": "geomecanica",
  "answer": "<p class=\"text-lg\">La mecánica de rocas es...</p>",
  "answer_plain": "La mecánica de rocas es una disciplina...",
  "sources": "<ul><li>docs/geomecanica/CI4402_Clase1Rev0.pdf (pág. 5)</li></ul>",
  "sources_plain": "• docs/geomecanica/CI4402_Clase1Rev0.pdf (pág. 5)"
}
```

### Ejemplo con Python:

```python
import requests

url = "http://localhost:8000/ask"
payload = {
    "question": "¿Qué es la fortificación en minería?",
    "category": "geomecanica"
}

response = requests.post(url, json=payload)
data = response.json()

print("=== RESPUESTA HTML ===")
print(data["answer"])

print("\n=== RESPUESTA TEXTO PLANO ===")
print(data["answer_plain"])

print("\n=== FUENTES ===")
print(data["sources_plain"])
```

### Ejemplo con JavaScript (fetch):

```javascript
const askQuestion = async () => {
  const response = await fetch("http://localhost:8000/ask", {
    method: "POST",
    headers: {
      "Content-Type": "application/json",
    },
    body: JSON.stringify({
      question: "¿Cuáles son los tipos de fortificación?",
      category: "geomecanica",
    }),
  });

  const data = await response.json();

  // Mostrar respuesta HTML en el DOM
  document.getElementById("html-answer").innerHTML = data.answer;

  // Mostrar respuesta texto plano
  document.getElementById("plain-answer").textContent = data.answer_plain;

  // Mostrar fuentes
  document.getElementById("sources").innerHTML = data.sources;
};
```

---

## 🌊 Endpoint: `/ask-stream` (Streaming)

### Características:

- ✅ Streaming progresivo de HTML
- ✅ Streaming progresivo de texto plano
- ✅ Respuesta más rápida (TTFB mejorado)
- ✅ Mejor experiencia de usuario

### Ejemplo con cURL:

```bash
curl -N -X POST http://localhost:8000/ask-stream \
  -H "Content-Type: application/json" \
  -d '{
    "question": "¿Qué es la acuñadura?",
    "category": "geomecanica"
  }'
```

### Formato de Respuesta (Server-Sent Events):

```
data: {"question": "...", "category": "...", "sources": "...", "sources_plain": "...", "type": "metadata"}

data: {"type": "html_start"}

data: {"type": "html_content", "content": "<p"}

data: {"type": "html_content", "content": " class="}

data: {"type": "html_end"}

data: {"type": "plain_start"}

data: {"type": "plain_content", "content": "La acuñadura"}

data: {"type": "plain_content", "content": " es un proceso..."}

data: {"type": "done"}
```

### Ejemplo con Python (usando SSE):

```python
import requests
import json

url = "http://localhost:8000/ask-stream"
payload = {
    "question": "¿Qué es el RMR?",
    "category": "geomecanica"
}

html_answer = ""
plain_answer = ""

with requests.post(url, json=payload, stream=True) as response:
    for line in response.iter_lines():
        if line:
            line = line.decode('utf-8')
            if line.startswith('data: '):
                data = json.loads(line[6:])

                if data['type'] == 'metadata':
                    print(f"Pregunta: {data['question']}")
                    print(f"Fuentes:\n{data['sources_plain']}\n")

                elif data['type'] == 'html_content':
                    html_answer += data['content']
                    # Puedes ir mostrando el HTML progresivamente

                elif data['type'] == 'plain_content':
                    plain_answer += data['content']
                    print(data['content'], end='', flush=True)

                elif data['type'] == 'done':
                    print("\n\n✅ Respuesta completa")

print("\n=== RESPUESTA HTML COMPLETA ===")
print(html_answer)

print("\n=== RESPUESTA TEXTO PLANO COMPLETA ===")
print(plain_answer)
```

### Ejemplo con JavaScript (EventSource):

```javascript
const askQuestionStream = (question, category) => {
  const eventSource = new EventSource(
    `http://localhost:8000/ask-stream?` +
      new URLSearchParams({
        question: question,
        category: category,
      })
  );

  let htmlAnswer = "";
  let plainAnswer = "";
  let currentMode = null;

  eventSource.onmessage = (event) => {
    const data = JSON.parse(event.data);

    switch (data.type) {
      case "metadata":
        console.log("Fuentes:", data.sources_plain);
        document.getElementById("sources").innerHTML = data.sources;
        break;

      case "html_start":
        currentMode = "html";
        htmlAnswer = "";
        break;

      case "html_content":
        htmlAnswer += data.content;
        document.getElementById("html-answer").innerHTML = htmlAnswer;
        break;

      case "html_end":
        currentMode = null;
        break;

      case "plain_start":
        currentMode = "plain";
        plainAnswer = "";
        break;

      case "plain_content":
        plainAnswer += data.content;
        document.getElementById("plain-answer").textContent = plainAnswer;
        break;

      case "done":
        eventSource.close();
        console.log("✅ Respuesta completa");
        break;

      case "error":
        console.error("Error:", data.error);
        eventSource.close();
        break;
    }
  };
};

// Uso
askQuestionStream("¿Qué es la geomecánica?", "geomecanica");
```

---

## 📋 Otros Endpoints

### GET `/categories`

Lista todas las categorías de documentos disponibles.

```bash
curl http://localhost:8000/categories
```

**Respuesta:**

```json
{
  "categories": ["geomecanica"]
}
```

### GET `/`

Información general de la API.

```bash
curl http://localhost:8000/
```

**Respuesta:**

```json
{
  "message": "PDF RAG API con LangChain",
  "endpoints": {
    "/ask": "POST - Consulta normal (respuesta completa)",
    "/ask-stream": "POST - Consulta con streaming (respuesta progresiva)",
    "/docs": "Documentación interactiva Swagger",
    "/categories": "GET - Lista de categorías disponibles"
  }
}
```

---

## 🎨 Ejemplo de Integración Frontend (React)

```jsx
import React, { useState } from "react";

function AskQuestion() {
  const [question, setQuestion] = useState("");
  const [htmlAnswer, setHtmlAnswer] = useState("");
  const [plainAnswer, setPlainAnswer] = useState("");
  const [sources, setSources] = useState("");
  const [loading, setLoading] = useState(false);

  const handleAsk = async () => {
    setLoading(true);

    const response = await fetch("http://localhost:8000/ask", {
      method: "POST",
      headers: { "Content-Type": "application/json" },
      body: JSON.stringify({
        question: question,
        category: "geomecanica",
      }),
    });

    const data = await response.json();
    setHtmlAnswer(data.answer);
    setPlainAnswer(data.answer_plain);
    setSources(data.sources_plain);
    setLoading(false);
  };

  return (
    <div className="container mx-auto p-4">
      <h1 className="text-2xl font-bold mb-4">
        PDF RAG - Consulta de Documentos
      </h1>

      <textarea
        className="w-full border p-2 rounded mb-2"
        rows="3"
        placeholder="Escribe tu pregunta..."
        value={question}
        onChange={(e) => setQuestion(e.target.value)}
      />

      <button
        className="bg-blue-500 text-white px-4 py-2 rounded"
        onClick={handleAsk}
        disabled={loading}
      >
        {loading ? "Consultando..." : "Preguntar"}
      </button>

      {htmlAnswer && (
        <div className="mt-6">
          <h2 className="text-xl font-semibold mb-2">Respuesta HTML:</h2>
          <div
            className="border p-4 rounded bg-gray-50"
            dangerouslySetInnerHTML={{ __html: htmlAnswer }}
          />
        </div>
      )}

      {plainAnswer && (
        <div className="mt-6">
          <h2 className="text-xl font-semibold mb-2">Respuesta Texto Plano:</h2>
          <pre className="border p-4 rounded bg-gray-50 whitespace-pre-wrap">
            {plainAnswer}
          </pre>
        </div>
      )}

      {sources && (
        <div className="mt-6">
          <h2 className="text-xl font-semibold mb-2">Fuentes:</h2>
          <pre className="border p-4 rounded bg-gray-100 text-sm">
            {sources}
          </pre>
        </div>
      )}
    </div>
  );
}

export default AskQuestion;
```

---

## 🧪 Testing

### Test Básico con Python:

```python
import requests
import time

def test_ask_endpoint():
    """Test del endpoint /ask con medición de tiempo."""

    url = "http://localhost:8000/ask"
    payload = {
        "question": "¿Qué es el RMR en mecánica de rocas?",
        "category": "geomecanica"
    }

    start_time = time.time()
    response = requests.post(url, json=payload)
    elapsed_time = time.time() - start_time

    assert response.status_code == 200
    data = response.json()

    # Verificar que ambos formatos existen
    assert "answer" in data
    assert "answer_plain" in data
    assert "sources" in data
    assert "sources_plain" in data

    # Verificar que no están vacías
    assert len(data["answer"]) > 0
    assert len(data["answer_plain"]) > 0

    print(f"✅ Test pasado en {elapsed_time:.2f}s")
    print(f"HTML length: {len(data['answer'])} chars")
    print(f"Plain length: {len(data['answer_plain'])} chars")

    return data

if __name__ == "__main__":
    test_ask_endpoint()
```

---

## 📊 Comparación de Formatos

| Característica    | HTML (`answer`)      | Texto Plano (`answer_plain`) |
| ----------------- | -------------------- | ---------------------------- |
| **Formato**       | HTML con Tailwind    | Texto sin formato            |
| **Uso**           | Frontend web         | CLI, logs, emails            |
| **Tamaño**        | Mayor (con tags)     | Menor (sin tags)             |
| **Lectura**       | Visual, estilizada   | Directa, simple              |
| **Procesamiento** | Requiere renderizado | Directo                      |

---

## 🚀 Mejores Prácticas

1. **Usa `/ask` cuando:**

   - Necesites la respuesta completa de una vez
   - Estés trabajando con aplicaciones síncronas
   - Quieras ambos formatos (HTML y texto plano)

2. **Usa `/ask-stream` cuando:**

   - Quieras mostrar respuestas progresivamente
   - La experiencia de usuario sea crítica
   - Trabajes con preguntas complejas que toman tiempo

3. **Manejo de Errores:**
   ```python
   try:
       response = requests.post(url, json=payload, timeout=60)
       response.raise_for_status()
       data = response.json()
   except requests.exceptions.Timeout:
       print("⏰ La consulta tardó demasiado")
   except requests.exceptions.HTTPError as e:
       print(f"❌ Error HTTP: {e}")
   except Exception as e:
       print(f"❌ Error: {e}")
   ```

---

**Última actualización:** 23 de octubre de 2025
