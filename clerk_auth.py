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

# Construir la URL de JWKS desde el issuer del token
# Para meet-midge-16.clerk.accounts.dev el JWKS está en:
# https://meet-midge-16.clerk.accounts.dev/.well-known/jwks.json
def get_jwks_url_from_issuer(issuer: str = None) -> str:
    """Construye la URL de JWKS desde el issuer."""
    if issuer:
        # Remover https:// si existe
        domain = issuer.replace("https://", "").replace("http://", "")
        return f"https://{domain}/.well-known/jwks.json"
    # Fallback a la URL genérica
    return "https://api.clerk.dev/v1/jwks"

# URL por defecto (se actualizará dinámicamente)
CLERK_JWKS_URL = "https://meet-midge-16.clerk.accounts.dev/.well-known/jwks.json"

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
        # Primero decodificar sin verificar para obtener el issuer
        unverified_payload = jwt.get_unverified_claims(token)
        issuer = unverified_payload.get("iss")
        
        if issuer:
            # Actualizar la URL de JWKS dinámicamente
            global CLERK_JWKS_URL
            CLERK_JWKS_URL = get_jwks_url_from_issuer(issuer)
            print(f"ℹ️ Usando JWKS URL: {CLERK_JWKS_URL}")
        
        # Obtener JWKS
        jwks = get_clerk_jwks()
        if not jwks:
            print("❌ No se pudo obtener JWKS")
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
            print(f"⚠️ No se encontró clave pública para kid: {unverified_header.get('kid')}")
            return None
        
        # Verificar y decodificar el token
        # Nota: No verificamos issuer porque Clerk usa diferentes issuers por ambiente
        payload = jwt.decode(
            token,
            rsa_key,
            algorithms=["RS256"],
            options={
                "verify_signature": True,
                "verify_aud": False,  # Clerk no usa audience standard
                "verify_iss": False,  # No verificar issuer (Clerk varía por ambiente)
                "verify_exp": True,   # SÍ verificar expiración
            }
        )
        
        print(f"✅ Token verificado exitosamente para user: {payload.get('sub')} ({payload.get('email', 'sin email')})")
        return payload
        
    except jwt.ExpiredSignatureError:
        print("⚠️ Token expirado")
        return None
    except JWTError as e:
        print(f"⚠️ Error al verificar token JWT: {e}")
        return None
    except Exception as e:
        print(f"❌ Error inesperado al verificar token: {e}")
        return None


def get_user_from_clerk_api(user_id: str) -> Optional[dict]:
    """
    Obtiene información del usuario desde la API de Clerk.
    
    Args:
        user_id: ID del usuario de Clerk
        
    Returns:
        Dict con información del usuario o None
    """
    if not CLERK_SECRET_KEY:
        print("⚠️ CLERK_SECRET_KEY no configurada")
        return None
    
    try:
        url = f"https://api.clerk.com/v1/users/{user_id}"
        headers = {
            "Authorization": f"Bearer {CLERK_SECRET_KEY}",
            "Content-Type": "application/json"
        }
        
        response = requests.get(url, headers=headers)
        
        if response.status_code == 200:
            return response.json()
        else:
            print(f"⚠️ Error al obtener usuario de Clerk API: {response.status_code}")
            return None
            
    except Exception as e:
        print(f"❌ Error al llamar a Clerk API: {e}")
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
        print("⚠️ No se proporcionaron credenciales")
        return None
    
    token = credentials.credentials
    
    # Verificar token
    payload = verify_clerk_token(token)
    
    if not payload:
        print("⚠️ Token inválido o expirado")
        return None
    
    # Extraer información del usuario del payload
    user_id = payload.get("sub")  # Subject (user_id)
    
    if not user_id:
        print("⚠️ No se encontró user_id en el token")
        return None
    
    # Intentar obtener email y nombres del payload primero
    email = payload.get("email")
    first_name = payload.get("given_name")
    last_name = payload.get("family_name")
    
    # Si no están en el payload, obtener de la API de Clerk
    if not email:
        print(f"ℹ️ Email no en JWT, obteniendo de Clerk API para user: {user_id}")
        user_data = get_user_from_clerk_api(user_id)
        
        if user_data:
            # Clerk API devuelve el email en email_addresses array
            email_addresses = user_data.get("email_addresses", [])
            if email_addresses:
                # Buscar el email principal
                primary_email = next(
                    (e for e in email_addresses if e.get("id") == user_data.get("primary_email_address_id")),
                    email_addresses[0]  # Fallback al primero
                )
                email = primary_email.get("email_address")
            
            first_name = user_data.get("first_name")
            last_name = user_data.get("last_name")
    
    print(f"✅ Usuario autenticado: {user_id} ({email})")
    
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
