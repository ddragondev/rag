# 🛠️ Solución de Problemas - Deployment Ubuntu

## ❌ Error: ModuleNotFoundError: No module named 'langchain.text_splitter'

### Problema:

El script `reindex_documents.py` usa imports obsoletos de LangChain.

### Solución:

```bash
# 1. Editar el archivo reindex_documents.py
nano reindex_documents.py

# 2. Cambiar la línea 7:
# DE:   from langchain.text_splitter import RecursiveCharacterTextSplitter
# A:    from langchain_text_splitters import RecursiveCharacterTextSplitter

# 3. Cambiar la línea 8:
# DE:   from langchain_community.vectorstores import Chroma
# A:    from langchain_chroma import Chroma
```

### Script de Corrección Automática:

```bash
cd /var/www/rag
sed -i 's/from langchain.text_splitter import/from langchain_text_splitters import/' reindex_documents.py
sed -i 's/from langchain_community.vectorstores import Chroma/from langchain_chroma import Chroma/' reindex_documents.py
```

---

## ❌ Error: ls: cannot access 'chroma_db/': No such file or directory

### Problema:

La base de datos vectorial no se ha creado aún.

### Solución:

```bash
# El directorio se creará automáticamente cuando ejecutes:
python reindex_documents.py
```

---

## ⚠️ Problema: Ejecutando como root

### Problema:

Estás ejecutando como `root@localhost`, lo cual no es seguro.

### Solución Recomendada:

```bash
# 1. Crear usuario dedicado
sudo useradd -m -s /bin/bash ragapp
sudo usermod -aG sudo ragapp

# 2. Cambiar propiedad del directorio
sudo chown -R ragapp:ragapp /var/www/rag

# 3. Cambiar a usuario ragapp
sudo su - ragapp
cd /var/www/rag
```

### Solución Rápida (mantener root):

```bash
# Si prefieres seguir como root:
cd /var/www/rag
source venv/bin/activate

# Verificar dependencias
pip list | grep langchain

# Si faltan dependencias:
pip install langchain-text-splitters langchain-chroma
```

---

## 🔧 Pasos de Solución Completa

### Paso 1: Corregir Imports

```bash
cd /var/www/rag

# Opción A: Usar sed (automático)
sed -i 's/from langchain.text_splitter import/from langchain_text_splitters import/' reindex_documents.py
sed -i 's/from langchain_community.vectorstores import Chroma/from langchain_chroma import Chroma/' reindex_documents.py

# Opción B: Editar manualmente
nano reindex_documents.py
# Cambiar las líneas como se indica arriba
```

### Paso 2: Verificar Dependencias

```bash
source venv/bin/activate

# Verificar qué tienes instalado
pip list | grep langchain

# Instalar dependencias faltantes
pip install langchain-text-splitters langchain-chroma chromadb

# O reinstalar todo desde requirements.txt
pip install -r requirements.txt
```

### Paso 3: Verificar Estructura de Archivos

```bash
# Verificar que tienes los documentos
ls -la docs/
ls -la docs/geomecanica/
ls -la docs/compliance/

# Si no existen, crearlos
mkdir -p docs/geomecanica docs/compliance videos/geomecanica
```

### Paso 4: Transferir Archivos (si faltan documentos)

```bash
# Desde tu Mac, transferir los PDFs:
scp -r /Users/ddragondev/Documents/OpenAI-PDF-RAG-LangChain-master/docs/* root@tu-servidor:/var/www/rag/docs/
scp -r /Users/ddragondev/Documents/OpenAI-PDF-RAG-LangChain-master/videos/* root@tu-servidor:/var/www/rag/videos/
```

### Paso 5: Verificar .env

```bash
# Verificar que existe .env con tu API key
cat .env

# Si no existe, crearlo:
echo "OPENAI_API_KEY=tu-api-key-aqui" > .env
echo "ENVIRONMENT=production" >> .env
echo "PORT=8000" >> .env
echo "HOST=0.0.0.0" >> .env
```

### Paso 6: Ejecutar Re-indexación

```bash
source venv/bin/activate
python reindex_documents.py
```

### Paso 7: Verificar Resultado

```bash
# Debería crear el directorio chroma_db
ls -la chroma_db/

# Debería mostrar las colecciones
ls -la chroma_db/*/
```

---

## 🧪 Verificación Completa

### Comprobar que Todo Funciona:

```bash
# 1. Verificar servicio
python main.py  # Debería iniciar sin errores

# 2. En otra terminal, probar API
curl http://localhost:8000/

# 3. Probar consulta
curl -X POST "http://localhost:8000/ask" \
  -H "Content-Type: application/json" \
  -d '{
    "question": "que es compliance?",
    "category": "compliance",
    "format": "plain"
  }'
```

---

## 📋 Checklist de Solución

- [ ] ✅ Corregir imports en `reindex_documents.py`
- [ ] ✅ Instalar dependencias faltantes: `langchain-text-splitters`, `langchain-chroma`
- [ ] ✅ Verificar que existe `.env` con `OPENAI_API_KEY`
- [ ] ✅ Verificar que existen directorios `docs/geomecanica` y `docs/compliance`
- [ ] ✅ Transferir PDFs si faltan
- [ ] ✅ Ejecutar `python reindex_documents.py`
- [ ] ✅ Verificar que se creó `chroma_db/`
- [ ] ✅ Probar que la API funciona

---

## 🚀 Una Vez Solucionado

### Configurar Servicio Systemd:

```bash
# Solo después de que todo funcione manualmente
sudo nano /etc/systemd/system/pdf-rag.service

# Contenido (ajustar rutas):
[Unit]
Description=PDF RAG API Service
After=network.target

[Service]
Type=simple
User=ragapp  # o root si prefieres mantenerlo
Group=ragapp # o root
WorkingDirectory=/var/www/rag
Environment=PATH=/var/www/rag/venv/bin
ExecStart=/var/www/rag/venv/bin/uvicorn main:app --host 0.0.0.0 --port 8000
Restart=always
RestartSec=3

[Install]
WantedBy=multi-user.target
```

### Iniciar Servicio:

```bash
sudo systemctl daemon-reload
sudo systemctl enable pdf-rag
sudo systemctl start pdf-rag
sudo systemctl status pdf-rag
```

---

## 📞 Comandos de Emergencia

### Si nada funciona, empezar de cero:

```bash
# 1. Eliminar todo
rm -rf /var/www/rag

# 2. Re-transferir archivos corregidos desde tu Mac
scp -r /Users/ddragondev/Documents/OpenAI-PDF-RAG-LangChain-master /var/www/rag

# 3. Seguir guía de deployment desde Paso 4
```

### Logs útiles:

```bash
# Ver qué está pasando
sudo journalctl -u pdf-rag -f

# Ver errores de Python
python main.py  # Ejecutar manualmente para ver errores
```

---

¡Ejecuta estos pasos y el sistema debería funcionar! 🚀
