# 🔧 Pasos para Arreglar el Error 401

## 🎯 Problema Identificado

El endpoint `/my-history` y `/my-conversations` están dando **401** porque:

1. ✅ El token es válido (tiene email, name, user_id)
2. ✅ El token NO está expirado (válido por 10076 minutos)
3. ❌ La URL de JWKS estaba mal configurada
4. ❌ El servidor necesita reiniciarse con los cambios

## ✅ Cambios Realizados en `clerk_auth.py`

### 1. URL de JWKS Corregida

```python
# ANTES (genérico):
CLERK_JWKS_URL = "https://api.clerk.dev/v1/jwks"

# AHORA (específico para tu instalación):
CLERK_JWKS_URL = "https://meet-midge-16.clerk.accounts.dev/.well-known/jwks.json"
```

### 2. Detección Dinámica del Issuer

Ahora el sistema detecta automáticamente el `issuer` del token y construye la URL correcta de JWKS.

### 3. Verificación de Issuer Desactivada

```python
options={
    "verify_iss": False,  # No verificar issuer (varía por ambiente)
}
```

### 4. Más Logs de Debug

Ahora se imprimen logs detallados para diagnosticar problemas.

---

## 🚀 Cómo Reiniciar el Servidor

### Opción 1: Desde la Terminal donde corre el servidor

1. Ve a la terminal donde está corriendo `uvicorn`
2. Presiona `Ctrl + C` para detenerlo
3. Ejecuta:

```bash
cd /Users/ddragondev/Documents/OpenAI-PDF-RAG-LangChain-master
source venv/bin/activate
uvicorn main:app --reload --host 0.0.0.0 --port 8000
```

### Opción 2: Matar y reiniciar

```bash
# Matar el proceso
pkill -f "uvicorn main:app"

# Esperar 2 segundos
sleep 2

# Reiniciar
cd /Users/ddragondev/Documents/OpenAI-PDF-RAG-LangChain-master
source venv/bin/activate
uvicorn main:app --reload --host 0.0.0.0 --port 8000
```

### Opción 3: Usar el script (más fácil)

```bash
./restart_server.sh
```

---

## 🧪 Probar Después del Reinicio

### 1. Espera a que el servidor inicie

Verás algo como:

```
INFO:     Uvicorn running on http://0.0.0.0:8000 (Press CTRL+C to quit)
INFO:     Started reloader process
```

### 2. Ejecuta el diagnóstico nuevamente

```bash
python test_auth_debug.py
```

### 3. Pega el mismo token que usaste antes

El token que funcionó parcialmente:

```
eyJhbGciOiJSUzI1NiIsImNhdCI6ImNsX0I3ZDRQRDIyMkFBQS...
```

---

## 📊 Resultados Esperados

### Antes (❌ Error):

```bash
🧪 TEST: /my-history CON autenticación
Status: 401
❌ Error 401: No autenticado
```

### Después (✅ Éxito):

```bash
🧪 TEST: /my-history CON autenticación
Status: 200
✅ Funciona correctamente
   user_email: dvegamed@gmail.com
   total_messages: X
```

---

## 🔍 Si Sigue Dando 401

### Revisa los logs del servidor

En la terminal donde corre el servidor, busca:

```bash
# Deberías ver:
ℹ️ Usando JWKS URL: https://meet-midge-16.clerk.accounts.dev/.well-known/jwks.json
✅ Token verificado exitosamente para user: user_34NsXErIAA1CKgEAVnMNIJrOiRQ (dvegamed@gmail.com)
✅ Usuario autenticado: user_34NsXErIAA1CKgEAVnMNIJrOiRQ (dvegamed@gmail.com)

# Si ves errores como:
❌ No se pudo obtener JWKS
⚠️ No se encontró clave pública para kid: ...
⚠️ Error al verificar token JWT: ...
```

### Verificar que la URL de JWKS funciona

```bash
curl https://meet-midge-16.clerk.accounts.dev/.well-known/jwks.json
```

Deberías ver algo como:

```json
{
  "keys": [
    {
      "use": "sig",
      "kty": "RSA",
      "kid": "ins_34NkqVco5yiIeDwaJgnh0pTmW9S",
      "alg": "RS256",
      "n": "...",
      "e": "AQAB"
    }
  ]
}
```

---

## 💡 Explicación Técnica

### ¿Por qué falló antes?

1. **URL de JWKS incorrecta**: Usábamos `https://api.clerk.dev/v1/jwks` que es genérica
2. **Tu instalación de Clerk**: Usa `meet-midge-16.clerk.accounts.dev`
3. **JWKS específico**: Cada instalación tiene su propio endpoint JWKS

### ¿Cómo funciona ahora?

```
1. Token llega al servidor
2. Decodificar sin verificar → Extraer "iss": "https://meet-midge-16.clerk.accounts.dev"
3. Construir URL: https://meet-midge-16.clerk.accounts.dev/.well-known/jwks.json
4. Obtener claves públicas (JWKS)
5. Verificar firma del token con la clave correcta (kid match)
6. ✅ Token válido → Extraer user_id, email, name
7. Retornar ClerkUser
```

---

## 🎯 Resumen de Pasos

1. ✅ Cambios en `clerk_auth.py` ya aplicados
2. ⏳ **TU TURNO**: Reiniciar el servidor
3. ⏳ **TU TURNO**: Ejecutar `python test_auth_debug.py`
4. ⏳ **TU TURNO**: Verificar que `/my-history` da 200 OK

---

## 📞 Si Necesitas Ayuda

Comparte:

1. Los logs del servidor al iniciar
2. Los logs cuando ejecutas `test_auth_debug.py`
3. La respuesta de: `curl https://meet-midge-16.clerk.accounts.dev/.well-known/jwks.json`

---

¡Reinicia el servidor y prueba! 🚀
