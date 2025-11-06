# 🚀 Deployment Rápido - Ubuntu

## Opción 1: Script Automático (Recomendado)

### En tu Ubuntu:

```bash
# 1. Descargar script
wget https://github.com/tu-usuario/tu-repo/raw/main/deploy_ubuntu.sh

# 2. Hacer ejecutable
chmod +x deploy_ubuntu.sh

# 3. Ejecutar
./deploy_ubuntu.sh
```

### Durante la ejecución:

- Te pedirá tu **OpenAI API Key**
- Opcionalmente tu **dominio** (o usar IP)
- Te dirá cuándo transferir archivos

---

## Opción 2: Manual (Paso a Paso)

### 1. Preparar servidor

```bash
sudo apt update && sudo apt upgrade -y
sudo apt install -y python3 python3-pip python3-venv git nginx
```

### 2. Transferir archivos desde tu Mac

```bash
# En tu Mac:
scp -r /Users/ddragondev/Documents/OpenAI-PDF-RAG-LangChain-master ubuntu@TU-IP:/home/ubuntu/pdf-rag
```

### 3. En Ubuntu - Configurar

```bash
cd /home/ubuntu/pdf-rag

# Crear entorno virtual
python3 -m venv venv
source venv/bin/activate

# Instalar dependencias
pip install -r requirements.txt

# Configurar API key
echo "OPENAI_API_KEY=tu-api-key" > .env

# Indexar documentos
python reindex_documents.py
```

### 4. Crear servicio

```bash
sudo nano /etc/systemd/system/pdf-rag.service
```

**Contenido:**

```ini
[Unit]
Description=PDF RAG API
After=network.target

[Service]
Type=simple
User=ubuntu
WorkingDirectory=/home/ubuntu/pdf-rag
Environment=PATH=/home/ubuntu/pdf-rag/venv/bin
ExecStart=/home/ubuntu/pdf-rag/venv/bin/uvicorn main:app --host 0.0.0.0 --port 8000
Restart=always

[Install]
WantedBy=multi-user.target
```

### 5. Iniciar servicio

```bash
sudo systemctl enable pdf-rag
sudo systemctl start pdf-rag
sudo systemctl status pdf-rag
```

### 6. Configurar Nginx

```bash
sudo nano /etc/nginx/sites-available/pdf-rag
```

**Contenido:**

```nginx
server {
    listen 80;
    server_name TU-IP;

    location / {
        proxy_pass http://127.0.0.1:8000;
        proxy_set_header Host $host;
        proxy_set_header X-Real-IP $remote_addr;
    }
}
```

### 7. Habilitar sitio

```bash
sudo ln -s /etc/nginx/sites-available/pdf-rag /etc/nginx/sites-enabled/
sudo systemctl restart nginx
```

### 8. Configurar firewall

```bash
sudo ufw allow 80
sudo ufw allow ssh
sudo ufw enable
```

---

## ✅ Verificar Funcionamiento

```bash
# Verificar servicio
sudo systemctl status pdf-rag

# Probar API
curl http://localhost:8000/

# Probar consulta
curl -X POST "http://TU-IP/ask" \
  -H "Content-Type: application/json" \
  -d '{
    "question": "que es compliance?",
    "category": "compliance",
    "format": "plain"
  }'
```

---

## 🔧 Comandos Útiles

```bash
# Ver logs en tiempo real
sudo journalctl -u pdf-rag -f

# Reiniciar servicio
sudo systemctl restart pdf-rag

# Ver estado del sistema
htop

# Backup manual
tar -czf backup-$(date +%Y%m%d).tar.gz chroma_db/ docs/
```

---

## 🛡️ SSL/HTTPS (Opcional)

Si tienes dominio:

```bash
sudo apt install certbot python3-certbot-nginx
sudo certbot --nginx -d tu-dominio.com
```

---

## 📊 URLs Disponibles

- **API Info**: `http://TU-IP/`
- **Categorías**: `http://TU-IP/categories`
- **Cache Stats**: `http://TU-IP/cache/stats`
- **Consulta PDFs**: `POST http://TU-IP/ask`
- **Consulta Videos**: `POST http://TU-IP/ask-video`

---

## ⚠️ Solución de Problemas

### Servicio no inicia

```bash
sudo journalctl -u pdf-rag -n 20
```

### Error de permisos

```bash
sudo chown -R ubuntu:ubuntu /home/ubuntu/pdf-rag
```

### API no responde

```bash
curl http://localhost:8000/
sudo systemctl restart pdf-rag
```

### Agregar documentos

```bash
# Copiar nuevo PDF
scp nuevo.pdf ubuntu@TU-IP:/home/ubuntu/pdf-rag/docs/compliance/

# Re-indexar
cd /home/ubuntu/pdf-rag
source venv/bin/activate
python reindex_documents.py
```

---

## 🎯 Resultado Final

Tendrás:

- ✅ API REST funcionando en puerto 80
- ✅ Nginx como proxy reverso
- ✅ Servicio systemd (auto-reinicio)
- ✅ Firewall configurado
- ✅ Base de datos vectorial indexada
- ✅ Sistema de logs
- ✅ Backup automático (si usas script)

**URL Final**: `http://TU-IP/` o `http://tu-dominio.com/`

¡Tu sistema RAG estará disponible 24/7 en internet! 🌐
