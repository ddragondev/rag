# 📡 API Endpoints - Documentación Completa

## 🌐 Base URL

```
http://localhost:8000
```

En producción: `https://tu-dominio.com`

---

## 📋 Índice de Endpoints

### Públicos (sin autenticación)

1. [GET /health](#get-health) - Estado del sistema
2. [GET /categories](#get-categories) - Listar categorías
3. [POST /upload-pdf](#post-upload-pdf) - Subir PDF
4. [POST /upload-video](#post-upload-video) - Subir video MP4
5. [GET /mongodb/health](#get-mongodbhealth) - Estado MongoDB
6. [GET /mongodb/metrics](#get-mongodbmetrics) - Métricas del sistema

### Auth Opcional (funcionan con/sin token)

7. [POST /ask](#post-ask) - Hacer pregunta
8. [POST /ask-video](#post-ask-video) - Pregunta sobre video

### Protegidos (requieren autenticación)

9. [GET /my-history](#get-my-history) - Obtener historial personal
10. [DELETE /my-history](#delete-my-history) - Limpiar historial
11. [GET /my-conversations](#get-my-conversations) - Listar conversaciones

### Administración

12. [POST /categories](#post-categories) - Crear categoría
13. [PUT /categories/{name}](#put-categoriesname) - Actualizar categoría
14. [DELETE /categories/{name}](#delete-categoriesname) - Eliminar categoría
15. [GET /cache/stats](#get-cachestats) - Estadísticas de caché
16. [DELETE /cache/clear](#delete-cacheclear) - Limpiar caché

---

# 📌 Endpoints Públicos

## GET /health

**Descripción:** Verifica el estado del sistema.

### Request

```bash
curl http://localhost:8000/health
```

### Response

```json
{
  "status": "healthy",
  "message": "Sistema funcionando correctamente"
}
```

### Status Codes

- `200` - Sistema funcionando
- `500` - Error en el sistema

---

## GET /categories

**Descripción:** Lista todas las categorías disponibles con sus configuraciones.

### Request

```bash
curl http://localhost:8000/categories
```

### Response

```json
{
  "categories": [
    {
      "name": "geomecanica",
      "display_name": "Geomecánica",
      "description": "Documentos sobre mecánica de rocas y suelos",
      "document_count": 15,
      "last_updated": "2025-11-10T12:00:00Z",
      "prompts": {
        "html": "Prompt personalizado HTML...",
        "plain": "Prompt personalizado texto plano..."
      }
    },
    {
      "name": "compliance",
      "display_name": "Compliance",
      "description": "Normativas y regulaciones",
      "document_count": 8,
      "last_updated": "2025-11-10T12:00:00Z"
    }
  ],
  "total": 2
}
```

### Campos de Response

| Campo            | Tipo              | Descripción                       |
| ---------------- | ----------------- | --------------------------------- |
| `name`           | string            | Nombre interno de la categoría    |
| `display_name`   | string            | Nombre para mostrar               |
| `description`    | string            | Descripción de la categoría       |
| `document_count` | number            | Cantidad de documentos            |
| `last_updated`   | string (ISO 8601) | Última actualización              |
| `prompts`        | object            | Prompts personalizados (opcional) |

### Status Codes

- `200` - Categorías obtenidas correctamente
- `500` - Error al obtener categorías

---

## POST /upload-pdf

**Descripción:** Sube uno o más archivos PDF y los procesa para una categoría.

### Request

```bash
curl -X POST http://localhost:8000/upload-pdf \
  -F "category=geomecanica" \
  -F "files=@/path/to/document1.pdf" \
  -F "files=@/path/to/document2.pdf"
```

### Request Body (multipart/form-data)

| Campo      | Tipo   | Requerido | Descripción            |
| ---------- | ------ | --------- | ---------------------- |
| `category` | string | ✅        | Nombre de la categoría |
| `files`    | file[] | ✅        | Uno o más archivos PDF |

### Response

```json
{
  "message": "2 archivos PDF subidos correctamente",
  "category": "geomecanica",
  "files_processed": [
    {
      "filename": "document1.pdf",
      "pages": 50,
      "status": "processed"
    },
    {
      "filename": "document2.pdf",
      "pages": 30,
      "status": "processed"
    }
  ],
  "vectorstore_updated": true
}
```

### Status Codes

- `200` - Archivos procesados correctamente
- `400` - Categoría inválida o archivos no PDF
- `500` - Error al procesar archivos

### Notas

- Máximo 10 archivos por request
- Tamaño máximo por archivo: 50MB
- Solo acepta archivos PDF

---

## POST /upload-video

**Descripción:** Sube un archivo de video MP4 y lo procesa.

### Request

```bash
curl -X POST http://localhost:8000/upload-video \
  -F "category=geomecanica" \
  -F "video_id=intro-rocas" \
  -F "file=@/path/to/video.mp4"
```

### Request Body (multipart/form-data)

| Campo      | Tipo   | Requerido | Descripción            |
| ---------- | ------ | --------- | ---------------------- |
| `category` | string | ✅        | Nombre de la categoría |
| `video_id` | string | ✅        | ID único del video     |
| `file`     | file   | ✅        | Archivo MP4            |

### Response

```json
{
  "message": "Video procesado correctamente",
  "video_id": "intro-rocas",
  "category": "geomecanica",
  "frames_extracted": 120,
  "vectorstore_updated": true
}
```

### Status Codes

- `200` - Video procesado correctamente
- `400` - Archivo no es MP4 o parámetros inválidos
- `500` - Error al procesar video

---

## GET /mongodb/health

**Descripción:** Verifica la conexión con MongoDB.

### Request

```bash
curl http://localhost:8000/mongodb/health
```

### Response

```json
{
  "status": "connected",
  "database": "rag_system",
  "collections": {
    "answer_cache": 150,
    "conversations": 45,
    "categories": 3,
    "metrics": 500
  },
  "server_info": {
    "version": "7.0.0",
    "maxBsonObjectSize": 16777216
  }
}
```

### Status Codes

- `200` - MongoDB conectado
- `500` - Error de conexión

---

## GET /mongodb/metrics

**Descripción:** Obtiene métricas del sistema.

### Request

```bash
curl http://localhost:8000/mongodb/metrics
```

### Response

```json
{
  "cache_stats": {
    "total_entries": 150,
    "total_hits": 1200,
    "total_misses": 300,
    "hit_rate": 0.8
  },
  "conversation_stats": {
    "total_conversations": 45,
    "total_messages": 890,
    "active_sessions": 12
  },
  "recent_metrics": [
    {
      "type": "cache_hit",
      "timestamp": "2025-11-10T12:00:00Z",
      "data": { "cache_key": "abc123" }
    }
  ]
}
```

### Status Codes

- `200` - Métricas obtenidas
- `500` - Error al obtener métricas

---

# 🔓 Endpoints con Auth Opcional

## POST /ask

**Descripción:** Hace una pregunta al sistema RAG. Si el usuario está autenticado, guarda el historial.

### Request (Sin autenticación)

```bash
curl -X POST http://localhost:8000/ask \
  -H "Content-Type: application/json" \
  -d '{
    "question": "¿Qué es la geomecánica?",
    "category": "geomecanica",
    "format": "both"
  }'
```

### Request (Con autenticación)

```bash
curl -X POST http://localhost:8000/ask \
  -H "Content-Type: application/json" \
  -H "Authorization: Bearer eyJhbGc..." \
  -d '{
    "question": "¿Qué es la geomecánica?",
    "category": "geomecanica",
    "format": "both"
  }'
```

### Request Body

```json
{
  "question": "¿Qué es la geomecánica?",
  "category": "geomecanica",
  "format": "both",
  "session_id": "opcional-solo-para-anonimos"
}
```

### Campos del Request

| Campo        | Tipo   | Requerido | Descripción                    |
| ------------ | ------ | --------- | ------------------------------ |
| `question`   | string | ✅        | Pregunta del usuario           |
| `category`   | string | ✅        | Categoría de documentos        |
| `format`     | string | ✅        | `"html"`, `"plain"` o `"both"` |
| `session_id` | string | ❌        | Solo para usuarios anónimos    |

### Response (Sin autenticación)

```json
{
  "question": "¿Qué es la geomecánica?",
  "category": "geomecanica",
  "format": "both",
  "answer": "<p>La geomecánica es...</p>",
  "answer_plain": "La geomecánica es...",
  "sources": "<ul><li>Manual de Geomecánica (pág. 10)</li></ul>",
  "sources_plain": "• Manual de Geomecánica (pág. 10)",
  "authenticated": false
}
```

### Response (Con autenticación)

```json
{
  "question": "¿Qué es la geomecánica?",
  "category": "geomecanica",
  "format": "both",
  "session_id": "user_2abc123",
  "answer": "<p>La geomecánica es...</p>",
  "answer_plain": "La geomecánica es...",
  "sources": "<ul><li>Manual de Geomecánica (pág. 10)</li></ul>",
  "sources_plain": "• Manual de Geomecánica (pág. 10)",
  "authenticated": true,
  "user_email": "usuario@ejemplo.com",
  "user_id": "user_2abc123"
}
```

### Campos del Response

| Campo           | Tipo    | Descripción                                           |
| --------------- | ------- | ----------------------------------------------------- |
| `question`      | string  | Pregunta original                                     |
| `category`      | string  | Categoría usada                                       |
| `format`        | string  | Formato de respuesta                                  |
| `answer`        | string  | Respuesta en HTML (si format="html" o "both")         |
| `answer_plain`  | string  | Respuesta en texto plano (si format="plain" o "both") |
| `sources`       | string  | Fuentes en HTML                                       |
| `sources_plain` | string  | Fuentes en texto plano                                |
| `session_id`    | string  | ID de sesión (solo autenticados)                      |
| `authenticated` | boolean | Si el usuario está autenticado                        |
| `user_email`    | string  | Email del usuario (solo autenticados)                 |
| `user_id`       | string  | ID del usuario (solo autenticados)                    |

### Status Codes

- `200` - Pregunta procesada correctamente
- `400` - Parámetros inválidos
- `401` - Token inválido (si se proporciona)
- `500` - Error al procesar pregunta

### Notas

- **Sin auth:** Usa caché para respuestas rápidas
- **Con auth:** Guarda historial en MongoDB
- **Historial conversacional:** Si hay `session_id`, incluye contexto de mensajes anteriores

---

## POST /ask-video

**Descripción:** Hace una pregunta sobre un video específico.

### Request (Con autenticación)

```bash
curl -X POST http://localhost:8000/ask-video \
  -H "Content-Type: application/json" \
  -H "Authorization: Bearer eyJhbGc..." \
  -d '{
    "question": "¿Qué muestra el video en el minuto 2?",
    "category": "geomecanica",
    "video_id": "intro-rocas",
    "format": "plain"
  }'
```

### Request Body

```json
{
  "question": "¿Qué muestra el video en el minuto 2?",
  "category": "geomecanica",
  "video_id": "intro-rocas",
  "format": "plain",
  "session_id": "opcional"
}
```

### Campos del Request

| Campo        | Tipo   | Requerido | Descripción                    |
| ------------ | ------ | --------- | ------------------------------ |
| `question`   | string | ✅        | Pregunta sobre el video        |
| `category`   | string | ✅        | Categoría del video            |
| `video_id`   | string | ✅        | ID del video                   |
| `format`     | string | ✅        | `"html"`, `"plain"` o `"both"` |
| `session_id` | string | ❌        | Solo para usuarios anónimos    |

### Response

```json
{
  "question": "¿Qué muestra el video en el minuto 2?",
  "category": "geomecanica",
  "video_id": "intro-rocas",
  "format": "plain",
  "answer_plain": "En el minuto 2 del video se muestra...",
  "sources_plain": "• Video: intro-rocas (frame 120)",
  "authenticated": true,
  "user_email": "usuario@ejemplo.com"
}
```

### Status Codes

- `200` - Pregunta procesada correctamente
- `400` - Video no encontrado o parámetros inválidos
- `500` - Error al procesar pregunta

---

# 🔒 Endpoints Protegidos (Requieren Autenticación)

## GET /my-history

**Descripción:** Obtiene el historial de conversaciones del usuario autenticado.

### Request

```bash
curl http://localhost:8000/my-history?limit=50 \
  -H "Authorization: Bearer eyJhbGc..."
```

### Query Parameters

| Parámetro | Tipo   | Default | Descripción                 |
| --------- | ------ | ------- | --------------------------- |
| `limit`   | number | 100     | Cantidad máxima de mensajes |

### Response

```json
{
  "user_id": "user_2abc123",
  "user_email": "usuario@ejemplo.com",
  "history": [
    {
      "role": "user",
      "content": "¿Qué es la geomecánica?",
      "timestamp": "2025-11-10T12:00:00Z",
      "metadata": {
        "category": "geomecanica",
        "format": "html",
        "user_id": "user_2abc123",
        "email": "usuario@ejemplo.com",
        "full_name": "Juan Pérez",
        "authenticated": true
      }
    },
    {
      "role": "assistant",
      "content": "La geomecánica es la ciencia...",
      "timestamp": "2025-11-10T12:00:05Z",
      "metadata": {
        "category": "geomecanica",
        "format": "html",
        "user_id": "user_2abc123",
        "email": "usuario@ejemplo.com",
        "full_name": "Juan Pérez",
        "authenticated": true
      }
    }
  ],
  "total_messages": 2
}
```

### Campos del Response

| Campo                 | Tipo   | Descripción              |
| --------------------- | ------ | ------------------------ |
| `user_id`             | string | ID de Clerk del usuario  |
| `user_email`          | string | Email del usuario        |
| `history`             | array  | Array de mensajes        |
| `history[].role`      | string | `"user"` o `"assistant"` |
| `history[].content`   | string | Contenido del mensaje    |
| `history[].timestamp` | string | Fecha/hora ISO 8601      |
| `history[].metadata`  | object | Información adicional    |
| `total_messages`      | number | Total de mensajes        |

### Status Codes

- `200` - Historial obtenido correctamente
- `401` - No autenticado o token inválido
- `500` - Error al obtener historial

### Ejemplo de uso en Frontend

```typescript
const getMyHistory = async () => {
  const token = await getToken(); // Clerk hook

  const response = await fetch("http://localhost:8000/my-history?limit=50", {
    headers: {
      Authorization: `Bearer ${token}`,
    },
  });

  const data = await response.json();
  return data.history;
};
```

---

## DELETE /my-history

**Descripción:** Elimina todo el historial de conversaciones del usuario autenticado.

### Request

```bash
curl -X DELETE http://localhost:8000/my-history \
  -H "Authorization: Bearer eyJhbGc..."
```

### Response

```json
{
  "message": "Historial eliminado correctamente",
  "user_email": "usuario@ejemplo.com"
}
```

### Status Codes

- `200` - Historial eliminado correctamente
- `401` - No autenticado o token inválido
- `500` - Error al eliminar historial

### Ejemplo de uso en Frontend

```typescript
const clearMyHistory = async () => {
  const token = await getToken();

  const response = await fetch("http://localhost:8000/my-history", {
    method: "DELETE",
    headers: {
      Authorization: `Bearer ${token}`,
    },
  });

  if (response.ok) {
    alert("Historial eliminado");
  }
};
```

---

## GET /my-conversations

**Descripción:** Lista todas las sesiones de conversación del usuario con resúmenes.

### Request

```bash
curl http://localhost:8000/my-conversations \
  -H "Authorization: Bearer eyJhbGc..."
```

### Response

```json
{
  "user_email": "usuario@ejemplo.com",
  "conversations": [
    {
      "session_id": "user_2abc123",
      "message_count": 10,
      "created_at": "2025-11-10T10:00:00Z",
      "updated_at": "2025-11-10T12:30:00Z",
      "last_message": "La geomecánica es la ciencia que estudia..."
    }
  ],
  "total": 1
}
```

### Campos del Response

| Campo                           | Tipo   | Descripción                              |
| ------------------------------- | ------ | ---------------------------------------- |
| `user_email`                    | string | Email del usuario                        |
| `conversations`                 | array  | Array de conversaciones                  |
| `conversations[].session_id`    | string | ID de la sesión                          |
| `conversations[].message_count` | number | Cantidad de mensajes                     |
| `conversations[].created_at`    | string | Fecha de creación                        |
| `conversations[].updated_at`    | string | Última actualización                     |
| `conversations[].last_message`  | string | Último mensaje (primeros 100 caracteres) |
| `total`                         | number | Total de conversaciones                  |

### Status Codes

- `200` - Conversaciones obtenidas correctamente
- `401` - No autenticado o token inválido
- `500` - Error al obtener conversaciones

---

# 🛠️ Endpoints de Administración

## POST /categories

**Descripción:** Crea una nueva categoría.

### Request

```bash
curl -X POST http://localhost:8000/categories \
  -H "Content-Type: application/json" \
  -d '{
    "name": "mineria",
    "display_name": "Minería",
    "description": "Documentos sobre minería",
    "prompts": {
      "html": "Prompt personalizado HTML...",
      "plain": "Prompt personalizado texto..."
    }
  }'
```

### Request Body

```json
{
  "name": "mineria",
  "display_name": "Minería",
  "description": "Documentos sobre minería",
  "prompts": {
    "html": "Eres un experto en minería...",
    "plain": "Eres un experto en minería..."
  }
}
```

### Response

```json
{
  "message": "Categoría creada correctamente",
  "category": {
    "name": "mineria",
    "display_name": "Minería",
    "description": "Documentos sobre minería",
    "created_at": "2025-11-10T12:00:00Z"
  }
}
```

### Status Codes

- `200` - Categoría creada
- `400` - Categoría ya existe o parámetros inválidos
- `500` - Error al crear categoría

---

## PUT /categories/{name}

**Descripción:** Actualiza una categoría existente.

### Request

```bash
curl -X PUT http://localhost:8000/categories/mineria \
  -H "Content-Type: application/json" \
  -d '{
    "display_name": "Minería Subterránea",
    "description": "Documentos sobre minería subterránea",
    "prompts": {
      "html": "Nuevo prompt HTML...",
      "plain": "Nuevo prompt texto..."
    }
  }'
```

### Response

```json
{
  "message": "Categoría actualizada correctamente",
  "category": "mineria"
}
```

### Status Codes

- `200` - Categoría actualizada
- `404` - Categoría no encontrada
- `500` - Error al actualizar categoría

---

## DELETE /categories/{name}

**Descripción:** Elimina una categoría y todos sus documentos.

### Request

```bash
curl -X DELETE http://localhost:8000/categories/mineria
```

### Response

```json
{
  "message": "Categoría eliminada correctamente",
  "category": "mineria",
  "documents_deleted": 15
}
```

### Status Codes

- `200` - Categoría eliminada
- `404` - Categoría no encontrada
- `500` - Error al eliminar categoría

---

## GET /cache/stats

**Descripción:** Obtiene estadísticas del caché.

### Request

```bash
curl http://localhost:8000/cache/stats
```

### Response

```json
{
  "total_entries": 150,
  "total_hits": 1200,
  "total_misses": 300,
  "hit_rate": 0.8,
  "cache_size_mb": 25.5,
  "oldest_entry": "2025-11-01T10:00:00Z",
  "newest_entry": "2025-11-10T12:00:00Z"
}
```

### Status Codes

- `200` - Estadísticas obtenidas
- `500` - Error al obtener estadísticas

---

## DELETE /cache/clear

**Descripción:** Limpia todo el caché.

### Request

```bash
curl -X DELETE http://localhost:8000/cache/clear
```

### Response

```json
{
  "message": "Caché limpiada correctamente",
  "entries_deleted": 150
}
```

### Status Codes

- `200` - Caché limpiada
- `500` - Error al limpiar caché

---

# 🔐 Autenticación con Clerk

## Cómo obtener el token JWT

### En React/Next.js:

```typescript
import { useAuth } from "@clerk/clerk-react";

function MyComponent() {
  const { getToken } = useAuth();

  const callAPI = async () => {
    const token = await getToken();

    const response = await fetch("http://localhost:8000/my-history", {
      headers: {
        Authorization: `Bearer ${token}`,
      },
    });

    return response.json();
  };
}
```

### Formato del Header:

```
Authorization: Bearer eyJhbGciOiJSUzI1NiIsInR5cCI6IkpXVCIsImtpZCI6Imluc18...
```

## Endpoints que aceptan autenticación

| Endpoint            | Auth      | Comportamiento                                         |
| ------------------- | --------- | ------------------------------------------------------ |
| `/ask`              | Opcional  | Con auth: guarda historial. Sin auth: usa caché        |
| `/ask-video`        | Opcional  | Con auth: guarda historial. Sin auth: respuesta simple |
| `/my-history`       | Requerida | Solo funciona autenticado                              |
| `/my-conversations` | Requerida | Solo funciona autenticado                              |

---

# 📊 Códigos de Error

## 400 - Bad Request

```json
{
  "detail": "Invalid format. Must be 'html', 'plain' or 'both'"
}
```

## 401 - Unauthorized

```json
{
  "detail": "Not authenticated"
}
```

## 404 - Not Found

```json
{
  "detail": "Category not found"
}
```

## 500 - Internal Server Error

```json
{
  "detail": "Error processing request: [error message]"
}
```

---

# 🎯 Ejemplos de Integración Frontend

## React Hook Completo

```typescript
// hooks/useRAG.ts
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

      if (!response.ok) {
        throw new Error(`HTTP ${response.status}`);
      }

      return await response.json();
    } finally {
      setLoading(false);
    }
  };

  const getHistory = async () => {
    if (!isSignedIn) return [];

    const token = await getToken();
    const response = await fetch(`${API_BASE}/my-history`, {
      headers: {
        Authorization: `Bearer ${token}`,
      },
    });

    const data = await response.json();
    return data.history;
  };

  const clearHistory = async () => {
    if (!isSignedIn) return;

    const token = await getToken();
    await fetch(`${API_BASE}/my-history`, {
      method: "DELETE",
      headers: {
        Authorization: `Bearer ${token}`,
      },
    });
  };

  return {
    ask,
    getHistory,
    clearHistory,
    loading,
  };
}
```

## Uso del Hook

```tsx
function ChatComponent() {
  const { ask, getHistory, clearHistory, loading } = useRAG();
  const [answer, setAnswer] = useState(null);

  const handleAsk = async () => {
    const result = await ask("¿Qué es la geomecánica?", "geomecanica");
    setAnswer(result);
  };

  const handleLoadHistory = async () => {
    const history = await getHistory();
    console.log("Mi historial:", history);
  };

  return (
    <div>
      <button onClick={handleAsk} disabled={loading}>
        Preguntar
      </button>
      <button onClick={handleLoadHistory}>Ver Historial</button>
      <button onClick={clearHistory}>Limpiar Historial</button>

      {answer && <div dangerouslySetInnerHTML={{ __html: answer.answer }} />}
    </div>
  );
}
```

---

# 🧪 Pruebas con cURL

## Flujo completo de prueba

```bash
# 1. Verificar salud
curl http://localhost:8000/health

# 2. Listar categorías
curl http://localhost:8000/categories

# 3. Pregunta sin autenticación
curl -X POST http://localhost:8000/ask \
  -H "Content-Type: application/json" \
  -d '{
    "question": "¿Qué es la geomecánica?",
    "category": "geomecanica",
    "format": "plain"
  }'

# 4. Pregunta con autenticación
TOKEN="tu_jwt_token_aqui"

curl -X POST http://localhost:8000/ask \
  -H "Content-Type: application/json" \
  -H "Authorization: Bearer $TOKEN" \
  -d '{
    "question": "¿Qué es la geomecánica?",
    "category": "geomecanica",
    "format": "plain"
  }'

# 5. Ver historial
curl http://localhost:8000/my-history \
  -H "Authorization: Bearer $TOKEN"

# 6. Ver conversaciones
curl http://localhost:8000/my-conversations \
  -H "Authorization: Bearer $TOKEN"

# 7. Limpiar historial
curl -X DELETE http://localhost:8000/my-history \
  -H "Authorization: Bearer $TOKEN"
```

---

# 📝 Notas Importantes

## Límites y Restricciones

- **Rate Limit:** Sin límite actualmente (agregar en producción)
- **Tamaño máximo de pregunta:** 1000 caracteres
- **Tamaño máximo de PDF:** 50MB
- **Historial máximo:** 100 mensajes por defecto
- **Timeout de requests:** 30 segundos

## Mejores Prácticas

1. **Caché:** Usa caché para usuarios anónimos (pregunta sin `session_id`)
2. **Autenticación:** Siempre verifica que el token sea válido antes de enviarlo
3. **Errores:** Maneja todos los códigos de error (400, 401, 404, 500)
4. **Historial:** Carga el historial al inicio solo si el usuario está autenticado
5. **Token refresh:** Usa `getToken()` de Clerk que maneja el refresh automáticamente

## CORS

El servidor está configurado para aceptar requests desde cualquier origen en desarrollo:

```python
allow_origins=["*"]  # Solo en desarrollo
```

**En producción, cambiar a:**

```python
allow_origins=[
    "https://tu-frontend.com",
    "https://app.tu-dominio.com"
]
```

---

# 🚀 ¡Listo para Integrar!

Con esta documentación tienes todo lo necesario para:

- ✅ Integrar todos los endpoints en tu frontend
- ✅ Manejar autenticación con Clerk
- ✅ Gestionar historial de usuarios
- ✅ Implementar flujos de trabajo completos
- ✅ Probar con cURL o Postman

**Documentación adicional:**

- `FRONTEND_HISTORIAL_USUARIO.md` - Componentes React completos
- `GUIA_INTEGRACION_CLERK.md` - Guía de autenticación
- `RESUMEN_CLERK_INTEGRATION.md` - Resumen ejecutivo

¿Necesitas ayuda con algún endpoint específico? 🎯
