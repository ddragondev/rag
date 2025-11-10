# 🔐 Integración Clerk Auth con Sistema RAG

## 📋 Resumen

Esta guía muestra cómo integrar **Clerk** (autenticación) con tu sistema RAG para:

✅ Autenticar usuarios con JWT
✅ Asociar conversaciones a usuarios específicos
✅ Mantener historial personal por usuario
✅ Proteger endpoints sensibles
✅ Soportar usuarios anónimos y autenticados

---

## 🏗️ Arquitectura

```
┌─────────────────────────────────────────────────────────────┐
│                   FRONTEND (React + Clerk)                   │
│                                                              │
│  Usuario login → Clerk genera JWT → Frontend guarda token   │
└────────────────────────┬─────────────────────────────────────┘
                         │
                         │ HTTP Request
                         │ Header: Authorization: Bearer <jwt>
                         ▼
┌─────────────────────────────────────────────────────────────┐
│                     BACKEND (FastAPI)                        │
│                                                              │
│  1. Middleware valida JWT con JWKS de Clerk                 │
│  2. Extrae user_id del token                                │
│  3. Usa user_id como session_id                             │
│  4. Guarda conversaciones con metadata de usuario           │
└────────────────────────┬─────────────────────────────────────┘
                         │
                         ▼
┌─────────────────────────────────────────────────────────────┐
│                        MONGODB                               │
│                                                              │
│  conversations: {                                           │
│    session_id: "user_2xxxxx",  ← Clerk user_id            │
│    messages: [...],                                        │
│    metadata: {                                             │
│      user_id: "user_2xxxxx",                               │
│      email: "usuario@ejemplo.com",                         │
│      full_name: "Juan Pérez"                               │
│    }                                                        │
│  }                                                          │
└─────────────────────────────────────────────────────────────┘
```

---

## 🚀 Configuración Paso a Paso

### 1️⃣ Variables de Entorno

Agrega a tu `.env`:

```env
# OpenAI (ya existente)
OPENAI_API_KEY=sk-...

# MongoDB (ya existente)
MONGO_URI=mongodb+srv://...

# Clerk (nuevo)
CLERK_PUBLISHABLE_KEY=pk_test_xxxxx
CLERK_SECRET_KEY=sk_test_xxxxx
```

**Dónde obtener las keys de Clerk:**

1. Ve a https://dashboard.clerk.com
2. Selecciona tu aplicación
3. Ve a "API Keys"
4. Copia `Publishable Key` y `Secret Key`

### 2️⃣ Instalar Dependencias

```bash
pip install python-jose[cryptography] pyjwt requests
```

O actualiza desde `requirements.txt`:

```bash
pip install -r requirements.txt
```

### 3️⃣ Archivos Creados

- ✅ `clerk_auth.py` - Middleware de autenticación
- ✅ `example_clerk_integration.py` - Ejemplos de uso
- ✅ Esta documentación

---

## 🎯 Tipos de Endpoints

### 1. **Públicos** (sin auth)

```python
@app.get("/health")
async def health():
    return {"status": "healthy"}
```

### 2. **Auth Opcional** (funciona con y sin auth)

```python
from clerk_auth import optional_auth, get_session_id_from_user

@app.post("/ask")
async def ask(
    request: QuestionRequest,
    user: Optional[ClerkUser] = Depends(optional_auth)  # ⬅️ Opcional
):
    # Si hay usuario, usa su ID
    session_id = get_session_id_from_user(user, request.session_id)

    # Procesar pregunta...

    # Solo guarda historial si hay session_id
    if session_id:
        mongo.save_conversation_message(session_id, "user", question)
```

**Ventajas:**

- Usuarios anónimos pueden usar el sistema
- Usuarios autenticados obtienen historial persistente
- Transición suave entre anónimo y autenticado

### 3. **Protegidos** (requieren auth)

```python
from clerk_auth import require_auth

@app.get("/my-conversations")
async def get_my_conversations(
    user: ClerkUser = Depends(require_auth)  # ⬅️ Requerido
):
    # Solo usuarios autenticados pueden acceder
    conversations = mongo.conversations_collection.find({
        "session_id": user.user_id
    })

    return {"conversations": list(conversations)}
```

**Uso:**

- Datos personales del usuario
- Historial de conversaciones
- Configuración de usuario
- Operaciones sensibles

---

## 💻 Integración Frontend

### React + Clerk

```tsx
import { useAuth } from "@clerk/clerk-react";

function ChatComponent() {
  const { getToken, isSignedIn } = useAuth();

  const askQuestion = async (question: string, category: string) => {
    let headers: any = {
      "Content-Type": "application/json",
    };

    // Si está autenticado, agregar token
    if (isSignedIn) {
      const token = await getToken();
      headers["Authorization"] = `Bearer ${token}`;
    }

    const response = await fetch("http://localhost:8000/ask", {
      method: "POST",
      headers: headers,
      body: JSON.stringify({
        question: question,
        category: category,
        format: "both",
        // No enviar session_id si está autenticado
      }),
    });

    const data = await response.json();

    // data.authenticated indica si se usó auth
    // data.user_email tiene el email del usuario

    return data;
  };

  return (
    <div className="chat-container">
      {isSignedIn ? (
        <p>Bienvenido! Tu historial se guarda automáticamente.</p>
      ) : (
        <p>Puedes preguntar sin cuenta, pero no se guardará historial.</p>
      )}

      {/* Tu componente de chat */}
    </div>
  );
}
```

### Obtener Historial del Usuario

```tsx
function MyHistoryPage() {
  const { getToken } = useAuth();
  const [history, setHistory] = useState([]);

  useEffect(() => {
    const fetchHistory = async () => {
      const token = await getToken();

      const response = await fetch("http://localhost:8000/my-history", {
        headers: {
          Authorization: `Bearer ${token}`,
        },
      });

      const data = await response.json();
      setHistory(data.history);
    };

    fetchHistory();
  }, []);

  return (
    <div>
      <h2>Mi Historial</h2>
      {history.map((msg, idx) => (
        <div key={idx}>
          <strong>{msg.role}:</strong> {msg.content}
        </div>
      ))}
    </div>
  );
}
```

---

## 🗄️ Estructura de Datos en MongoDB

### Conversación con Usuario Autenticado

```javascript
{
  "_id": ObjectId("..."),
  "session_id": "user_2xxxxxxxxxxxxx",  // ⬅️ Clerk user_id
  "messages": [
    {
      "role": "user",
      "content": "¿Qué es la geomecánica?",
      "timestamp": ISODate("2025-11-10T12:00:00Z"),
      "metadata": {
        "category": "geomecanica",
        "format": "html",
        "user_id": "user_2xxxxxxxxxxxxx",  // ⬅️ ID de Clerk
        "email": "juan@ejemplo.com",        // ⬅️ Email del usuario
        "full_name": "Juan Pérez",          // ⬅️ Nombre completo
        "authenticated": true
      }
    },
    {
      "role": "assistant",
      "content": "La geomecánica es...",
      "timestamp": ISODate("2025-11-10T12:00:05Z"),
      "metadata": { /* mismo */ }
    }
  ],
  "created_at": ISODate("2025-11-10T12:00:00Z"),
  "updated_at": ISODate("2025-11-10T12:00:05Z"),
  "message_count": 2
}
```

### Conversación Anónima (sin auth)

```javascript
{
  "_id": ObjectId("..."),
  "session_id": null,  // ⬅️ Sin sesión (no se guarda)
  // O si el frontend envía un session_id temporal:
  "session_id": "temp_abc123",  // ⬅️ ID temporal del frontend
  "messages": [...],
  "metadata": {
    "authenticated": false  // ⬅️ No autenticado
  }
}
```

---

## 🔒 Flujos de Autenticación

### Flujo 1: Usuario Anónimo

```
1. Usuario abre app → No está autenticado
2. Hace pregunta → Backend NO guarda historial (o usa session_id temporal)
3. Respuesta se entrega → No hay persistencia
4. Usuario cierra app → Pierde historial
```

### Flujo 2: Usuario Autenticado

```
1. Usuario hace login con Clerk → Obtiene JWT
2. Frontend guarda token
3. Cada pregunta incluye token en header
4. Backend:
   - Valida JWT
   - Extrae user_id
   - Usa user_id como session_id
   - Guarda en MongoDB con metadata de usuario
5. Historial persiste para siempre
6. Usuario puede ver su historial en /my-history
```

### Flujo 3: Transición Anónimo → Autenticado

```
1. Usuario anónimo hace preguntas → No se guarda
2. Usuario decide hacer login
3. A partir de ahora, todas las conversaciones se guardan
4. Historial previo no se migra (era anónimo)
```

**Opción avanzada**: Puedes implementar migración de sesión temporal:

```typescript
// Antes del login, guarda session_id temporal
const tempSessionId = localStorage.getItem("tempSessionId");

// Después del login
if (tempSessionId) {
  // Llamar endpoint para migrar conversación
  await fetch("/migrate-session", {
    method: "POST",
    headers: { Authorization: `Bearer ${token}` },
    body: JSON.stringify({ temp_session_id: tempSessionId }),
  });
}
```

---

## 🎨 Endpoints Recomendados

### Para Integrar en tu main.py

```python
from clerk_auth import optional_auth, require_auth, get_session_id_from_user

# 1. Preguntas con auth opcional
@app.post("/ask")
async def ask(request: QuestionRequest, user: Optional[ClerkUser] = Depends(optional_auth)):
    session_id = get_session_id_from_user(user, request.session_id)
    # ... tu lógica actual

# 2. Obtener mis conversaciones (protegido)
@app.get("/my-conversations")
async def my_conversations(user: ClerkUser = Depends(require_auth)):
    return mongo.get_active_sessions_for_user(user.user_id)

# 3. Obtener mi historial (protegido)
@app.get("/my-history")
async def my_history(user: ClerkUser = Depends(require_auth)):
    history = mongo.get_conversation_history(user.user_id, limit=100)
    return {"history": history, "user_email": user.email}

# 4. Limpiar mi historial (protegido)
@app.delete("/my-history")
async def clear_my_history(user: ClerkUser = Depends(require_auth)):
    mongo.clear_conversation(user.user_id)
    return {"message": "Historial eliminado"}

# 5. Perfil de usuario (protegido)
@app.get("/me")
async def get_me(user: ClerkUser = Depends(require_auth)):
    return {
        "user_id": user.user_id,
        "email": user.email,
        "full_name": user.full_name
    }
```

---

## 📊 Ventajas de esta Arquitectura

### ✅ Para el Usuario

1. **Sin barreras**: Puede probar sin cuenta
2. **Historial personal**: Si se registra, guarda todo
3. **Multi-dispositivo**: Accede desde cualquier lugar
4. **Privacidad**: Solo ve su propio historial

### ✅ Para el Desarrollador

1. **Simple**: Clerk maneja toda la auth
2. **Seguro**: JWT verificado con JWKS
3. **Escalable**: Stateless (no sesiones en servidor)
4. **Flexible**: Endpoints públicos y protegidos

### ✅ Para el Sistema

1. **Performance**: Auth opcional no afecta velocidad
2. **Caché inteligente**: Anónimos usan caché, autenticados guardan
3. **Trazabilidad**: Sabes qué usuario hizo cada pregunta
4. **Analytics**: Puedes analizar uso por usuario

---

## 🚨 Consideraciones de Seguridad

### 1. **CORS**

```python
app.add_middleware(
    CORSMiddleware,
    allow_origins=["https://tu-frontend.com"],  # ⬅️ Específico en producción
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)
```

### 2. **Rate Limiting**

```python
from slowapi import Limiter

limiter = Limiter(key_func=lambda: user.user_id if user else "anonymous")

@app.post("/ask")
@limiter.limit("10/minute")  # ⬅️ 10 preguntas por minuto
async def ask(...):
    pass
```

### 3. **Validación de Datos**

```python
# Ya tienes con Pydantic ✅
class QuestionRequest(BaseModel):
    question: str
    category: str
    format: str = "both"
```

---

## 🧪 Pruebas

### Probar sin Auth

```bash
curl -X POST http://localhost:8000/ask \
  -H "Content-Type: application/json" \
  -d '{"question": "test", "category": "geomecanica", "format": "plain"}'
```

### Probar con Auth

```bash
# Obtener token del frontend de Clerk primero
TOKEN="eyJhbGc..."

curl -X POST http://localhost:8000/ask \
  -H "Content-Type: application/json" \
  -H "Authorization: Bearer $TOKEN" \
  -d '{"question": "test", "category": "geomecanica", "format": "plain"}'
```

### Ver historial

```bash
curl http://localhost:8000/my-history \
  -H "Authorization: Bearer $TOKEN"
```

---

## 📝 Checklist de Implementación

- [ ] Instalar dependencias (`pip install -r requirements.txt`)
- [ ] Agregar `CLERK_PUBLISHABLE_KEY` y `CLERK_SECRET_KEY` a `.env`
- [ ] Copiar `clerk_auth.py` al proyecto
- [ ] Actualizar endpoints en `main.py` con decoradores de auth
- [ ] Configurar CORS para tu frontend
- [ ] Probar con Postman/curl
- [ ] Integrar en frontend con `@clerk/clerk-react`
- [ ] Probar flujo completo (anónimo → login → historial)
- [ ] Deploy a producción

---

## 🎉 Resultado Final

```
Usuario Anónimo → Pregunta → Respuesta rápida (caché) → No guarda

Usuario con Login → Pregunta → Respuesta + Guarda en DB → Historial personal
                    ↓
                Puede ver historial desde cualquier dispositivo
                Puede eliminar su historial
                Tiene experiencia personalizada
```

---

¿Necesitas ayuda con algún paso específico? 🚀
