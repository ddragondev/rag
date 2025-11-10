# 🔌 Ejemplos de Integración por Framework

## 📋 Índice

1. [React + Clerk](#react--clerk)
2. [Next.js + Clerk](#nextjs--clerk)
3. [Vue.js](#vuejs)
4. [Angular](#angular)
5. [Vanilla JavaScript](#vanilla-javascript)
6. [Python (Backend to Backend)](#python-backend-to-backend)
7. [Postman Collection](#postman-collection)

---

# React + Clerk

## Setup completo

### 1. Instalar dependencias

```bash
npm install @clerk/clerk-react
```

### 2. Configurar App.tsx

```tsx
// App.tsx
import { ClerkProvider } from "@clerk/clerk-react";
import { ChatApp } from "./components/ChatApp";

const CLERK_PUBLISHABLE_KEY = import.meta.env.VITE_CLERK_PUBLISHABLE_KEY;

function App() {
  return (
    <ClerkProvider publishableKey={CLERK_PUBLISHABLE_KEY}>
      <ChatApp />
    </ClerkProvider>
  );
}

export default App;
```

### 3. Hook personalizado (src/hooks/useRAG.ts)

```typescript
import { useState } from "react";
import { useAuth } from "@clerk/clerk-react";

interface AskParams {
  question: string;
  category: string;
  format?: "html" | "plain" | "both";
}

interface Message {
  role: "user" | "assistant";
  content: string;
  timestamp: string;
}

const API_BASE = import.meta.env.VITE_API_BASE || "http://localhost:8000";

export function useRAG() {
  const { getToken, isSignedIn } = useAuth();
  const [loading, setLoading] = useState(false);
  const [error, setError] = useState<string | null>(null);

  const ask = async ({ question, category, format = "both" }: AskParams) => {
    setLoading(true);
    setError(null);

    try {
      const headers: Record<string, string> = {
        "Content-Type": "application/json",
      };

      if (isSignedIn) {
        const token = await getToken();
        if (token) {
          headers["Authorization"] = `Bearer ${token}`;
        }
      }

      const response = await fetch(`${API_BASE}/ask`, {
        method: "POST",
        headers,
        body: JSON.stringify({
          question,
          category,
          format,
        }),
      });

      if (!response.ok) {
        throw new Error(`HTTP error! status: ${response.status}`);
      }

      const data = await response.json();
      return data;
    } catch (err: any) {
      setError(err.message);
      throw err;
    } finally {
      setLoading(false);
    }
  };

  const getHistory = async (limit = 100): Promise<Message[]> => {
    if (!isSignedIn) {
      return [];
    }

    try {
      const token = await getToken();

      const response = await fetch(`${API_BASE}/my-history?limit=${limit}`, {
        headers: {
          Authorization: `Bearer ${token}`,
        },
      });

      if (!response.ok) {
        throw new Error("Failed to fetch history");
      }

      const data = await response.json();
      return data.history || [];
    } catch (err: any) {
      setError(err.message);
      return [];
    }
  };

  const clearHistory = async () => {
    if (!isSignedIn) return;

    try {
      const token = await getToken();

      const response = await fetch(`${API_BASE}/my-history`, {
        method: "DELETE",
        headers: {
          Authorization: `Bearer ${token}`,
        },
      });

      if (!response.ok) {
        throw new Error("Failed to clear history");
      }
    } catch (err: any) {
      setError(err.message);
      throw err;
    }
  };

  const getCategories = async () => {
    try {
      const response = await fetch(`${API_BASE}/categories`);

      if (!response.ok) {
        throw new Error("Failed to fetch categories");
      }

      const data = await response.json();
      return data.categories || [];
    } catch (err: any) {
      setError(err.message);
      return [];
    }
  };

  return {
    ask,
    getHistory,
    clearHistory,
    getCategories,
    loading,
    error,
    isSignedIn,
  };
}
```

### 4. Componente de Chat (src/components/ChatApp.tsx)

```tsx
import React, { useState, useEffect } from "react";
import {
  SignInButton,
  SignOutButton,
  SignedIn,
  SignedOut,
  useUser,
} from "@clerk/clerk-react";
import { useRAG } from "../hooks/useRAG";

export function ChatApp() {
  const { user } = useUser();
  const { ask, getHistory, clearHistory, getCategories, loading, isSignedIn } =
    useRAG();

  const [question, setQuestion] = useState("");
  const [category, setCategory] = useState("geomecanica");
  const [categories, setCategories] = useState<any[]>([]);
  const [history, setHistory] = useState<any[]>([]);
  const [currentAnswer, setCurrentAnswer] = useState<any>(null);

  useEffect(() => {
    loadCategories();
  }, []);

  useEffect(() => {
    if (isSignedIn) {
      loadHistory();
    } else {
      setHistory([]);
    }
  }, [isSignedIn]);

  const loadCategories = async () => {
    const cats = await getCategories();
    setCategories(cats);
    if (cats.length > 0) {
      setCategory(cats[0].name);
    }
  };

  const loadHistory = async () => {
    const hist = await getHistory(50);
    setHistory(hist);
  };

  const handleSubmit = async (e: React.FormEvent) => {
    e.preventDefault();

    if (!question.trim()) return;

    try {
      const answer = await ask({
        question,
        category,
        format: "both",
      });

      setCurrentAnswer(answer);
      setQuestion("");

      // Recargar historial si está autenticado
      if (isSignedIn) {
        await loadHistory();
      }
    } catch (error) {
      console.error("Error:", error);
      alert("Error al procesar la pregunta");
    }
  };

  const handleClearHistory = async () => {
    if (confirm("¿Estás seguro de eliminar todo tu historial?")) {
      try {
        await clearHistory();
        setHistory([]);
        alert("Historial eliminado");
      } catch (error) {
        alert("Error al eliminar historial");
      }
    }
  };

  return (
    <div className="chat-app">
      {/* Header */}
      <header className="header">
        <h1>💬 RAG Chat Assistant</h1>

        <div className="auth-section">
          <SignedOut>
            <div className="warning">
              ⚠️ Sin cuenta tu historial no se guarda
            </div>
            <SignInButton mode="modal">
              <button className="btn-login">🔐 Iniciar Sesión</button>
            </SignInButton>
          </SignedOut>

          <SignedIn>
            <div className="user-info">
              <span>
                👋 {user?.firstName || user?.emailAddresses[0].emailAddress}
              </span>
              <SignOutButton>
                <button className="btn-logout">Cerrar Sesión</button>
              </SignOutButton>
            </div>
          </SignedIn>
        </div>
      </header>

      <div className="main-container">
        {/* Sidebar con historial */}
        <aside className="sidebar">
          <div className="sidebar-header">
            <h3>📜 Historial</h3>
            <SignedIn>
              {history.length > 0 && (
                <button
                  onClick={handleClearHistory}
                  className="btn-clear"
                  title="Limpiar historial"
                >
                  🗑️
                </button>
              )}
            </SignedIn>
          </div>

          <div className="history-container">
            <SignedOut>
              <p className="no-auth-message">
                Inicia sesión para ver tu historial
              </p>
            </SignedOut>

            <SignedIn>
              {history.length === 0 ? (
                <p className="no-history">No hay conversaciones aún</p>
              ) : (
                <div className="history-list">
                  {history.map((msg, idx) => (
                    <div key={idx} className={`history-item ${msg.role}`}>
                      <div className="msg-icon">
                        {msg.role === "user" ? "👤" : "🤖"}
                      </div>
                      <div className="msg-content">
                        <div className="msg-text">
                          {msg.content.substring(0, 80)}
                          {msg.content.length > 80 && "..."}
                        </div>
                        <div className="msg-time">
                          {new Date(msg.timestamp).toLocaleTimeString()}
                        </div>
                      </div>
                    </div>
                  ))}
                </div>
              )}
            </SignedIn>
          </div>
        </aside>

        {/* Área principal */}
        <main className="main-content">
          {/* Conversación actual */}
          {currentAnswer && (
            <div className="answer-container">
              <div className="question">
                <strong>Pregunta:</strong> {currentAnswer.question}
              </div>

              <div className="answer">
                <strong>Respuesta:</strong>
                <div
                  dangerouslySetInnerHTML={{ __html: currentAnswer.answer }}
                />
              </div>

              {currentAnswer.sources && (
                <div className="sources">
                  <strong>Fuentes:</strong>
                  <div
                    dangerouslySetInnerHTML={{ __html: currentAnswer.sources }}
                  />
                </div>
              )}
            </div>
          )}

          {/* Formulario */}
          <form onSubmit={handleSubmit} className="chat-form">
            <select
              value={category}
              onChange={(e) => setCategory(e.target.value)}
              className="category-select"
            >
              {categories.map((cat) => (
                <option key={cat.name} value={cat.name}>
                  {cat.display_name || cat.name}
                </option>
              ))}
            </select>

            <input
              type="text"
              value={question}
              onChange={(e) => setQuestion(e.target.value)}
              placeholder="Escribe tu pregunta..."
              className="question-input"
              disabled={loading}
            />

            <button
              type="submit"
              disabled={loading || !question.trim()}
              className="btn-send"
            >
              {loading ? "⏳ Procesando..." : "📤 Enviar"}
            </button>
          </form>
        </main>
      </div>
    </div>
  );
}
```

### 5. Variables de entorno (.env)

```env
VITE_CLERK_PUBLISHABLE_KEY=pk_test_xxxxxxxxxxxxx
VITE_API_BASE=http://localhost:8000
```

---

# Next.js + Clerk

## Setup completo

### 1. Instalar dependencias

```bash
npm install @clerk/nextjs
```

### 2. Configurar middleware (middleware.ts)

```typescript
import { authMiddleware } from "@clerk/nextjs";

export default authMiddleware({
  publicRoutes: ["/", "/api/public"],
});

export const config = {
  matcher: ["/((?!.+\\.[\\w]+$|_next).*)", "/", "/(api|trpc)(.*)"],
};
```

### 3. Layout con ClerkProvider (app/layout.tsx)

```tsx
import { ClerkProvider } from "@clerk/nextjs";
import "./globals.css";

export default function RootLayout({
  children,
}: {
  children: React.ReactNode;
}) {
  return (
    <ClerkProvider>
      <html lang="es">
        <body>{children}</body>
      </html>
    </ClerkProvider>
  );
}
```

### 4. API Route para proxy (app/api/ask/route.ts)

```typescript
import { auth } from "@clerk/nextjs";
import { NextRequest, NextResponse } from "next/server";

const API_BASE = process.env.BACKEND_API_BASE || "http://localhost:8000";

export async function POST(request: NextRequest) {
  try {
    const { userId, getToken } = auth();
    const body = await request.json();

    const headers: Record<string, string> = {
      "Content-Type": "application/json",
    };

    // Si hay usuario autenticado, agregar token
    if (userId) {
      const token = await getToken();
      if (token) {
        headers["Authorization"] = `Bearer ${token}`;
      }
    }

    const response = await fetch(`${API_BASE}/ask`, {
      method: "POST",
      headers,
      body: JSON.stringify(body),
    });

    const data = await response.json();

    return NextResponse.json(data);
  } catch (error: any) {
    return NextResponse.json({ error: error.message }, { status: 500 });
  }
}
```

### 5. Componente de página (app/chat/page.tsx)

```tsx
"use client";

import { useState } from "react";
import { useAuth, SignInButton, SignOutButton, useUser } from "@clerk/nextjs";

export default function ChatPage() {
  const { isSignedIn } = useAuth();
  const { user } = useUser();
  const [question, setQuestion] = useState("");
  const [answer, setAnswer] = useState<any>(null);
  const [loading, setLoading] = useState(false);

  const handleAsk = async (e: React.FormEvent) => {
    e.preventDefault();
    setLoading(true);

    try {
      const response = await fetch("/api/ask", {
        method: "POST",
        headers: {
          "Content-Type": "application/json",
        },
        body: JSON.stringify({
          question,
          category: "geomecanica",
          format: "both",
        }),
      });

      const data = await response.json();
      setAnswer(data);
      setQuestion("");
    } catch (error) {
      console.error("Error:", error);
    } finally {
      setLoading(false);
    }
  };

  return (
    <div className="container">
      <header>
        <h1>RAG Chat</h1>
        {isSignedIn ? (
          <div>
            <span>Hola, {user?.firstName}</span>
            <SignOutButton />
          </div>
        ) : (
          <SignInButton mode="modal" />
        )}
      </header>

      <form onSubmit={handleAsk}>
        <input
          type="text"
          value={question}
          onChange={(e) => setQuestion(e.target.value)}
          placeholder="Tu pregunta..."
          disabled={loading}
        />
        <button type="submit" disabled={loading}>
          {loading ? "Procesando..." : "Preguntar"}
        </button>
      </form>

      {answer && (
        <div className="answer">
          <div dangerouslySetInnerHTML={{ __html: answer.answer }} />
        </div>
      )}
    </div>
  );
}
```

### 6. Variables de entorno (.env.local)

```env
NEXT_PUBLIC_CLERK_PUBLISHABLE_KEY=pk_test_xxxxxxxxxxxxx
CLERK_SECRET_KEY=sk_test_xxxxxxxxxxxxx
BACKEND_API_BASE=http://localhost:8000
```

---

# Vue.js

## Setup con Composition API

### 1. Composable (composables/useRAG.ts)

```typescript
import { ref } from "vue";

const API_BASE = import.meta.env.VITE_API_BASE || "http://localhost:8000";

export function useRAG() {
  const loading = ref(false);
  const error = ref<string | null>(null);

  const ask = async (question: string, category: string, token?: string) => {
    loading.value = true;
    error.value = null;

    try {
      const headers: Record<string, string> = {
        "Content-Type": "application/json",
      };

      if (token) {
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

      if (!response.ok) {
        throw new Error(`HTTP error! status: ${response.status}`);
      }

      return await response.json();
    } catch (err: any) {
      error.value = err.message;
      throw err;
    } finally {
      loading.value = false;
    }
  };

  const getHistory = async (token: string, limit = 100) => {
    try {
      const response = await fetch(`${API_BASE}/my-history?limit=${limit}`, {
        headers: {
          Authorization: `Bearer ${token}`,
        },
      });

      if (!response.ok) {
        throw new Error("Failed to fetch history");
      }

      const data = await response.json();
      return data.history || [];
    } catch (err: any) {
      error.value = err.message;
      return [];
    }
  };

  return {
    ask,
    getHistory,
    loading,
    error,
  };
}
```

### 2. Componente (components/ChatApp.vue)

```vue
<template>
  <div class="chat-app">
    <header>
      <h1>RAG Chat</h1>
    </header>

    <form @submit.prevent="handleAsk">
      <select v-model="category">
        <option value="geomecanica">Geomecánica</option>
        <option value="compliance">Compliance</option>
      </select>

      <input
        v-model="question"
        type="text"
        placeholder="Tu pregunta..."
        :disabled="loading"
      />

      <button type="submit" :disabled="loading || !question.trim()">
        {{ loading ? "Procesando..." : "Enviar" }}
      </button>
    </form>

    <div v-if="answer" class="answer">
      <div v-html="answer.answer"></div>
      <div v-if="answer.sources" v-html="answer.sources"></div>
    </div>

    <div v-if="error" class="error">Error: {{ error }}</div>
  </div>
</template>

<script setup lang="ts">
import { ref } from "vue";
import { useRAG } from "../composables/useRAG";

const { ask, loading, error } = useRAG();

const question = ref("");
const category = ref("geomecanica");
const answer = ref<any>(null);

const handleAsk = async () => {
  if (!question.value.trim()) return;

  try {
    answer.value = await ask(question.value, category.value);
    question.value = "";
  } catch (err) {
    console.error("Error:", err);
  }
};
</script>
```

---

# Vanilla JavaScript

## Sin frameworks

```html
<!DOCTYPE html>
<html lang="es">
  <head>
    <meta charset="UTF-8" />
    <meta name="viewport" content="width=device-width, initial-scale=1.0" />
    <title>RAG Chat</title>
    <style>
      body {
        font-family: Arial, sans-serif;
        max-width: 800px;
        margin: 50px auto;
        padding: 20px;
      }
      .form-group {
        margin-bottom: 15px;
      }
      select,
      input,
      button {
        width: 100%;
        padding: 10px;
        margin-top: 5px;
      }
      .answer {
        margin-top: 20px;
        padding: 20px;
        background: #f5f5f5;
        border-radius: 5px;
      }
      .loading {
        color: #666;
      }
    </style>
  </head>
  <body>
    <h1>💬 RAG Chat Assistant</h1>

    <form id="chatForm">
      <div class="form-group">
        <label for="category">Categoría:</label>
        <select id="category">
          <option value="geomecanica">Geomecánica</option>
          <option value="compliance">Compliance</option>
          <option value="test">Test</option>
        </select>
      </div>

      <div class="form-group">
        <label for="question">Pregunta:</label>
        <input
          type="text"
          id="question"
          placeholder="Escribe tu pregunta..."
          required
        />
      </div>

      <button type="submit" id="submitBtn">Enviar</button>
    </form>

    <div id="loading" class="loading" style="display:none;">
      ⏳ Procesando tu pregunta...
    </div>

    <div id="answer" class="answer" style="display:none;"></div>

    <script>
      const API_BASE = "http://localhost:8000";

      document
        .getElementById("chatForm")
        .addEventListener("submit", async (e) => {
          e.preventDefault();

          const question = document.getElementById("question").value;
          const category = document.getElementById("category").value;

          // Mostrar loading
          document.getElementById("loading").style.display = "block";
          document.getElementById("answer").style.display = "none";
          document.getElementById("submitBtn").disabled = true;

          try {
            const response = await fetch(`${API_BASE}/ask`, {
              method: "POST",
              headers: {
                "Content-Type": "application/json",
              },
              body: JSON.stringify({
                question: question,
                category: category,
                format: "both",
              }),
            });

            if (!response.ok) {
              throw new Error(`HTTP error! status: ${response.status}`);
            }

            const data = await response.json();

            // Mostrar respuesta
            const answerDiv = document.getElementById("answer");
            answerDiv.innerHTML = `
                    <h3>Respuesta:</h3>
                    ${data.answer}
                    ${data.sources ? `<h4>Fuentes:</h4>${data.sources}` : ""}
                `;
            answerDiv.style.display = "block";

            // Limpiar formulario
            document.getElementById("question").value = "";
          } catch (error) {
            alert("Error: " + error.message);
          } finally {
            document.getElementById("loading").style.display = "none";
            document.getElementById("submitBtn").disabled = false;
          }
        });
    </script>
  </body>
</html>
```

---

# Python (Backend to Backend)

## Cliente Python para llamar a la API

```python
#!/usr/bin/env python3
"""
Cliente Python para interactuar con la API RAG
"""

import requests
from typing import Optional, Dict, List

class RAGClient:
    def __init__(self, base_url: str = "http://localhost:8000", token: Optional[str] = None):
        self.base_url = base_url
        self.token = token
        self.session = requests.Session()

        if token:
            self.session.headers.update({
                'Authorization': f'Bearer {token}'
            })

    def ask(
        self,
        question: str,
        category: str,
        format: str = "both",
        session_id: Optional[str] = None
    ) -> Dict:
        """Hace una pregunta al sistema RAG"""
        payload = {
            "question": question,
            "category": category,
            "format": format
        }

        if session_id and not self.token:
            payload["session_id"] = session_id

        response = self.session.post(
            f"{self.base_url}/ask",
            json=payload
        )
        response.raise_for_status()
        return response.json()

    def get_history(self, limit: int = 100) -> List[Dict]:
        """Obtiene el historial (requiere autenticación)"""
        if not self.token:
            raise ValueError("Token requerido para obtener historial")

        response = self.session.get(
            f"{self.base_url}/my-history",
            params={"limit": limit}
        )
        response.raise_for_status()
        data = response.json()
        return data.get("history", [])

    def clear_history(self) -> Dict:
        """Limpia el historial (requiere autenticación)"""
        if not self.token:
            raise ValueError("Token requerido para limpiar historial")

        response = self.session.delete(f"{self.base_url}/my-history")
        response.raise_for_status()
        return response.json()

    def get_categories(self) -> List[Dict]:
        """Obtiene todas las categorías disponibles"""
        response = self.session.get(f"{self.base_url}/categories")
        response.raise_for_status()
        data = response.json()
        return data.get("categories", [])

    def health_check(self) -> Dict:
        """Verifica el estado del sistema"""
        response = self.session.get(f"{self.base_url}/health")
        response.raise_for_status()
        return response.json()


# Ejemplo de uso
if __name__ == "__main__":
    # Sin autenticación
    client = RAGClient()

    # Verificar salud
    health = client.health_check()
    print("Sistema:", health)

    # Listar categorías
    categories = client.get_categories()
    print(f"\nCategorías disponibles: {len(categories)}")
    for cat in categories:
        print(f"  - {cat['display_name']}: {cat['description']}")

    # Hacer pregunta
    answer = client.ask(
        question="¿Qué es la geomecánica?",
        category="geomecanica",
        format="plain"
    )
    print(f"\nPregunta: {answer['question']}")
    print(f"Respuesta: {answer['answer_plain'][:200]}...")

    # Con autenticación (necesitas un token de Clerk)
    # token = "tu_jwt_token_aqui"
    # auth_client = RAGClient(token=token)
    # history = auth_client.get_history(limit=10)
    # print(f"\nHistorial: {len(history)} mensajes")
```

---

# Postman Collection

## Importar en Postman

```json
{
  "info": {
    "name": "RAG API",
    "schema": "https://schema.getpostman.com/json/collection/v2.1.0/collection.json"
  },
  "variable": [
    {
      "key": "base_url",
      "value": "http://localhost:8000"
    },
    {
      "key": "clerk_token",
      "value": "eyJhbGc..."
    }
  ],
  "item": [
    {
      "name": "Health Check",
      "request": {
        "method": "GET",
        "url": "{{base_url}}/health"
      }
    },
    {
      "name": "Get Categories",
      "request": {
        "method": "GET",
        "url": "{{base_url}}/categories"
      }
    },
    {
      "name": "Ask Question (No Auth)",
      "request": {
        "method": "POST",
        "url": "{{base_url}}/ask",
        "header": [
          {
            "key": "Content-Type",
            "value": "application/json"
          }
        ],
        "body": {
          "mode": "raw",
          "raw": "{\n  \"question\": \"¿Qué es la geomecánica?\",\n  \"category\": \"geomecanica\",\n  \"format\": \"plain\"\n}"
        }
      }
    },
    {
      "name": "Ask Question (With Auth)",
      "request": {
        "method": "POST",
        "url": "{{base_url}}/ask",
        "header": [
          {
            "key": "Content-Type",
            "value": "application/json"
          },
          {
            "key": "Authorization",
            "value": "Bearer {{clerk_token}}"
          }
        ],
        "body": {
          "mode": "raw",
          "raw": "{\n  \"question\": \"¿Qué es la geomecánica?\",\n  \"category\": \"geomecanica\",\n  \"format\": \"both\"\n}"
        }
      }
    },
    {
      "name": "Get My History",
      "request": {
        "method": "GET",
        "url": "{{base_url}}/my-history?limit=50",
        "header": [
          {
            "key": "Authorization",
            "value": "Bearer {{clerk_token}}"
          }
        ]
      }
    },
    {
      "name": "Clear My History",
      "request": {
        "method": "DELETE",
        "url": "{{base_url}}/my-history",
        "header": [
          {
            "key": "Authorization",
            "value": "Bearer {{clerk_token}}"
          }
        ]
      }
    }
  ]
}
```

---

# 🎯 Resumen de Integración

## Flujo Típico

1. **Inicializar cliente** con URL base
2. **Obtener token** de Clerk (si está autenticado)
3. **Listar categorías** disponibles
4. **Hacer pregunta** con categoría seleccionada
5. **Mostrar respuesta** con fuentes
6. **Cargar historial** (si está autenticado)

## Endpoints Más Usados

| Endpoint      | Frecuencia | Autenticación |
| ------------- | ---------- | ------------- |
| `/ask`        | Alta       | Opcional      |
| `/categories` | Media      | No            |
| `/my-history` | Media      | Requerida     |
| `/health`     | Baja       | No            |

## Mejores Prácticas

1. **Caché del frontend:** Guarda categorías en localStorage
2. **Debounce:** Espera 300ms antes de enviar pregunta
3. **Retry logic:** Reintentar requests fallidos (3 intentos máx)
4. **Loading states:** Mostrar indicadores de carga
5. **Error handling:** Manejar todos los códigos HTTP

---

¿Necesitas ayuda con algún framework específico? 🚀
