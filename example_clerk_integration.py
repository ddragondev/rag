"""
Ejemplo de integración de Clerk Auth con el sistema RAG
Muestra cómo proteger endpoints y asociar conversaciones a usuarios
"""

from fastapi import FastAPI, Depends, HTTPException
from pydantic import BaseModel
from typing import Optional
from clerk_auth import (
    ClerkUser, 
    require_auth, 
    optional_auth,
    get_session_id_from_user,
    get_user_metadata
)
from mongo_manager import get_mongo_manager

app = FastAPI()
mongo = get_mongo_manager()


# ==================== MODELOS ====================

class QuestionRequest(BaseModel):
    question: str
    category: str
    format: str = "both"
    session_id: Optional[str] = None  # Opcional, se usará user_id si está autenticado


# ==================== ENDPOINTS PÚBLICOS ====================

@app.get("/")
async def root():
    """Endpoint público - no requiere auth."""
    return {"message": "PDF RAG API con Clerk Auth"}


@app.get("/health")
async def health():
    """Health check - público."""
    return {"status": "healthy"}


# ==================== ENDPOINTS CON AUTH OPCIONAL ====================

@app.post("/ask")
async def ask_question(
    request: QuestionRequest,
    user: Optional[ClerkUser] = Depends(optional_auth)  # ⬅️ Auth opcional
):
    """
    Endpoint de preguntas con autenticación OPCIONAL.
    
    - Si el usuario está autenticado: usa su user_id como session_id
    - Si no está autenticado: usa caché y no guarda historial
    """
    
    # Determinar session_id
    session_id = get_session_id_from_user(user, request.session_id)
    
    # Si hay usuario autenticado, guardar metadata
    if user and session_id:
        metadata = get_user_metadata(user)
        metadata["category"] = request.category
        metadata["format"] = request.format
        
        print(f"👤 Usuario autenticado: {user.email} ({user.user_id})")
        print(f"💬 Guardando conversación para: {session_id}")
    else:
        metadata = {
            "category": request.category,
            "format": request.format,
            "authenticated": False
        }
        print(f"🔓 Usuario anónimo (sin auth)")
    
    # Aquí va tu lógica normal de RAG...
    # answer = process_question(request.question, request.category, session_id)
    
    # Guardar en historial si hay sesión
    if session_id:
        mongo.save_conversation_message(
            session_id=session_id,
            role="user",
            content=request.question,
            metadata=metadata
        )
        
        # ... guardar respuesta también
        # mongo.save_conversation_message(session_id, "assistant", answer, metadata)
    
    return {
        "answer": "Respuesta...",
        "session_id": session_id,
        "authenticated": user is not None,
        "user_email": user.email if user else None
    }


# ==================== ENDPOINTS PROTEGIDOS (REQUIEREN AUTH) ====================

@app.get("/my-conversations")
async def get_my_conversations(
    user: ClerkUser = Depends(require_auth)  # ⬅️ Auth REQUERIDA
):
    """
    Obtiene las conversaciones del usuario autenticado.
    Solo accesible con token JWT válido.
    """
    
    # Buscar conversaciones del usuario
    conversations = mongo.conversations_collection.find(
        {"session_id": user.user_id}
    ).sort("updated_at", -1).limit(50)
    
    result = []
    for conv in conversations:
        result.append({
            "session_id": conv.get("session_id"),
            "message_count": conv.get("message_count", 0),
            "created_at": conv.get("created_at"),
            "updated_at": conv.get("updated_at"),
            "preview": conv.get("messages", [])[-1].get("content", "")[:100] if conv.get("messages") else ""
        })
    
    return {
        "user_id": user.user_id,
        "email": user.email,
        "conversations": result
    }


@app.get("/my-history")
async def get_my_history(
    user: ClerkUser = Depends(require_auth)
):
    """
    Obtiene el historial completo del usuario autenticado.
    """
    
    history = mongo.get_conversation_history(user.user_id, limit=100)
    
    return {
        "user_id": user.user_id,
        "email": user.email,
        "message_count": len(history),
        "history": history
    }


@app.delete("/my-history")
async def clear_my_history(
    user: ClerkUser = Depends(require_auth)
):
    """
    Limpia el historial del usuario autenticado.
    """
    
    deleted = mongo.clear_conversation(user.user_id)
    
    return {
        "message": "Historial eliminado",
        "user_id": user.user_id,
        "deleted": deleted
    }


# ==================== ENDPOINTS ADMIN (REQUIEREN ROLE ESPECIAL) ====================

@app.get("/admin/all-conversations")
async def get_all_conversations(
    user: ClerkUser = Depends(require_auth)
):
    """
    Obtiene TODAS las conversaciones (solo para admins).
    
    En producción, deberías verificar que el usuario tiene rol de admin:
    if user.email not in ["admin@tuempresa.com"]:
        raise HTTPException(403, "No autorizado")
    """
    
    # TODO: Agregar verificación de rol de admin
    # Por ahora, cualquier usuario autenticado puede ver todas
    
    active_sessions = mongo.get_active_sessions(hours=24)
    
    return {
        "admin_user": user.email,
        "total_sessions": len(active_sessions),
        "sessions": active_sessions
    }


# ==================== EJEMPLO DE USO EN FRONTEND ====================

"""
// Frontend (React + Clerk)

import { useAuth } from '@clerk/clerk-react';

function ChatComponent() {
  const { getToken } = useAuth();
  
  const askQuestion = async (question, category) => {
    // Obtener token JWT de Clerk
    const token = await getToken();
    
    // Hacer request con token en header
    const response = await fetch('http://localhost:8000/ask', {
      method: 'POST',
      headers: {
        'Content-Type': 'application/json',
        'Authorization': `Bearer ${token}`,  // ⬅️ Token aquí
      },
      body: JSON.stringify({
        question: question,
        category: category,
        format: 'both'
        // No enviar session_id, se usa el user_id automáticamente
      })
    });
    
    return await response.json();
  };
  
  // Obtener mis conversaciones
  const getMyConversations = async () => {
    const token = await getToken();
    
    const response = await fetch('http://localhost:8000/my-conversations', {
      headers: {
        'Authorization': `Bearer ${token}`,
      }
    });
    
    return await response.json();
  };
  
  return (
    <div>
      {/* Tu componente de chat */}
    </div>
  );
}
"""
