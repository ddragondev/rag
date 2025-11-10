"""
Middleware de autenticación con Clerk para FastAPI
Valida tokens JWT de Clerk y extrae información del usuario
"""

import os
import requests
from typing import Optional
from fastapi import HTTPException, Security, Depends
from fastapi.security import HTTPBearer, HTTPAuthorizationCredentials
from jose import jwt, JWTError
import dotenv

# Cargar variables de entorno
dotenv.load_dotenv()

# Configuración de Clerk
CLERK_PUBLISHABLE_KEY = os.getenv("CLERK_PUBLISHABLE_KEY")
CLERK_SECRET_KEY = os.getenv("CLERK_SECRET_KEY")
CLERK_JWKS_URL = "https://api.clerk.dev/v1/jwks"

# Security scheme
security = HTTPBearer(auto_error=False)


class ClerkUser:
    """Representa un usuario autenticado de Clerk."""
    
    def __init__(self, user_id: str, email: Optional[str] = None, 
                 first_name: Optional[str] = None, last_name: Optional[str] = None):
        self.user_id = user_id
        self.email = email
        self.first_name = first_name
        self.last_name = last_name
        self.full_name = f"{first_name} {last_name}".strip() if first_name or last_name else None
    
    def __repr__(self):
        return f"ClerkUser(user_id={self.user_id}, email={self.email})"


def get_clerk_jwks():
    """Obtiene las claves públicas JWKS de Clerk."""
    try:
        response = requests.get(CLERK_JWKS_URL)
        response.raise_for_status()
        return response.json()
    except Exception as e:
        print(f"❌ Error al obtener JWKS de Clerk: {e}")
        return None


def verify_clerk_token(token: str) -> Optional[dict]:
    """
    Verifica y decodifica un token JWT de Clerk.
    
    Args:
        token: JWT token de Clerk
        
    Returns:
        Dict con los claims del token o None si es inválido
    """
    try:
        # Obtener JWKS
        jwks = get_clerk_jwks()
        if not jwks:
            return None
        
        # Decodificar sin verificar primero para obtener el header
        unverified_header = jwt.get_unverified_header(token)
        
        # Encontrar la clave correcta en JWKS
        rsa_key = None
        for key in jwks.get("keys", []):
            if key["kid"] == unverified_header["kid"]:
                rsa_key = {
                    "kty": key["kty"],
                    "kid": key["kid"],
                    "use": key["use"],
                    "n": key["n"],
                    "e": key["e"]
                }
                break
        
        if not rsa_key:
            print("⚠️ No se encontró clave pública para el token")
            return None
        
        # Verificar y decodificar el token
        payload = jwt.decode(
            token,
            rsa_key,
            algorithms=["RS256"],
            options={
                "verify_signature": True,
                "verify_aud": False,  # Clerk no usa audience
                "verify_iss": True,
            }
        )
        
        return payload
        
    except JWTError as e:
        print(f"⚠️ Error al verificar token: {e}")
        return None
    except Exception as e:
        print(f"❌ Error inesperado: {e}")
        return None


async def get_current_user(
    credentials: Optional[HTTPAuthorizationCredentials] = Security(security)
) -> Optional[ClerkUser]:
    """
    Obtiene el usuario actual desde el token JWT de Clerk.
    
    Args:
        credentials: Credenciales HTTP Bearer
        
    Returns:
        ClerkUser si el token es válido, None en caso contrario
    """
    if not credentials:
        return None
    
    token = credentials.credentials
    
    # Verificar token
    payload = verify_clerk_token(token)
    
    if not payload:
        return None
    
    # Extraer información del usuario
    user_id = payload.get("sub")  # Subject (user_id)
    email = payload.get("email")
    first_name = payload.get("given_name")
    last_name = payload.get("family_name")
    
    if not user_id:
        return None
    
    return ClerkUser(
        user_id=user_id,
        email=email,
        first_name=first_name,
        last_name=last_name
    )


async def require_auth(
    user: Optional[ClerkUser] = Depends(get_current_user)
) -> ClerkUser:
    """
    Requiere autenticación. Lanza HTTPException si no está autenticado.
    
    Args:
        user: Usuario actual (inyectado por dependencia)
        
    Returns:
        ClerkUser autenticado
        
    Raises:
        HTTPException: Si el usuario no está autenticado
    """
    if not user:
        raise HTTPException(
            status_code=401,
            detail="No autenticado. Token JWT requerido.",
            headers={"WWW-Authenticate": "Bearer"},
        )
    
    return user


async def optional_auth(
    user: Optional[ClerkUser] = Depends(get_current_user)
) -> Optional[ClerkUser]:
    """
    Autenticación opcional. No lanza error si no está autenticado.
    
    Args:
        user: Usuario actual (inyectado por dependencia)
        
    Returns:
        ClerkUser si está autenticado, None en caso contrario
    """
    return user


# Función helper para obtener session_id desde usuario
def get_session_id_from_user(user: Optional[ClerkUser], 
                             fallback_session_id: Optional[str] = None) -> Optional[str]:
    """
    Obtiene el session_id apropiado.
    
    Prioridad:
    1. user_id de Clerk si el usuario está autenticado
    2. fallback_session_id si se proporciona
    3. None (sin sesión)
    
    Args:
        user: Usuario autenticado de Clerk
        fallback_session_id: Session ID de respaldo
        
    Returns:
        Session ID apropiado o None
    """
    if user:
        return user.user_id
    return fallback_session_id


# Función para agregar metadata de usuario a MongoDB
def get_user_metadata(user: Optional[ClerkUser]) -> dict:
    """
    Obtiene metadata del usuario para almacenar en MongoDB.
    
    Args:
        user: Usuario autenticado
        
    Returns:
        Dict con metadata del usuario
    """
    if not user:
        return {}
    
    return {
        "user_id": user.user_id,
        "email": user.email,
        "full_name": user.full_name,
        "authenticated": True
    }
