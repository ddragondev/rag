# 🚀 Guía de Deployment en Ubuntu

## 📋 Requisitos del Servidor

### Hardware Mínimo
- **RAM**: 4GB (recomendado 8GB)
- **CPU**: 2 cores (recomendado 4 cores)
- **Almacenamiento**: 10GB libres (para documentos y base de datos vectorial)
- **Conexión**: Internet estable para API de OpenAI

### Software
- **Ubuntu**: 20.04 LTS o superior
- **Python**: 3.9+ (recomendado 3.11)
- **Acceso**: SSH o acceso directo al servidor

---

## 🛠️ Instalación Paso a Paso

### Paso 1: Actualizar el Sistema
```bash
# Conectar al servidor
ssh usuario@tu-servidor-ubuntu

# Actualizar paquetes
sudo apt update && sudo apt upgrade -y

# Instalar dependencias básicas
sudo apt install -y python3 python3-pip python3-venv git curl nginx supervisor
```

### Paso 2: Crear Usuario para la Aplicación
```bash
# Crear usuario específico para la app (más seguro)
sudo useradd -m -s /bin/bash ragapp
sudo usermod -aG sudo ragapp

# Cambiar a usuario ragapp
sudo su - ragapp
```

### Paso 3: Clonar/Transferir el Proyecto
```bash
# Opción A: Si tienes Git
git clone https://github.com/tu-usuario/tu-repo.git pdf-rag
cd pdf-rag

# Opción B: Transferir archivos desde tu Mac
# En tu Mac:
scp -r /Users/ddragondev/Documents/OpenAI-PDF-RAG-LangChain-master ragapp@tu-servidor:/home/ragapp/pdf-rag

# En Ubuntu:
cd /home/ragapp/pdf-rag
```

### Paso 4: Configurar Entorno Virtual
```bash
# Crear entorno virtual
python3 -m venv venv

# Activar entorno
source venv/bin/activate

# Actualizar pip
pip install --upgrade pip

# Instalar dependencias
pip install fastapi uvicorn python-dotenv
pip install langchain langchain-community langchain-openai
pip install langchain-chroma chromadb
pip install langchain-text-splitters
pip install pypdf unstructured[pdf]
```

### Paso 5: Configurar Variables de Entorno
```bash
# Crear archivo .env
nano .env

# Contenido del archivo .env:
OPENAI_API_KEY=tu-api-key-aqui
ENVIRONMENT=production
PORT=8000
HOST=0.0.0.0
```

### Paso 6: Transferir Documentos
```bash
# Crear estructura de carpetas
mkdir -p docs/geomecanica docs/compliance videos/geomecanica

# Transferir documentos desde tu Mac
# En tu Mac:
scp -r /Users/ddragondev/Documents/OpenAI-PDF-RAG-LangChain-master/docs/* ragapp@tu-servidor:/home/ragapp/pdf-rag/docs/
scp -r /Users/ddragondev/Documents/OpenAI-PDF-RAG-LangChain-master/videos/* ragapp@tu-servidor:/home/ragapp/pdf-rag/videos/
```

### Paso 7: Indexar Documentos
```bash
# Activar entorno virtual
source venv/bin/activate

# Ejecutar re-indexación
python reindex_documents.py

# Verificar que funcionó
ls -la chroma_db/
```

---

## 🔧 Configuración del Servicio

### Paso 8: Crear Servicio Systemd
```bash
# Crear archivo de servicio
sudo nano /etc/systemd/system/pdf-rag.service
```

**Contenido del archivo:**
```ini
[Unit]
Description=PDF RAG API Service
After=network.target

[Service]
Type=simple
User=ragapp
Group=ragapp
WorkingDirectory=/home/ragapp/pdf-rag
Environment=PATH=/home/ragapp/pdf-rag/venv/bin
ExecStart=/home/ragapp/pdf-rag/venv/bin/uvicorn main:app --host 0.0.0.0 --port 8000
Restart=always
RestartSec=3

[Install]
WantedBy=multi-user.target
```

### Paso 9: Habilitar y Iniciar Servicio
```bash
# Recargar systemd
sudo systemctl daemon-reload

# Habilitar servicio
sudo systemctl enable pdf-rag

# Iniciar servicio
sudo systemctl start pdf-rag

# Verificar estado
sudo systemctl status pdf-rag

# Ver logs en tiempo real
sudo journalctl -u pdf-rag -f
```

---

## 🌐 Configuración de Nginx (Proxy Inverso)

### Paso 10: Configurar Nginx
```bash
# Crear configuración de sitio
sudo nano /etc/nginx/sites-available/pdf-rag
```

**Contenido del archivo:**
```nginx
server {
    listen 80;
    server_name tu-dominio.com;  # Cambiar por tu dominio o IP

    location / {
        proxy_pass http://127.0.0.1:8000;
        proxy_set_header Host $host;
        proxy_set_header X-Real-IP $remote_addr;
        proxy_set_header X-Forwarded-For $proxy_add_x_forwarded_for;
        proxy_set_header X-Forwarded-Proto $scheme;
        
        # Timeouts para respuestas largas
        proxy_read_timeout 300;
        proxy_connect_timeout 300;
        proxy_send_timeout 300;
    }
}
```

### Paso 11: Activar Sitio
```bash
# Habilitar sitio
sudo ln -s /etc/nginx/sites-available/pdf-rag /etc/nginx/sites-enabled/

# Verificar configuración
sudo nginx -t

# Reiniciar nginx
sudo systemctl restart nginx

# Habilitar nginx en boot
sudo systemctl enable nginx
```

---

## 🔒 Configuración de Firewall

### Paso 12: Configurar UFW
```bash
# Habilitar firewall
sudo ufw enable

# Permitir SSH
sudo ufw allow ssh

# Permitir HTTP y HTTPS
sudo ufw allow 80
sudo ufw allow 443

# Verificar reglas
sudo ufw status
```

---

## 🛡️ SSL/HTTPS con Let's Encrypt (Opcional pero Recomendado)

### Paso 13: Configurar HTTPS
```bash
# Instalar certbot
sudo apt install -y certbot python3-certbot-nginx

# Obtener certificado SSL
sudo certbot --nginx -d tu-dominio.com

# Verificar renovación automática
sudo certbot renew --dry-run
```

---

## 📊 Monitoreo y Logs

### Comandos Útiles de Administración

```bash
# Ver estado del servicio
sudo systemctl status pdf-rag

# Reiniciar servicio
sudo systemctl restart pdf-rag

# Ver logs en tiempo real
sudo journalctl -u pdf-rag -f

# Ver logs de nginx
sudo tail -f /var/log/nginx/access.log
sudo tail -f /var/log/nginx/error.log

# Ver uso de recursos
htop
df -h
free -h
```

### Configurar Logrotate
```bash
# Crear configuración de rotación de logs
sudo nano /etc/logrotate.d/pdf-rag
```

**Contenido:**
```
/var/log/pdf-rag/*.log {
    daily
    missingok
    rotate 30
    compress
    notifempty
    create 644 ragapp ragapp
}
```

---

## 🧪 Verificación del Deployment

### Paso 14: Probar la API

```bash
# Desde el servidor
curl http://localhost:8000/

# Desde internet (cambiar IP)
curl http://tu-servidor-ip/

# Probar consulta
curl -X POST "http://tu-servidor-ip/ask" \
  -H "Content-Type: application/json" \
  -d '{
    "question": "que es compliance?",
    "category": "compliance", 
    "format": "plain"
  }'
```

### Verificar Endpoints
```bash
# Info de la API
curl http://tu-servidor-ip/

# Lista categorías
curl http://tu-servidor-ip/categories

# Stats del caché
curl http://tu-servidor-ip/cache/stats

# Lista videos
curl http://tu-servidor-ip/videos/geomecanica
```

---

## 🚀 Optimizaciones de Producción

### Configuración de Uvicorn para Producción
```bash
# Editar archivo de servicio para múltiples workers
sudo nano /etc/systemd/system/pdf-rag.service
```

**Cambiar ExecStart a:**
```ini
ExecStart=/home/ragapp/pdf-rag/venv/bin/uvicorn main:app --host 0.0.0.0 --port 8000 --workers 4 --worker-class uvicorn.workers.UvicornWorker
```

### Configuración de Límites de Sistema
```bash
# Editar límites del sistema
sudo nano /etc/security/limits.conf

# Agregar al final:
ragapp soft nofile 65536
ragapp hard nofile 65536
ragapp soft nproc 32768
ragapp hard nproc 32768
```

### Configuración de Memoria Swap (si es necesario)
```bash
# Crear archivo swap de 2GB
sudo fallocate -l 2G /swapfile
sudo chmod 600 /swapfile
sudo mkswap /swapfile
sudo swapon /swapfile

# Hacer permanente
echo '/swapfile none swap sw 0 0' | sudo tee -a /etc/fstab
```

---

## 📱 Automatización de Backups

### Script de Backup
```bash
# Crear script de backup
nano /home/ragapp/backup_rag.sh
```

**Contenido del script:**
```bash
#!/bin/bash
BACKUP_DIR="/home/ragapp/backups"
DATE=$(date +%Y%m%d_%H%M%S)

# Crear directorio de backup
mkdir -p $BACKUP_DIR

# Backup de base de datos vectorial
tar -czf $BACKUP_DIR/chroma_db_$DATE.tar.gz -C /home/ragapp/pdf-rag chroma_db/

# Backup de documentos
tar -czf $BACKUP_DIR/docs_$DATE.tar.gz -C /home/ragapp/pdf-rag docs/

# Backup de configuración
cp /home/ragapp/pdf-rag/.env $BACKUP_DIR/env_$DATE.backup

# Limpiar backups antiguos (más de 7 días)
find $BACKUP_DIR -name "*.tar.gz" -mtime +7 -delete
find $BACKUP_DIR -name "*.backup" -mtime +7 -delete

echo "Backup completado: $DATE"
```

```bash
# Hacer ejecutable
chmod +x /home/ragapp/backup_rag.sh

# Agregar a crontab (backup diario a las 2 AM)
crontab -e

# Agregar línea:
0 2 * * * /home/ragapp/backup_rag.sh >> /home/ragapp/backup.log 2>&1
```

---

## 🔧 Mantenimiento

### Actualizar el Sistema
```bash
# Detener servicio
sudo systemctl stop pdf-rag

# Actualizar código
cd /home/ragapp/pdf-rag
git pull  # o transferir archivos nuevos

# Activar entorno
source venv/bin/activate

# Actualizar dependencias si es necesario
pip install -r requirements.txt

# Re-indexar si agregaste documentos
python reindex_documents.py

# Reiniciar servicio
sudo systemctl start pdf-rag
```

### Agregar Nuevos Documentos
```bash
# Transferir nuevos PDFs
scp nuevo-documento.pdf ragapp@tu-servidor:/home/ragapp/pdf-rag/docs/compliance/

# Re-indexar
cd /home/ragapp/pdf-rag
source venv/bin/activate
python reindex_documents.py

# El servicio automáticamente usará los nuevos documentos
```

---

## ⚠️ Solución de Problemas

### Servicio no inicia
```bash
# Ver logs detallados
sudo journalctl -u pdf-rag -n 50

# Verificar permisos
ls -la /home/ragapp/pdf-rag/
sudo chown -R ragapp:ragapp /home/ragapp/pdf-rag/

# Verificar entorno virtual
source /home/ragapp/pdf-rag/venv/bin/activate
python -c "import fastapi; print('FastAPI OK')"
```

### Error de conexión a OpenAI
```bash
# Verificar API key
cat /home/ragapp/pdf-rag/.env

# Probar conexión
source /home/ragapp/pdf-rag/venv/bin/activate
python -c "
import openai
import os
from dotenv import load_dotenv
load_dotenv()
client = openai.OpenAI(api_key=os.getenv('OPENAI_API_KEY'))
response = client.models.list()
print('OpenAI connection OK')
"
```

### Nginx no funciona
```bash
# Verificar configuración
sudo nginx -t

# Ver logs de nginx
sudo tail -f /var/log/nginx/error.log

# Reiniciar nginx
sudo systemctl restart nginx
```

### Base de datos corrupta
```bash
# Re-crear base de datos
cd /home/ragapp/pdf-rag
source venv/bin/activate
rm -rf chroma_db/
python reindex_documents.py
```

---

## 📈 Monitoreo de Performance

### Instalar htop y iotop
```bash
sudo apt install -y htop iotop

# Monitorear CPU y RAM
htop

# Monitorear I/O
sudo iotop
```

### Script de Monitoreo Básico
```bash
# Crear script de monitoreo
nano /home/ragapp/monitor_rag.sh
```

**Contenido:**
```bash
#!/bin/bash
echo "=== PDF RAG System Status ==="
echo "Date: $(date)"
echo ""

echo "Service Status:"
sudo systemctl is-active pdf-rag
echo ""

echo "Memory Usage:"
free -h
echo ""

echo "Disk Usage:"
df -h /home/ragapp/pdf-rag
echo ""

echo "API Response Test:"
curl -s http://localhost:8000/ | jq -r '.message' || echo "API not responding"
echo ""

echo "Recent Logs (last 5 lines):"
sudo journalctl -u pdf-rag -n 5 --no-pager
```

---

## 🎯 Checklist Final

### ✅ Verificaciones Pre-Producción

- [ ] **Servicio funcionando**: `sudo systemctl status pdf-rag`
- [ ] **API responde**: `curl http://localhost:8000/`
- [ ] **Nginx configurado**: `sudo nginx -t`
- [ ] **Firewall activo**: `sudo ufw status`
- [ ] **SSL configurado** (si usas dominio): `sudo certbot certificates`
- [ ] **Documentos indexados**: `ls -la chroma_db/`
- [ ] **Backup configurado**: `ls -la /home/ragapp/backups/`
- [ ] **Logs funcionando**: `sudo journalctl -u pdf-rag -n 5`

### 🚀 URLs de Acceso

```
# API Principal
http://tu-servidor-ip/

# Consulta PDFs
POST http://tu-servidor-ip/ask

# Consulta Videos  
POST http://tu-servidor-ip/ask-video

# Lista Categorías
GET http://tu-servidor-ip/categories

# Stats Cache
GET http://tu-servidor-ip/cache/stats
```

---

## 📞 Comandos de Administración Rápida

```bash
# Ver estado general
sudo systemctl status pdf-rag nginx

# Reiniciar todo
sudo systemctl restart pdf-rag nginx

# Ver logs en tiempo real
sudo journalctl -u pdf-rag -f

# Backup manual
/home/ragapp/backup_rag.sh

# Verificar recursos
htop
df -h
```

¡Tu sistema RAG está listo para producción en Ubuntu! 🎉