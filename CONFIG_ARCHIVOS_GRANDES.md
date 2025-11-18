# 📦 Configuración para Archivos Grandes

## 🎯 Límites Actuales

### Desarrollo (FastAPI directo):

- **Límite configurado:** 100 MB
- **Middleware:** `LimitUploadSizeMiddleware` valida el header `content-length`
- **Validación adicional:** El endpoint verifica el tamaño después de leer el archivo
- **Error 413:** Se rechaza ANTES de procesar si excede el límite
- **Mensaje:** "Request too large (X MB). Maximum allowed: 100 MB"

---

## 🚨 Solución Error 413 en Local

Si obtienes error **413 Content Too Large** en desarrollo local:

### ✅ Ya está solucionado con el middleware

El código ahora incluye `LimitUploadSizeMiddleware` que:
1. Intercepta requests a `/upload`
2. Lee el header `content-length`
3. Rechaza archivos grandes ANTES de procesarlos
4. Retorna error 413 con mensaje claro

**No necesitas configurar nada adicional en local.**

---

## 🚀 Configuración en Producción

Si estás usando **nginx** como proxy reverso, necesitas configurar el límite también en nginx.

### 1. Configuración de nginx

Edita tu archivo de configuración de nginx:

```bash
sudo nano /etc/nginx/sites-available/tu-app
```

Agrega o modifica esta línea dentro del bloque `server`:

```nginx
server {
    listen 80;
    server_name tu-dominio.com;

    # Aumentar límite de subida a 100 MB
    client_max_body_size 100M;

    location / {
        proxy_pass http://127.0.0.1:8000;
        proxy_set_header Host $host;
        proxy_set_header X-Real-IP $remote_addr;
        proxy_set_header X-Forwarded-For $proxy_add_x_forwarded_for;
        proxy_set_header X-Forwarded-Proto $scheme;

        # Aumentar timeout para archivos grandes
        proxy_read_timeout 300;
        proxy_connect_timeout 300;
        proxy_send_timeout 300;
    }
}
```

### 2. Reiniciar nginx

```bash
sudo nginx -t  # Verificar configuración
sudo systemctl restart nginx
```

---

## 🔧 Aumentar el Límite

Si necesitas archivos **más grandes que 100 MB**, modifica:

### En main.py:

```python
# Cambiar línea 42-43
MAX_FILE_SIZE = 200 * 1024 * 1024  # 200 MB (ejemplo)
MAX_FILE_SIZE_MB = MAX_FILE_SIZE / (1024 * 1024)
```

### En nginx (si usas):

```nginx
client_max_body_size 200M;
```

---

## ⚡ Optimizaciones para Archivos Grandes

### 1. Streaming Upload (próximamente)

Para archivos muy grandes, considera implementar upload por chunks:

```python
@app.post("/categories/{category_name}/upload-chunked")
async def upload_file_chunked(
    category_name: str,
    chunk: UploadFile = File(...),
    chunk_number: int = 0,
    total_chunks: int = 1,
    file_id: str = ""
):
    """Sube un archivo en chunks para archivos muy grandes."""
    # Implementación de chunks
    pass
```

### 2. Compresión antes de subir

En el frontend, considera comprimir PDFs antes de subirlos:

```javascript
// Usando pdf-lib para optimizar PDFs
import { PDFDocument } from "pdf-lib";

async function optimizePDF(file) {
  const arrayBuffer = await file.arrayBuffer();
  const pdfDoc = await PDFDocument.load(arrayBuffer);
  const pdfBytes = await pdfDoc.save({ useObjectStreams: false });
  return new File([pdfBytes], file.name, { type: "application/pdf" });
}
```

### 3. Validación en el frontend

Valida el tamaño antes de enviar:

```javascript
const MAX_FILE_SIZE = 100 * 1024 * 1024; // 100 MB

function validateFile(file) {
  if (file.size > MAX_FILE_SIZE) {
    alert(
      `Archivo demasiado grande (${(file.size / 1024 / 1024).toFixed(
        2
      )} MB). Máximo: 100 MB`
    );
    return false;
  }
  return true;
}
```

---

## 📊 Monitoreo

### Ver tamaño de archivos subidos:

```bash
# Ver tamaño de todos los PDFs
find docs/ -name "*.pdf" -exec ls -lh {} \; | awk '{print $5, $9}'

# Ver archivos mayores a 50 MB
find docs/ -name "*.pdf" -size +50M -exec ls -lh {} \;
```

### Logs del servidor:

El servidor registra el tamaño de cada archivo subido:

```
✅ File uploaded successfully: 45.67 MB
❌ File too large: 120.50 MB (max: 100 MB)
```

---

## 🚨 Problemas Comunes

### Error: "413 Request Entity Too Large"

**Causa:** nginx tiene un límite menor al configurado en FastAPI.

**Solución:** Aumenta `client_max_body_size` en nginx y reinicia.

---

### Error: "504 Gateway Timeout"

**Causa:** El archivo es tan grande que nginx cierra la conexión antes de completar la subida.

**Solución:** Aumenta los timeouts en nginx:

```nginx
proxy_read_timeout 600;
proxy_connect_timeout 600;
proxy_send_timeout 600;
```

---

### Error: Archivo se sube pero no se indexa

**Causa:** ChromaDB puede tardar mucho en indexar PDFs muy grandes.

**Solución:** Considera dividir PDFs grandes en secciones más pequeñas, o aumenta el timeout del endpoint `/reindex`.

---

## 📝 Notas Importantes

1. **Memoria del servidor:** Archivos grandes consumen memoria RAM durante el procesamiento
2. **ChromaDB:** La indexación de PDFs grandes puede tardar varios minutos
3. **OpenAI Embeddings:** Hay límites de tokens por minuto (TPM) en tu cuenta de OpenAI
4. **Costos:** PDFs más grandes = más tokens = más costo en embeddings

---

## 🎯 Recomendaciones

| Tamaño PDF | Recomendación                       |
| ---------- | ----------------------------------- |
| < 10 MB    | ✅ Perfecto, no hay problema        |
| 10-50 MB   | ⚠️ OK, pero tarda en indexar        |
| 50-100 MB  | ⚠️ Funciona, pero considera dividir |
| > 100 MB   | 🚫 Divide en archivos más pequeños  |

---

**Fecha de actualización:** 18 de noviembre de 2025  
**Estado:** ✅ Funcional con límite de 100 MB
