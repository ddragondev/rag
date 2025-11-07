# 💬 API de Conversaciones - Documentación

## 🎯 Descripción

El sistema RAG ahora incluye **memoria conversacional** que permite mantener el contexto de las conversaciones. Cada conversación se identifica con un `session_id` único.

---

## 📋 Endpoints Disponibles

### 1. **GET /conversations**

Lista todas las conversaciones activas con resumen.

**Respuesta:**

```json
{
  "total_conversations": 2,
  "conversations": [
    {
      "session_id": "usuario123",
      "message_count": 8,
      "interaction_count": 4,
      "first_question": "¿Qué es CAP?",
      "last_question": "¿Cuál es su directorio?",
      "last_answer": "El Directorio de CAP S.A. está compuesto por...",
      "preview": "¿Qué es CAP?..."
    },
    {
      "session_id": "session_456",
      "message_count": 4,
      "interaction_count": 2,
      "first_question": "¿Qué es la geomecánica?",
      "last_question": "¿Cuáles son sus aplicaciones?",
      "last_answer": "Las aplicaciones principales son...",
      "preview": "¿Qué es la geomecánica?..."
    }
  ]
}
```

**Ejemplo cURL:**

```bash
curl -X GET "http://localhost:8000/conversations"
```

**Ejemplo JavaScript:**

```javascript
const response = await fetch("http://localhost:8000/conversations");
const data = await response.json();
console.log(`Total conversaciones: ${data.total_conversations}`);
```

---

### 2. **GET /conversations/{session_id}**

Obtiene el historial completo de una conversación específica.

**Parámetros:**

- `session_id` (string): ID único de la sesión

**Respuesta:**

```json
{
  "session_id": "usuario123",
  "message_count": 8,
  "first_message": "¿Qué es CAP?",
  "last_message": "El Directorio de CAP S.A. está compuesto por...",
  "history": [
    {
      "role": "user",
      "content": "¿Qué es CAP?"
    },
    {
      "role": "assistant",
      "content": "CAP S.A. es una compañía minera y siderúrgica..."
    },
    {
      "role": "user",
      "content": "¿Cuál es su directorio?"
    },
    {
      "role": "assistant",
      "content": "El Directorio de CAP S.A. está compuesto por..."
    }
  ]
}
```

**Ejemplo cURL:**

```bash
curl -X GET "http://localhost:8000/conversations/usuario123"
```

**Ejemplo JavaScript:**

```javascript
const sessionId = "usuario123";
const response = await fetch(
  `http://localhost:8000/conversations/${sessionId}`
);
const data = await response.json();
console.log(`Mensajes: ${data.message_count}`);
console.log("Historial:", data.history);
```

---

### 3. **POST /ask** (con session_id)

Hacer una pregunta manteniendo el contexto conversacional.

**Body:**

```json
{
  "question": "¿Cuál es su directorio?",
  "category": "compliance",
  "format": "plain",
  "session_id": "usuario123"
}
```

**Características:**

- ✅ Mantiene contexto de las últimas 3 interacciones
- ✅ No usa caché (respuestas frescas siempre)
- ✅ Entiende referencias ("su", "ellos", "eso", etc.)

**Ejemplo cURL:**

```bash
# Primera pregunta
curl -X POST "http://localhost:8000/ask" \
  -H "Content-Type: application/json" \
  -d '{
    "question": "¿Qué es CAP?",
    "category": "compliance",
    "format": "plain",
    "session_id": "usuario123"
  }'

# Segunda pregunta (con contexto)
curl -X POST "http://localhost:8000/ask" \
  -H "Content-Type: application/json" \
  -d '{
    "question": "¿Cuál es su modelo de prevención de delitos?",
    "category": "compliance",
    "format": "plain",
    "session_id": "usuario123"
  }'
```

**Ejemplo JavaScript:**

```javascript
const sessionId = "usuario123";

// Primera pregunta
const response1 = await fetch("http://localhost:8000/ask", {
  method: "POST",
  headers: { "Content-Type": "application/json" },
  body: JSON.stringify({
    question: "¿Qué es CAP?",
    category: "compliance",
    format: "plain",
    session_id: sessionId,
  }),
});

// Segunda pregunta (entiende "su" = CAP)
const response2 = await fetch("http://localhost:8000/ask", {
  method: "POST",
  headers: { "Content-Type": "application/json" },
  body: JSON.stringify({
    question: "¿Cuál es su directorio?",
    category: "compliance",
    format: "plain",
    session_id: sessionId,
  }),
});
```

---

### 4. **DELETE /conversations/{session_id}**

Elimina el historial de una conversación específica.

**Parámetros:**

- `session_id` (string): ID único de la sesión a eliminar

**Respuesta:**

```json
{
  "message": "Conversación 'usuario123' eliminada exitosamente"
}
```

**Ejemplo cURL:**

```bash
curl -X DELETE "http://localhost:8000/conversations/usuario123"
```

**Ejemplo JavaScript:**

```javascript
const sessionId = "usuario123";
await fetch(`http://localhost:8000/conversations/${sessionId}`, {
  method: "DELETE",
});
```

---

### 5. **DELETE /conversations**

Elimina TODAS las conversaciones del sistema.

**Respuesta:**

```json
{
  "message": "Se eliminaron 15 conversaciones"
}
```

**Ejemplo cURL:**

```bash
curl -X DELETE "http://localhost:8000/conversations"
```

**Ejemplo JavaScript:**

```javascript
await fetch("http://localhost:8000/conversations", {
  method: "DELETE",
});
```

---

## 🔧 Integración con React

### Hook Personalizado para Conversaciones

```javascript
import { useState, useEffect } from "react";

const useConversation = (category) => {
  const [sessionId] = useState(
    () => `session_${Date.now()}_${Math.random().toString(36).substr(2, 9)}`
  );
  const [messages, setMessages] = useState([]);
  const [loading, setLoading] = useState(false);

  // Cargar conversación existente
  const loadConversation = async (existingSessionId) => {
    const response = await fetch(
      `http://localhost:8000/conversations/${existingSessionId}`
    );
    const data = await response.json();
    setMessages(data.history || []);
  };

  // Enviar pregunta
  const askQuestion = async (question, format = "plain") => {
    setLoading(true);

    // Agregar pregunta del usuario a la UI inmediatamente
    const userMessage = { role: "user", content: question };
    setMessages((prev) => [...prev, userMessage]);

    try {
      const response = await fetch("http://localhost:8000/ask", {
        method: "POST",
        headers: { "Content-Type": "application/json" },
        body: JSON.stringify({
          question,
          category,
          format,
          session_id: sessionId,
        }),
      });

      const data = await response.json();

      // Agregar respuesta del asistente
      const assistantMessage = {
        role: "assistant",
        content: data.answer_plain || data.answer,
      };
      setMessages((prev) => [...prev, assistantMessage]);

      return data;
    } finally {
      setLoading(false);
    }
  };

  // Limpiar conversación
  const clearConversation = async () => {
    await fetch(`http://localhost:8000/conversations/${sessionId}`, {
      method: "DELETE",
    });
    setMessages([]);
  };

  return {
    sessionId,
    messages,
    loading,
    askQuestion,
    clearConversation,
    loadConversation,
  };
};

export default useConversation;
```

### Componente de Chat

```javascript
import React, { useState } from "react";
import useConversation from "./hooks/useConversation";

const ChatComponent = ({ category }) => {
  const [input, setInput] = useState("");
  const { messages, loading, askQuestion, clearConversation, sessionId } =
    useConversation(category);

  const handleSubmit = async (e) => {
    e.preventDefault();
    if (!input.trim()) return;

    await askQuestion(input);
    setInput("");
  };

  return (
    <div className="chat-container">
      <div className="chat-header">
        <h3>Chat - {category}</h3>
        <small>Sesión: {sessionId}</small>
        <button onClick={clearConversation}>Limpiar</button>
      </div>

      <div className="messages">
        {messages.map((msg, idx) => (
          <div key={idx} className={`message ${msg.role}`}>
            <strong>{msg.role === "user" ? "Tú" : "Asistente"}:</strong>
            <p>{msg.content}</p>
          </div>
        ))}
        {loading && <div className="loading">Escribiendo...</div>}
      </div>

      <form onSubmit={handleSubmit}>
        <input
          type="text"
          value={input}
          onChange={(e) => setInput(e.target.value)}
          placeholder="Escribe tu pregunta..."
          disabled={loading}
        />
        <button type="submit" disabled={loading}>
          Enviar
        </button>
      </form>
    </div>
  );
};

export default ChatComponent;
```

### Componente de Lista de Conversaciones

```javascript
import React, { useState, useEffect } from "react";

const ConversationsList = ({ onSelectConversation }) => {
  const [conversations, setConversations] = useState([]);

  useEffect(() => {
    loadConversations();
  }, []);

  const loadConversations = async () => {
    const response = await fetch("http://localhost:8000/conversations");
    const data = await response.json();
    setConversations(data.conversations);
  };

  const deleteConversation = async (sessionId) => {
    await fetch(`http://localhost:8000/conversations/${sessionId}`, {
      method: "DELETE",
    });
    loadConversations(); // Recargar lista
  };

  return (
    <div className="conversations-list">
      <h3>Conversaciones Activas ({conversations.length})</h3>
      {conversations.map((conv) => (
        <div
          key={conv.session_id}
          className="conversation-item"
          onClick={() => onSelectConversation(conv.session_id)}
        >
          <div className="conv-preview">{conv.preview}</div>
          <div className="conv-info">
            {conv.interaction_count} interacciones
          </div>
          <button
            onClick={(e) => {
              e.stopPropagation();
              deleteConversation(conv.session_id);
            }}
          >
            Eliminar
          </button>
        </div>
      ))}
    </div>
  );
};

export default ConversationsList;
```

---

## 🎯 Características del Sistema

### ✅ Memoria Persistente

- Las conversaciones se mantienen **mientras el servidor esté corriendo**
- Puedes cerrar la pestaña y volver a la conversación usando el mismo `session_id`
- No se pierde el contexto al refrescar la página si guardas el `session_id`

### ✅ Límites Automáticos

- Cada sesión mantiene hasta **20 mensajes** (10 interacciones)
- En el contexto del prompt se incluyen las **últimas 3 interacciones** (6 mensajes)
- Esto evita saturar el token limit de OpenAI

### ✅ Sin Caché en Conversaciones

- Las preguntas con `session_id` NO se cachean
- Esto asegura que siempre se procesen con el contexto correcto
- Las preguntas sin `session_id` SÍ usan caché para velocidad

### ✅ Resumen Inteligente

- El endpoint `/conversations` muestra un preview de cada conversación
- Fácil identificar conversaciones por su primera pregunta
- Estadísticas útiles (mensaje count, interaction count)

---

## 🚀 Casos de Uso

### 1. Chat Interactivo

Usuario hace múltiples preguntas relacionadas manteniendo contexto.

### 2. Soporte Multi-Usuario

Cada usuario tiene su propio `session_id` (ej: `user_${userId}`)

### 3. Recuperación de Conversación

Usuario puede volver a una conversación anterior usando su `session_id`

### 4. Análisis de Interacciones

Revisar el historial completo para entender qué información buscan los usuarios

---

## 📌 Notas Importantes

⚠️ **Persistencia**: Las conversaciones se almacenan en memoria. Si reinicias el servidor, se pierden. Para persistencia permanente, considera agregar almacenamiento en base de datos.

✅ **IDs Únicos**: Genera `session_id` únicos usando timestamps + random para evitar colisiones.

✅ **Limpieza**: Considera implementar un sistema de limpieza automática de conversaciones antiguas.

---

## 🎉 ¡Sistema Listo!

El sistema de conversaciones está completamente funcional. Puedes empezar a usarlo inmediatamente en tu aplicación React.
