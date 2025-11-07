# 💬 Sistema de Memoria Conversacional

## 🎯 Descripción

El sistema ahora soporta **conversaciones con contexto**, permitiendo que el asistente "recuerde" las interacciones previas y responda de forma coherente a preguntas de seguimiento.

## 🔧 Cómo funciona

### **Sin session_id** (Modo simple)

- Cada pregunta se procesa de forma independiente
- Se usa caché de respuestas para velocidad
- No hay memoria entre preguntas

### **Con session_id** (Modo conversacional)

- El sistema mantiene historial de la conversación
- Respuestas consideran el contexto previo
- NO se usa caché (cada conversación es única)
- Historial limitado a últimas 10 interacciones (20 mensajes)

## 📝 Ejemplos de Uso

### **Ejemplo 1: Conversación simple**

```bash
# Primera pregunta
curl -X POST "http://localhost:8000/ask" \
  -H "Content-Type: application/json" \
  -d '{
    "question": "¿Qué es CAP?",
    "category": "compliance",
    "format": "plain",
    "session_id": "user-123-session"
  }'

# Respuesta:
# "CAP S.A. es una compañía minera chilena..."

# Segunda pregunta (con contexto)
curl -X POST "http://localhost:8000/ask" \
  -H "Content-Type: application/json" \
  -d '{
    "question": "¿Cuál es su modelo de gobierno corporativo?",
    "category": "compliance",
    "format": "plain",
    "session_id": "user-123-session"
  }'

# Respuesta:
# "El modelo de gobierno corporativo de CAP incluye..."
# (Sabe que "su" se refiere a CAP por el contexto previo)
```

### **Ejemplo 2: React/JavaScript**

```javascript
// Generar session_id único por usuario
const sessionId = `user-${userId}-${Date.now()}`;

// Primera pregunta
const response1 = await fetch("http://localhost:8000/ask", {
  method: "POST",
  headers: { "Content-Type": "application/json" },
  body: JSON.stringify({
    question: "¿Qué es la geomecánica?",
    category: "geomecanica",
    format: "html",
    session_id: sessionId,
  }),
});

// Segunda pregunta en la misma conversación
const response2 = await fetch("http://localhost:8000/ask", {
  method: "POST",
  headers: { "Content-Type": "application/json" },
  body: JSON.stringify({
    question: "Dame ejemplos de aplicaciones",
    category: "geomecanica",
    format: "html",
    session_id: sessionId, // ⭐ Mismo session_id
  }),
});
// El sistema entiende que "aplicaciones" se refiere a geomecánica
```

### **Ejemplo 3: Gestión de sesiones**

```bash
# Ver historial de una conversación
curl -X GET "http://localhost:8000/conversations/user-123-session"

# Respuesta:
# {
#   "session_id": "user-123-session",
#   "message_count": 6,
#   "history": [
#     {"role": "user", "content": "¿Qué es CAP?"},
#     {"role": "assistant", "content": "CAP S.A. es..."},
#     ...
#   ]
# }

# Limpiar una conversación específica
curl -X DELETE "http://localhost:8000/conversations/user-123-session"

# Limpiar todas las conversaciones
curl -X DELETE "http://localhost:8000/conversations"
```

## 🎛️ Endpoints Nuevos

| Método | Endpoint                      | Descripción                        |
| ------ | ----------------------------- | ---------------------------------- |
| GET    | `/conversations/{session_id}` | Obtiene el historial de una sesión |
| DELETE | `/conversations/{session_id}` | Elimina una sesión específica      |
| DELETE | `/conversations`              | Elimina todas las sesiones         |

## 📊 Estructura del Historial

El historial mantiene:

- **Últimas 10 interacciones** (20 mensajes: 10 usuario + 10 asistente)
- **Formato**: `[{role: "user"|"assistant", content: "..."}]`
- **Se incluye en el prompt**: Últimas 3 interacciones (6 mensajes)

## 🔒 Consideraciones

### **session_id**

- Debe ser único por usuario/conversación
- Recomendado: `user-{userId}-{timestamp}` o UUID
- Persistencia: Solo en memoria (se pierde al reiniciar servidor)

### **Caché**

- **Con session_id**: NO se usa caché
- **Sin session_id**: SÍ se usa caché
- Esto asegura que conversaciones sean dinámicas

### **Performance**

- Conversaciones son ligeramente más lentas (no usan caché)
- Cada mensaje adicional suma ~50-100 tokens al prompt
- Límite de 20 mensajes previene sobrecarga

## 🚀 Mejores Prácticas

### **1. Generar session_id único**

```javascript
// Opción 1: Timestamp + userId
const sessionId = `user-${userId}-${Date.now()}`;

// Opción 2: UUID
import { v4 as uuidv4 } from "uuid";
const sessionId = `session-${uuidv4()}`;
```

### **2. Limpiar sesiones inactivas**

```javascript
// En tu app React, cuando el usuario cierra el chat
const closeChat = async () => {
  await fetch(`/conversations/${sessionId}`, { method: "DELETE" });
};
```

### **3. Usar session_id solo cuando necesites contexto**

```javascript
// Pregunta simple (usa caché)
const simpleQuery = {
  question: "¿Qué es la geomecánica?",
  category: "geomecanica",
  format: "html",
  // NO session_id
};

// Conversación (con contexto)
const conversationalQuery = {
  question: "Dame más ejemplos",
  category: "geomecanica",
  format: "html",
  session_id: currentSessionId, // ✅ Con session_id
};
```

## 🎨 Ejemplo de UI React

```jsx
import { useState } from "react";

function ChatComponent() {
  const [sessionId] = useState(`session-${Date.now()}`);
  const [messages, setMessages] = useState([]);

  const sendMessage = async (question) => {
    // Agregar mensaje del usuario
    setMessages((prev) => [...prev, { role: "user", content: question }]);

    // Enviar a API con session_id
    const response = await fetch("http://localhost:8000/ask", {
      method: "POST",
      headers: { "Content-Type": "application/json" },
      body: JSON.stringify({
        question,
        category: "compliance",
        format: "html",
        session_id: sessionId, // Mantiene contexto
      }),
    });

    const data = await response.json();

    // Agregar respuesta del asistente
    setMessages((prev) => [
      ...prev,
      {
        role: "assistant",
        content: data.answer,
      },
    ]);
  };

  return (
    <div className="chat">
      {messages.map((msg, i) => (
        <div key={i} className={msg.role}>
          {msg.content}
        </div>
      ))}
    </div>
  );
}
```

## ✅ Verificar Funcionamiento

```bash
# 1. Hacer primera pregunta
curl -X POST "http://localhost:8000/ask" \
  -H "Content-Type: application/json" \
  -d '{"question": "¿Qué es CAP?", "category": "compliance", "format": "plain", "session_id": "test-123"}'

# 2. Hacer pregunta de seguimiento
curl -X POST "http://localhost:8000/ask" \
  -H "Content-Type: application/json" \
  -d '{"question": "¿Cuáles son sus comités?", "category": "compliance", "format": "plain", "session_id": "test-123"}'

# 3. Ver historial
curl -X GET "http://localhost:8000/conversations/test-123"

# 4. Limpiar
curl -X DELETE "http://localhost:8000/conversations/test-123"
```

## 🎯 Beneficios

✅ **Conversaciones naturales**: El usuario puede hacer preguntas de seguimiento  
✅ **Referencias contextuales**: "Dame más detalles", "¿Y qué más?"  
✅ **Mejor UX**: Interfaz de chat más fluida  
✅ **Flexible**: Se puede usar con o sin contexto según necesidad  
✅ **Escalable**: Historial limitado previene sobrecarga

---

**¿Necesitas ayuda para integrar esto en tu app React?** 🚀
