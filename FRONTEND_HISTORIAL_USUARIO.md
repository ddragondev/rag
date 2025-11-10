# 💬 Historial de Conversaciones por Usuario - Frontend

## 🎯 Objetivo

Cada usuario autenticado con Clerk verá **solo su propio historial** de conversaciones. Los usuarios anónimos no tendrán historial persistente.

---

## 🏗️ Arquitectura del Flujo

```
┌─────────────────────────────────────────────────────────────┐
│                    USUARIO SE AUTENTICA                      │
│                                                              │
│  1. Login con Clerk → Obtiene JWT token                     │
│  2. Frontend guarda token automáticamente                   │
└────────────────────────┬─────────────────────────────────────┘
                         │
                         ▼
┌─────────────────────────────────────────────────────────────┐
│                  USUARIO HACE PREGUNTA                       │
│                                                              │
│  3. Frontend envía pregunta con token en Authorization      │
│  4. Backend extrae user_id del JWT                          │
│  5. Backend usa user_id como session_id                     │
│  6. Backend guarda conversación en MongoDB con user_id      │
└────────────────────────┬─────────────────────────────────────┘
                         │
                         ▼
┌─────────────────────────────────────────────────────────────┐
│              USUARIO CARGA SU HISTORIAL                      │
│                                                              │
│  7. Frontend llama /my-history con token                    │
│  8. Backend filtra conversaciones por user_id               │
│  9. Frontend muestra solo SUS conversaciones                │
└─────────────────────────────────────────────────────────────┘
```

---

## 🔧 Paso 1: Actualizar Backend (main.py)

### Agregar imports necesarios

```python
# Al inicio de main.py, agregar:
from clerk_auth import (
    optional_auth,
    require_auth,
    get_session_id_from_user,
    get_user_metadata,
    ClerkUser
)
from typing import Optional
from fastapi import Depends
```

### Modificar endpoint /ask

```python
@app.post("/ask")
async def ask_question(
    question_request: QuestionRequest,
    user: Optional[ClerkUser] = Depends(optional_auth)  # ⬅️ AGREGAR ESTO
):
    """Endpoint para hacer preguntas con historial por usuario."""
    question = question_request.question
    category = normalize_category(question_request.category)
    format_type = question_request.format.lower()

    # ⬇️ NUEVO: Usar user_id si está autenticado, sino usar el session_id del request
    session_id = get_session_id_from_user(user, question_request.session_id)

    if format_type not in ["html", "plain", "both"]:
        raise HTTPException(status_code=400, detail="Invalid format")

    try:
        # Si hay session_id, NO usar caché (para conversaciones con contexto)
        use_cache = session_id is None

        if use_cache:
            cache_key = get_cache_key(question, category, format_type)
            cached_answer = mongo.get_cached_answer(cache_key)
            if cached_answer:
                return cached_answer

        # ... (resto del código sigue igual)

        # Si hay session_id, agregar historial conversacional
        conversation_context = ""
        if session_id:
            history = get_conversation_history(session_id)
            conversation_context = format_conversation_context(history)
            result["session_id"] = session_id

            # ⬇️ NUEVO: Agregar info del usuario si está autenticado
            if user:
                result["authenticated"] = True
                result["user_email"] = user.email

        # ... (resto del código para generar respuesta)

        # Guardar en historial si hay sesión
        if session_id:
            # ⬇️ NUEVO: Agregar metadata del usuario
            metadata = {
                "category": category,
                "format": "html"
            }

            if user:
                metadata.update(get_user_metadata(user))

            add_to_conversation(session_id, "user", question, metadata)
            add_to_conversation(session_id, "assistant", answer, metadata)

        return result

    except HTTPException as e:
        raise e
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))
```

### Agregar endpoint para obtener historial del usuario

```python
@app.get("/my-history")
async def get_my_history(
    limit: int = 100,
    user: ClerkUser = Depends(require_auth)  # ⬅️ Requiere autenticación
):
    """Obtiene el historial de conversaciones del usuario autenticado."""
    try:
        # Usar el user_id como session_id
        history = mongo.get_conversation_history(user.user_id, limit=limit)

        return {
            "user_id": user.user_id,
            "user_email": user.email,
            "history": history,
            "total_messages": len(history)
        }
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))


@app.delete("/my-history")
async def clear_my_history(
    user: ClerkUser = Depends(require_auth)  # ⬅️ Requiere autenticación
):
    """Elimina el historial de conversaciones del usuario autenticado."""
    try:
        mongo.clear_conversation(user.user_id)

        return {
            "message": "Historial eliminado correctamente",
            "user_email": user.email
        }
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))


@app.get("/my-conversations")
async def get_my_conversations(
    user: ClerkUser = Depends(require_auth)  # ⬅️ Requiere autenticación
):
    """Lista todas las sesiones de conversación del usuario."""
    try:
        # Obtener todas las conversaciones del usuario
        conversations = mongo.conversations_collection.find({
            "session_id": user.user_id
        }).sort("updated_at", -1)

        result = []
        for conv in conversations:
            result.append({
                "session_id": conv["session_id"],
                "message_count": conv.get("message_count", 0),
                "created_at": conv["created_at"].isoformat(),
                "updated_at": conv["updated_at"].isoformat(),
                "last_message": conv["messages"][-1]["content"][:100] if conv["messages"] else ""
            })

        return {
            "user_email": user.email,
            "conversations": result,
            "total": len(result)
        }
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))
```

---

## 🎨 Paso 2: Implementar en Frontend (React + Clerk)

### Setup inicial de Clerk

```tsx
// App.tsx o main.tsx
import {
  ClerkProvider,
  SignInButton,
  SignOutButton,
  SignedIn,
  SignedOut,
  useAuth,
  useUser,
} from "@clerk/clerk-react";

const CLERK_PUBLISHABLE_KEY = "tu_pk_test_xxxxx";

function App() {
  return (
    <ClerkProvider publishableKey={CLERK_PUBLISHABLE_KEY}>
      <ChatApp />
    </ClerkProvider>
  );
}
```

### Hook personalizado para el historial

```tsx
// hooks/useConversationHistory.ts
import { useState, useEffect } from "react";
import { useAuth } from "@clerk/clerk-react";

interface Message {
  role: "user" | "assistant";
  content: string;
  timestamp: string;
  metadata?: any;
}

export function useConversationHistory() {
  const { getToken, isSignedIn } = useAuth();
  const [history, setHistory] = useState<Message[]>([]);
  const [loading, setLoading] = useState(false);
  const [error, setError] = useState<string | null>(null);

  // Cargar historial al montar el componente (solo si está autenticado)
  useEffect(() => {
    if (isSignedIn) {
      loadHistory();
    }
  }, [isSignedIn]);

  const loadHistory = async () => {
    if (!isSignedIn) {
      setHistory([]);
      return;
    }

    setLoading(true);
    setError(null);

    try {
      const token = await getToken();

      const response = await fetch(
        "http://localhost:8000/my-history?limit=100",
        {
          headers: {
            Authorization: `Bearer ${token}`,
          },
        }
      );

      if (!response.ok) {
        throw new Error("Error al cargar historial");
      }

      const data = await response.json();
      setHistory(data.history || []);
    } catch (err: any) {
      setError(err.message);
      console.error("Error loading history:", err);
    } finally {
      setLoading(false);
    }
  };

  const clearHistory = async () => {
    if (!isSignedIn) return;

    try {
      const token = await getToken();

      const response = await fetch("http://localhost:8000/my-history", {
        method: "DELETE",
        headers: {
          Authorization: `Bearer ${token}`,
        },
      });

      if (!response.ok) {
        throw new Error("Error al limpiar historial");
      }

      setHistory([]);
    } catch (err: any) {
      setError(err.message);
      console.error("Error clearing history:", err);
    }
  };

  const addMessage = (message: Message) => {
    setHistory((prev) => [...prev, message]);
  };

  return {
    history,
    loading,
    error,
    loadHistory,
    clearHistory,
    addMessage,
  };
}
```

### Hook para hacer preguntas

```tsx
// hooks/useAskQuestion.ts
import { useState } from "react";
import { useAuth } from "@clerk/clerk-react";

interface AskQuestionParams {
  question: string;
  category: string;
  format?: "html" | "plain" | "both";
}

export function useAskQuestion() {
  const { getToken, isSignedIn } = useAuth();
  const [loading, setLoading] = useState(false);
  const [error, setError] = useState<string | null>(null);

  const askQuestion = async ({
    question,
    category,
    format = "both",
  }: AskQuestionParams) => {
    setLoading(true);
    setError(null);

    try {
      let headers: any = {
        "Content-Type": "application/json",
      };

      // Si está autenticado, agregar token
      if (isSignedIn) {
        const token = await getToken();
        headers["Authorization"] = `Bearer ${token}`;
      }

      const body: any = {
        question,
        category,
        format,
      };

      // NO enviar session_id si está autenticado (el backend usa user_id)
      // Si quieres mantener sesiones anónimas, puedes generar un ID temporal:
      if (!isSignedIn) {
        // Generar o recuperar session_id temporal del localStorage
        let tempSessionId = localStorage.getItem("temp_session_id");
        if (!tempSessionId) {
          tempSessionId = `anon_${Date.now()}_${Math.random()
            .toString(36)
            .substr(2, 9)}`;
          localStorage.setItem("temp_session_id", tempSessionId);
        }
        body.session_id = tempSessionId;
      }

      const response = await fetch("http://localhost:8000/ask", {
        method: "POST",
        headers,
        body: JSON.stringify(body),
      });

      if (!response.ok) {
        throw new Error("Error al procesar la pregunta");
      }

      const data = await response.json();
      return data;
    } catch (err: any) {
      setError(err.message);
      console.error("Error asking question:", err);
      throw err;
    } finally {
      setLoading(false);
    }
  };

  return {
    askQuestion,
    loading,
    error,
  };
}
```

### Componente principal de Chat

```tsx
// components/ChatApp.tsx
import React, { useState } from "react";
import {
  SignInButton,
  SignOutButton,
  SignedIn,
  SignedOut,
  useUser,
} from "@clerk/clerk-react";
import { useConversationHistory } from "../hooks/useConversationHistory";
import { useAskQuestion } from "../hooks/useAskQuestion";

export function ChatApp() {
  const { user } = useUser();
  const {
    history,
    loading: historyLoading,
    clearHistory,
    addMessage,
  } = useConversationHistory();
  const { askQuestion, loading: askLoading } = useAskQuestion();

  const [question, setQuestion] = useState("");
  const [category, setCategory] = useState("geomecanica");
  const [currentAnswer, setCurrentAnswer] = useState<any>(null);

  const handleSubmit = async (e: React.FormEvent) => {
    e.preventDefault();

    if (!question.trim()) return;

    try {
      // Agregar pregunta al historial visual inmediatamente
      const userMessage = {
        role: "user" as const,
        content: question,
        timestamp: new Date().toISOString(),
      };
      addMessage(userMessage);

      // Enviar pregunta al backend
      const answer = await askQuestion({
        question,
        category,
        format: "both",
      });

      // Agregar respuesta al historial visual
      const assistantMessage = {
        role: "assistant" as const,
        content: answer.answer || answer.answer_plain,
        timestamp: new Date().toISOString(),
      };
      addMessage(assistantMessage);

      setCurrentAnswer(answer);
      setQuestion("");
    } catch (error) {
      console.error("Error:", error);
      alert("Error al procesar la pregunta");
    }
  };

  return (
    <div className="chat-app">
      {/* Header con autenticación */}
      <header className="chat-header">
        <h1>💬 RAG Chat Assistant</h1>

        <SignedOut>
          <div className="auth-section">
            <p>⚠️ Sin cuenta tu historial no se guarda</p>
            <SignInButton mode="modal">
              <button className="btn-login">🔐 Iniciar Sesión</button>
            </SignInButton>
          </div>
        </SignedOut>

        <SignedIn>
          <div className="auth-section">
            <p>
              👋 Hola, {user?.firstName || user?.emailAddresses[0].emailAddress}
            </p>
            <SignOutButton>
              <button className="btn-logout">Cerrar Sesión</button>
            </SignOutButton>
          </div>
        </SignedIn>
      </header>

      <div className="chat-container">
        {/* Sidebar con historial */}
        <aside className="chat-sidebar">
          <div className="sidebar-header">
            <h3>📜 Tu Historial</h3>

            <SignedIn>
              {history.length > 0 && (
                <button
                  onClick={clearHistory}
                  className="btn-clear"
                  title="Limpiar historial"
                >
                  🗑️
                </button>
              )}
            </SignedIn>
          </div>

          <SignedOut>
            <div className="sidebar-message">
              <p>📝 Inicia sesión para ver tu historial</p>
            </div>
          </SignedOut>

          <SignedIn>
            {historyLoading ? (
              <p>Cargando historial...</p>
            ) : history.length === 0 ? (
              <p className="no-history">No hay conversaciones aún</p>
            ) : (
              <div className="history-list">
                {history.map((msg, idx) => (
                  <div key={idx} className={`history-item ${msg.role}`}>
                    <div className="message-role">
                      {msg.role === "user" ? "👤" : "🤖"}
                    </div>
                    <div className="message-content">
                      {msg.content.substring(0, 80)}
                      {msg.content.length > 80 && "..."}
                    </div>
                    <div className="message-time">
                      {new Date(msg.timestamp).toLocaleTimeString()}
                    </div>
                  </div>
                ))}
              </div>
            )}
          </SignedIn>
        </aside>

        {/* Área principal de chat */}
        <main className="chat-main">
          {/* Conversación actual */}
          <div className="current-conversation">
            {history.slice(-10).map((msg, idx) => (
              <div key={idx} className={`message ${msg.role}`}>
                <div className="message-header">
                  <strong>{msg.role === "user" ? "Tú" : "Asistente"}</strong>
                  <span className="timestamp">
                    {new Date(msg.timestamp).toLocaleTimeString()}
                  </span>
                </div>
                <div
                  className="message-body"
                  dangerouslySetInnerHTML={{
                    __html: msg.content,
                  }}
                />
              </div>
            ))}
          </div>

          {/* Formulario de pregunta */}
          <form onSubmit={handleSubmit} className="chat-form">
            <select
              value={category}
              onChange={(e) => setCategory(e.target.value)}
              className="category-select"
            >
              <option value="geomecanica">🪨 Geomecánica</option>
              <option value="compliance">📋 Compliance</option>
              <option value="test">🧪 Test</option>
            </select>

            <input
              type="text"
              value={question}
              onChange={(e) => setQuestion(e.target.value)}
              placeholder="Escribe tu pregunta..."
              className="question-input"
              disabled={askLoading}
            />

            <button
              type="submit"
              disabled={askLoading || !question.trim()}
              className="btn-send"
            >
              {askLoading ? "⏳" : "📤"} Enviar
            </button>
          </form>
        </main>
      </div>
    </div>
  );
}
```

### Estilos CSS básicos

```css
/* styles/chat.css */
.chat-app {
  display: flex;
  flex-direction: column;
  height: 100vh;
  font-family: system-ui, -apple-system, sans-serif;
}

.chat-header {
  display: flex;
  justify-content: space-between;
  align-items: center;
  padding: 1rem 2rem;
  background: linear-gradient(135deg, #667eea 0%, #764ba2 100%);
  color: white;
  box-shadow: 0 2px 10px rgba(0, 0, 0, 0.1);
}

.chat-header h1 {
  margin: 0;
  font-size: 1.5rem;
}

.auth-section {
  display: flex;
  align-items: center;
  gap: 1rem;
}

.btn-login,
.btn-logout {
  padding: 0.5rem 1rem;
  border: none;
  border-radius: 0.5rem;
  cursor: pointer;
  font-weight: 600;
  transition: transform 0.2s;
}

.btn-login {
  background: white;
  color: #667eea;
}

.btn-logout {
  background: rgba(255, 255, 255, 0.2);
  color: white;
}

.btn-login:hover,
.btn-logout:hover {
  transform: scale(1.05);
}

.chat-container {
  display: flex;
  flex: 1;
  overflow: hidden;
}

.chat-sidebar {
  width: 300px;
  background: #f7f7f7;
  border-right: 1px solid #ddd;
  display: flex;
  flex-direction: column;
  overflow-y: auto;
}

.sidebar-header {
  display: flex;
  justify-content: space-between;
  align-items: center;
  padding: 1rem;
  border-bottom: 1px solid #ddd;
  background: white;
}

.sidebar-header h3 {
  margin: 0;
  font-size: 1.1rem;
}

.btn-clear {
  background: none;
  border: none;
  font-size: 1.2rem;
  cursor: pointer;
  opacity: 0.6;
  transition: opacity 0.2s;
}

.btn-clear:hover {
  opacity: 1;
}

.sidebar-message {
  padding: 2rem 1rem;
  text-align: center;
  color: #666;
}

.history-list {
  flex: 1;
  overflow-y: auto;
}

.history-item {
  display: flex;
  gap: 0.5rem;
  padding: 0.75rem 1rem;
  border-bottom: 1px solid #eee;
  cursor: pointer;
  transition: background 0.2s;
}

.history-item:hover {
  background: #fff;
}

.history-item.user {
  background: #f0f0f0;
}

.message-role {
  font-size: 1.2rem;
}

.message-content {
  flex: 1;
  font-size: 0.9rem;
  color: #333;
  overflow: hidden;
  text-overflow: ellipsis;
}

.message-time {
  font-size: 0.75rem;
  color: #999;
}

.chat-main {
  flex: 1;
  display: flex;
  flex-direction: column;
  background: white;
}

.current-conversation {
  flex: 1;
  overflow-y: auto;
  padding: 2rem;
}

.message {
  margin-bottom: 1.5rem;
  padding: 1rem;
  border-radius: 0.5rem;
}

.message.user {
  background: #e3f2fd;
  margin-left: 20%;
}

.message.assistant {
  background: #f5f5f5;
  margin-right: 20%;
}

.message-header {
  display: flex;
  justify-content: space-between;
  margin-bottom: 0.5rem;
  font-size: 0.9rem;
}

.message-header strong {
  color: #667eea;
}

.timestamp {
  color: #999;
  font-size: 0.8rem;
}

.message-body {
  line-height: 1.6;
}

.chat-form {
  display: flex;
  gap: 1rem;
  padding: 1.5rem;
  border-top: 1px solid #ddd;
  background: #fafafa;
}

.category-select {
  padding: 0.75rem;
  border: 1px solid #ddd;
  border-radius: 0.5rem;
  font-size: 1rem;
  min-width: 150px;
}

.question-input {
  flex: 1;
  padding: 0.75rem;
  border: 1px solid #ddd;
  border-radius: 0.5rem;
  font-size: 1rem;
}

.question-input:focus {
  outline: none;
  border-color: #667eea;
}

.btn-send {
  padding: 0.75rem 1.5rem;
  background: #667eea;
  color: white;
  border: none;
  border-radius: 0.5rem;
  font-weight: 600;
  cursor: pointer;
  transition: background 0.2s;
}

.btn-send:hover:not(:disabled) {
  background: #5568d3;
}

.btn-send:disabled {
  opacity: 0.5;
  cursor: not-allowed;
}

.no-history {
  padding: 2rem 1rem;
  text-align: center;
  color: #999;
  font-style: italic;
}
```

---

## 🚀 Resultado Final

### Para Usuario Anónimo:

- ✅ Puede hacer preguntas
- ❌ No ve historial (sidebar vacío)
- ❌ Historial no se guarda
- 💡 Ve mensaje: "Inicia sesión para guardar tu historial"

### Para Usuario Autenticado:

- ✅ Puede hacer preguntas
- ✅ Ve su historial en sidebar (solo suyo)
- ✅ Historial se guarda automáticamente
- ✅ Puede limpiar su historial
- ✅ Historial persiste entre sesiones y dispositivos

---

## 🔄 Flujo Completo

1. **Usuario abre la app** → Ve chat
2. **Sin login** → Puede preguntar pero no se guarda
3. **Hace login con Clerk** → Automáticamente se carga su historial
4. **Hace preguntas** → Se guardan con su user_id
5. **Cierra y reabre** → Su historial sigue ahí
6. **Otro usuario entra** → Solo ve SU historial, no el de otros

---

## 📊 MongoDB - Estructura

```javascript
// Usuario 1 (user_2abc123)
{
  "session_id": "user_2abc123",
  "messages": [
    {
      "role": "user",
      "content": "¿Qué es la geomecánica?",
      "metadata": {
        "user_id": "user_2abc123",
        "email": "juan@ejemplo.com",
        "full_name": "Juan Pérez"
      }
    }
  ]
}

// Usuario 2 (user_2xyz789) - Completamente separado
{
  "session_id": "user_2xyz789",
  "messages": [
    {
      "role": "user",
      "content": "¿Qué es compliance?",
      "metadata": {
        "user_id": "user_2xyz789",
        "email": "maria@ejemplo.com",
        "full_name": "María García"
      }
    }
  ]
}
```

---

## ✅ Checklist de Implementación

### Backend:

- [ ] Agregar imports de `clerk_auth` en `main.py`
- [ ] Modificar endpoint `/ask` con `user = Depends(optional_auth)`
- [ ] Usar `get_session_id_from_user(user, request.session_id)`
- [ ] Agregar metadata de usuario al guardar conversaciones
- [ ] Crear endpoint `/my-history` (GET)
- [ ] Crear endpoint `/my-history` (DELETE)
- [ ] Crear endpoint `/my-conversations` (GET)
- [ ] Reiniciar servidor FastAPI

### Frontend:

- [ ] Instalar Clerk: `npm install @clerk/clerk-react`
- [ ] Configurar `ClerkProvider` con tu `CLERK_PUBLISHABLE_KEY`
- [ ] Crear hook `useConversationHistory`
- [ ] Crear hook `useAskQuestion`
- [ ] Implementar componente `ChatApp`
- [ ] Agregar estilos CSS
- [ ] Probar flujo sin login
- [ ] Probar flujo con login
- [ ] Verificar que cada usuario ve solo su historial

---

## 🎉 ¡Listo!

Con esto tendrás un sistema completo donde:

- Cada usuario tiene su propio historial privado
- No hay cross-contamination entre usuarios
- Usuarios anónimos pueden usar el sistema sin restricciones
- Experiencia fluida entre anónimo y autenticado

¿Necesitas ayuda con alguna parte específica? 🚀
