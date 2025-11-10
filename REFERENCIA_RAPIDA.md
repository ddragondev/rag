# ⚡ Referencia Rápida - API Endpoints

## 🎯 Endpoints Esenciales

### 1️⃣ Hacer Pregunta (Con/Sin Auth)

```bash
POST /ask
```

**Sin autenticación:**

```javascript
fetch("http://localhost:8000/ask", {
  method: "POST",
  headers: { "Content-Type": "application/json" },
  body: JSON.stringify({
    question: "¿Qué es la geomecánica?",
    category: "geomecanica",
    format: "both",
  }),
});
```

**Con autenticación (Clerk):**

```javascript
const token = await getToken(); // Clerk hook

fetch("http://localhost:8000/ask", {
  method: "POST",
  headers: {
    "Content-Type": "application/json",
    Authorization: `Bearer ${token}`,
  },
  body: JSON.stringify({
    question: "¿Qué es la geomecánica?",
    category: "geomecanica",
    format: "both",
  }),
});
```

**Response:**

```json
{
  "question": "¿Qué es la geomecánica?",
  "answer": "<p>HTML response</p>",
  "answer_plain": "Plain text response",
  "sources": "<ul><li>Source 1</li></ul>",
  "sources_plain": "• Source 1",
  "authenticated": true, // Solo si está autenticado
  "user_email": "user@example.com", // Solo si está autenticado
  "session_id": "user_2abc123" // Solo si está autenticado
}
```

---

### 2️⃣ Ver Historial Personal

```bash
GET /my-history?limit=100
```

**Request:**

```javascript
const token = await getToken();

fetch("http://localhost:8000/my-history?limit=50", {
  headers: {
    Authorization: `Bearer ${token}`,
  },
});
```

**Response:**

```json
{
  "user_id": "user_2abc123",
  "user_email": "user@example.com",
  "history": [
    {
      "role": "user",
      "content": "¿Qué es la geomecánica?",
      "timestamp": "2025-11-10T12:00:00Z",
      "metadata": {
        /* ... */
      }
    },
    {
      "role": "assistant",
      "content": "La geomecánica es...",
      "timestamp": "2025-11-10T12:00:05Z",
      "metadata": {
        /* ... */
      }
    }
  ],
  "total_messages": 2
}
```

---

### 3️⃣ Limpiar Historial

```bash
DELETE /my-history
```

**Request:**

```javascript
const token = await getToken();

fetch("http://localhost:8000/my-history", {
  method: "DELETE",
  headers: {
    Authorization: `Bearer ${token}`,
  },
});
```

**Response:**

```json
{
  "message": "Historial eliminado correctamente",
  "user_email": "user@example.com"
}
```

---

### 4️⃣ Listar Categorías

```bash
GET /categories
```

**Request:**

```javascript
fetch("http://localhost:8000/categories");
```

**Response:**

```json
{
  "categories": [
    {
      "name": "geomecanica",
      "display_name": "Geomecánica",
      "description": "Documentos sobre mecánica de rocas",
      "document_count": 15
    },
    {
      "name": "compliance",
      "display_name": "Compliance",
      "description": "Normativas y regulaciones",
      "document_count": 8
    }
  ],
  "total": 2
}
```

---

### 5️⃣ Health Check

```bash
GET /health
```

**Request:**

```javascript
fetch("http://localhost:8000/health");
```

**Response:**

```json
{
  "status": "healthy",
  "message": "Sistema funcionando correctamente"
}
```

---

## 🔐 Autenticación

### Obtener Token (React + Clerk)

```tsx
import { useAuth } from "@clerk/clerk-react";

function MyComponent() {
  const { getToken, isSignedIn } = useAuth();

  const callAPI = async () => {
    if (isSignedIn) {
      const token = await getToken();
      // Usar token en headers
    }
  };
}
```

### Formato del Header

```
Authorization: Bearer eyJhbGciOiJSUzI1NiIsInR5cCI6IkpXVCJ9...
```

---

## 📝 Formatos de Respuesta

### `format: "html"`

```json
{
  "answer": "<p>Respuesta en HTML con <strong>formato</strong></p>",
  "sources": "<ul><li>Fuente 1</li><li>Fuente 2</li></ul>"
}
```

### `format: "plain"`

```json
{
  "answer_plain": "Respuesta en texto plano sin formato",
  "sources_plain": "• Fuente 1\n• Fuente 2"
}
```

### `format: "both"`

```json
{
  "answer": "<p>HTML...</p>",
  "answer_plain": "Plain...",
  "sources": "<ul>...</ul>",
  "sources_plain": "• ..."
}
```

---

## ⚠️ Códigos HTTP

| Código | Significado  | Ejemplo                 |
| ------ | ------------ | ----------------------- |
| 200    | OK           | Respuesta exitosa       |
| 400    | Bad Request  | Formato inválido        |
| 401    | Unauthorized | Token inválido/faltante |
| 404    | Not Found    | Categoría no existe     |
| 500    | Server Error | Error interno           |

---

## 🎨 Hook React Completo

```typescript
import { useState } from "react";
import { useAuth } from "@clerk/clerk-react";

const API_BASE = "http://localhost:8000";

export function useRAG() {
  const { getToken, isSignedIn } = useAuth();
  const [loading, setLoading] = useState(false);

  const ask = async (question: string, category: string) => {
    setLoading(true);
    try {
      const headers: any = {
        "Content-Type": "application/json",
      };

      if (isSignedIn) {
        const token = await getToken();
        headers["Authorization"] = `Bearer ${token}`;
      }

      const response = await fetch(`${API_BASE}/ask`, {
        method: "POST",
        headers,
        body: JSON.stringify({
          question,
          category,
          format: "both",
        }),
      });

      return await response.json();
    } finally {
      setLoading(false);
    }
  };

  const getHistory = async () => {
    if (!isSignedIn) return [];

    const token = await getToken();
    const response = await fetch(`${API_BASE}/my-history`, {
      headers: { Authorization: `Bearer ${token}` },
    });

    const data = await response.json();
    return data.history;
  };

  return { ask, getHistory, loading, isSignedIn };
}
```

---

## 📊 Tabla de Endpoints

| Método | Endpoint            | Auth     | Descripción            |
| ------ | ------------------- | -------- | ---------------------- |
| GET    | `/health`           | No       | Estado del sistema     |
| GET    | `/categories`       | No       | Listar categorías      |
| POST   | `/ask`              | Opcional | Hacer pregunta         |
| POST   | `/ask-video`        | Opcional | Pregunta sobre video   |
| GET    | `/my-history`       | Sí       | Ver historial personal |
| DELETE | `/my-history`       | Sí       | Limpiar historial      |
| GET    | `/my-conversations` | Sí       | Listar conversaciones  |
| GET    | `/mongodb/health`   | No       | Estado MongoDB         |
| GET    | `/cache/stats`      | No       | Estadísticas caché     |
| DELETE | `/cache/clear`      | No       | Limpiar caché          |

---

## 🚀 Ejemplo Completo (React)

```tsx
import { useState, useEffect } from "react";
import { SignInButton, SignedIn, SignedOut, useAuth } from "@clerk/clerk-react";
import { useRAG } from "./hooks/useRAG";

function ChatApp() {
  const { ask, getHistory, loading, isSignedIn } = useRAG();
  const [question, setQuestion] = useState("");
  const [answer, setAnswer] = useState(null);
  const [history, setHistory] = useState([]);

  useEffect(() => {
    if (isSignedIn) {
      loadHistory();
    }
  }, [isSignedIn]);

  const loadHistory = async () => {
    const hist = await getHistory();
    setHistory(hist);
  };

  const handleSubmit = async (e) => {
    e.preventDefault();
    const result = await ask(question, "geomecanica");
    setAnswer(result);
    setQuestion("");

    if (isSignedIn) {
      await loadHistory(); // Recargar historial
    }
  };

  return (
    <div>
      <header>
        <h1>RAG Chat</h1>
        <SignedOut>
          <SignInButton />
        </SignedOut>
        <SignedIn>
          <p>Historial guardado automáticamente</p>
        </SignedIn>
      </header>

      <form onSubmit={handleSubmit}>
        <input
          value={question}
          onChange={(e) => setQuestion(e.target.value)}
          placeholder="Tu pregunta..."
        />
        <button disabled={loading}>
          {loading ? "Procesando..." : "Enviar"}
        </button>
      </form>

      {answer && <div dangerouslySetInnerHTML={{ __html: answer.answer }} />}

      <SignedIn>
        <aside>
          <h3>Tu Historial</h3>
          {history.map((msg, i) => (
            <div key={i}>
              {msg.role}: {msg.content.substring(0, 50)}...
            </div>
          ))}
        </aside>
      </SignedIn>
    </div>
  );
}
```

---

## 🔗 Variables de Entorno

```env
# Frontend (.env)
VITE_CLERK_PUBLISHABLE_KEY=pk_test_xxxxxxxxxxxxx
VITE_API_BASE=http://localhost:8000

# Backend (.env)
OPENAI_API_KEY=sk-xxxxxxxxxxxxx
MONGO_URI=mongodb+srv://...
CLERK_PUBLISHABLE_KEY=pk_test_xxxxxxxxxxxxx
CLERK_SECRET_KEY=sk_test_xxxxxxxxxxxxx
```

---

## 📚 Documentación Completa

- **`API_ENDPOINTS.md`** - Documentación detallada de todos los endpoints
- **`EJEMPLOS_INTEGRACION.md`** - Ejemplos por framework (React, Vue, Next.js, etc.)
- **`FRONTEND_HISTORIAL_USUARIO.md`** - Componentes completos de chat
- **`GUIA_INTEGRACION_CLERK.md`** - Guía de autenticación

---

## 💡 Tips

1. **Caché**: Usuarios anónimos usan caché (rápido)
2. **Historial**: Solo usuarios autenticados guardan historial
3. **Token**: Clerk maneja refresh automáticamente con `getToken()`
4. **Errores**: Siempre verifica `response.ok` antes de parsear JSON
5. **Loading**: Muestra indicadores de carga para mejor UX

---

## 🎯 Flujo Típico

```
1. Usuario abre app
   ↓
2. Cargar categorías (GET /categories)
   ↓
3. Usuario hace pregunta
   ↓
4. Si está autenticado → Enviar con token
   Si no → Enviar sin token
   ↓
5. Mostrar respuesta
   ↓
6. Si autenticado → Recargar historial
```

---

¿Necesitas más ejemplos? Consulta `EJEMPLOS_INTEGRACION.md` 🚀
