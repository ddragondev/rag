#!/bin/bash

# 🚀 Script de Auto-Deployment para Ubuntu
# Autor: AI Assistant
# Descripción: Instala y configura automáticamente el sistema PDF RAG

set -e  # Salir si hay errores

# Colores para output
RED='\033[0;31m'
GREEN='\033[0;32m'
YELLOW='\033[1;33m'
BLUE='\033[0;34m'
NC='\033[0m' # No Color

# Función para logs
log() {
    echo -e "${GREEN}[$(date +'%Y-%m-%d %H:%M:%S')] $1${NC}"
}

warn() {
    echo -e "${YELLOW}[WARNING] $1${NC}"
}

error() {
    echo -e "${RED}[ERROR] $1${NC}"
    exit 1
}

info() {
    echo -e "${BLUE}[INFO] $1${NC}"
}

# Banner
echo -e "${BLUE}"
cat << "EOF"
 ____  ____  _____   ____      _    ____  
|  _ \|  _ \|  ___| |  _ \    / \  / ___| 
| |_) | | | | |_    | |_) |  / _ \| |  _  
|  __/| |_| |  _|   |  _ <  / ___ \ |_| | 
|_|   |____/|_|     |_| \_\/_/   \_\____| 
                                          
Auto-Deployment Script para Ubuntu
EOF
echo -e "${NC}"

# Verificar que se ejecute como root o con sudo
if [[ $EUID -eq 0 ]]; then
   error "No ejecutes este script como root. Úsalo con un usuario normal que tenga sudo."
fi

# Verificar Ubuntu
if ! grep -q "Ubuntu" /etc/os-release; then
    error "Este script está diseñado para Ubuntu. OS detectado: $(cat /etc/os-release | grep PRETTY_NAME)"
fi

log "Iniciando deployment del sistema PDF RAG..."

# Configuración
APP_USER="ragapp"
APP_DIR="/home/$APP_USER/pdf-rag"
SERVICE_NAME="pdf-rag"
DOMAIN=""
OPENAI_API_KEY=""

# Pedir configuración
echo ""
info "Configuración inicial:"
read -p "Dominio (opcional, presiona Enter para usar solo IP): " DOMAIN
echo ""
read -p "OpenAI API Key: " OPENAI_API_KEY

if [[ -z "$OPENAI_API_KEY" ]]; then
    error "OpenAI API Key es requerida"
fi

# Paso 1: Actualizar sistema
log "Actualizando sistema Ubuntu..."
sudo apt update && sudo apt upgrade -y

# Paso 2: Instalar dependencias
log "Instalando dependencias del sistema..."
sudo apt install -y python3 python3-pip python3-venv git curl nginx supervisor htop iotop ufw

# Paso 3: Crear usuario de aplicación
log "Creando usuario de aplicación..."
if ! id "$APP_USER" &>/dev/null; then
    sudo useradd -m -s /bin/bash $APP_USER
    sudo usermod -aG sudo $APP_USER
    log "Usuario $APP_USER creado"
else
    warn "Usuario $APP_USER ya existe"
fi

# Paso 4: Crear directorio de aplicación
log "Configurando directorio de aplicación..."
sudo mkdir -p $APP_DIR
sudo chown $APP_USER:$APP_USER $APP_DIR

# Paso 5: Transferir archivos (necesita intervención manual)
echo ""
warn "ACCIÓN REQUERIDA:"
echo "Transfiere los archivos del proyecto a $APP_DIR"
echo "Desde tu Mac, ejecuta:"
echo "scp -r /Users/ddragondev/Documents/OpenAI-PDF-RAG-LangChain-master/* $APP_USER@$(hostname -I | awk '{print $1}'):$APP_DIR/"
echo ""
read -p "Presiona Enter cuando hayas transferido los archivos..."

# Verificar que los archivos existen
if [[ ! -f "$APP_DIR/main.py" ]]; then
    error "No se encontró main.py en $APP_DIR. Verifica la transferencia de archivos."
fi

# Paso 6: Configurar entorno virtual
log "Configurando entorno virtual Python..."
sudo -u $APP_USER bash -c "
cd $APP_DIR
python3 -m venv venv
source venv/bin/activate
pip install --upgrade pip
pip install fastapi uvicorn python-dotenv
pip install langchain langchain-community langchain-openai
pip install langchain-chroma chromadb
pip install langchain-text-splitters
pip install pypdf unstructured[pdf]
"

# Paso 7: Crear archivo .env
log "Configurando variables de entorno..."
sudo -u $APP_USER bash -c "cat > $APP_DIR/.env << EOF
OPENAI_API_KEY=$OPENAI_API_KEY
ENVIRONMENT=production
PORT=8000
HOST=0.0.0.0
EOF"

# Paso 8: Indexar documentos
log "Indexando documentos..."
if [[ -f "$APP_DIR/reindex_documents.py" ]]; then
    sudo -u $APP_USER bash -c "
    cd $APP_DIR
    source venv/bin/activate
    python reindex_documents.py
    "
else
    warn "No se encontró reindex_documents.py. Tendrás que indexar manualmente."
fi

# Paso 9: Crear servicio systemd
log "Configurando servicio systemd..."
sudo tee /etc/systemd/system/$SERVICE_NAME.service > /dev/null << EOF
[Unit]
Description=PDF RAG API Service
After=network.target

[Service]
Type=simple
User=$APP_USER
Group=$APP_USER
WorkingDirectory=$APP_DIR
Environment=PATH=$APP_DIR/venv/bin
ExecStart=$APP_DIR/venv/bin/uvicorn main:app --host 0.0.0.0 --port 8000 --workers 2
Restart=always
RestartSec=3
StandardOutput=journal
StandardError=journal

[Install]
WantedBy=multi-user.target
EOF

# Paso 10: Habilitar y iniciar servicio
log "Habilitando e iniciando servicio..."
sudo systemctl daemon-reload
sudo systemctl enable $SERVICE_NAME
sudo systemctl start $SERVICE_NAME

# Verificar que el servicio esté funcionando
sleep 5
if sudo systemctl is-active --quiet $SERVICE_NAME; then
    log "Servicio $SERVICE_NAME iniciado correctamente"
else
    error "Error al iniciar el servicio. Verifica los logs: sudo journalctl -u $SERVICE_NAME -f"
fi

# Paso 11: Configurar Nginx
log "Configurando Nginx..."

# Crear configuración básica
if [[ -n "$DOMAIN" ]]; then
    SERVER_NAME=$DOMAIN
else
    SERVER_NAME=$(hostname -I | awk '{print $1}')
fi

sudo tee /etc/nginx/sites-available/$SERVICE_NAME > /dev/null << EOF
server {
    listen 80;
    server_name $SERVER_NAME;

    location / {
        proxy_pass http://127.0.0.1:8000;
        proxy_set_header Host \$host;
        proxy_set_header X-Real-IP \$remote_addr;
        proxy_set_header X-Forwarded-For \$proxy_add_x_forwarded_for;
        proxy_set_header X-Forwarded-Proto \$scheme;
        
        proxy_read_timeout 300;
        proxy_connect_timeout 300;
        proxy_send_timeout 300;
    }
}
EOF

# Habilitar sitio
sudo ln -sf /etc/nginx/sites-available/$SERVICE_NAME /etc/nginx/sites-enabled/
sudo rm -f /etc/nginx/sites-enabled/default

# Verificar configuración de nginx
if sudo nginx -t; then
    sudo systemctl restart nginx
    sudo systemctl enable nginx
    log "Nginx configurado correctamente"
else
    error "Error en configuración de Nginx"
fi

# Paso 12: Configurar firewall
log "Configurando firewall..."
sudo ufw --force enable
sudo ufw allow ssh
sudo ufw allow 80
sudo ufw allow 443

# Paso 13: Crear script de backup
log "Configurando sistema de backup..."
sudo -u $APP_USER bash -c "
mkdir -p /home/$APP_USER/backups
cat > /home/$APP_USER/backup_rag.sh << 'EOF'
#!/bin/bash
BACKUP_DIR=\"/home/$APP_USER/backups\"
DATE=\$(date +%Y%m%d_%H%M%S)

mkdir -p \$BACKUP_DIR
tar -czf \$BACKUP_DIR/chroma_db_\$DATE.tar.gz -C $APP_DIR chroma_db/ 2>/dev/null || true
tar -czf \$BACKUP_DIR/docs_\$DATE.tar.gz -C $APP_DIR docs/ 2>/dev/null || true
cp $APP_DIR/.env \$BACKUP_DIR/env_\$DATE.backup 2>/dev/null || true

find \$BACKUP_DIR -name \"*.tar.gz\" -mtime +7 -delete 2>/dev/null || true
find \$BACKUP_DIR -name \"*.backup\" -mtime +7 -delete 2>/dev/null || true

echo \"Backup completado: \$DATE\"
EOF

chmod +x /home/$APP_USER/backup_rag.sh
"

# Configurar crontab para backup diario
sudo -u $APP_USER bash -c "(crontab -l 2>/dev/null; echo '0 2 * * * /home/$APP_USER/backup_rag.sh >> /home/$APP_USER/backup.log 2>&1') | crontab -"

# Paso 14: SSL/HTTPS (si se proporcionó dominio)
if [[ -n "$DOMAIN" ]]; then
    log "Configurando SSL con Let's Encrypt..."
    sudo apt install -y certbot python3-certbot-nginx
    
    echo ""
    info "Para configurar SSL, ejecuta manualmente:"
    echo "sudo certbot --nginx -d $DOMAIN"
    echo ""
fi

# Paso 15: Crear script de monitoreo
log "Creando herramientas de monitoreo..."
sudo -u $APP_USER bash -c "
cat > /home/$APP_USER/monitor_rag.sh << 'EOF'
#!/bin/bash
echo \"=== PDF RAG System Status ===\"
echo \"Date: \$(date)\"
echo \"\"

echo \"Service Status:\"
sudo systemctl is-active $SERVICE_NAME
echo \"\"

echo \"Memory Usage:\"
free -h
echo \"\"

echo \"Disk Usage:\"
df -h $APP_DIR
echo \"\"

echo \"API Response Test:\"
curl -s http://localhost:8000/ | jq -r '.message' 2>/dev/null || curl -s http://localhost:8000/ || echo \"API not responding\"
echo \"\"

echo \"Recent Logs (last 5 lines):\"
sudo journalctl -u $SERVICE_NAME -n 5 --no-pager
EOF

chmod +x /home/$APP_USER/monitor_rag.sh
"

# Verificación final
log "Realizando verificaciones finales..."

# Verificar servicio
sleep 3
if sudo systemctl is-active --quiet $SERVICE_NAME; then
    log "✅ Servicio funcionando"
else
    warn "⚠️  Servicio no está activo"
fi

# Verificar nginx
if sudo systemctl is-active --quiet nginx; then
    log "✅ Nginx funcionando"
else
    warn "⚠️  Nginx no está activo"
fi

# Verificar API
sleep 2
if curl -s http://localhost:8000/ | grep -q "PDF"; then
    log "✅ API respondiendo"
else
    warn "⚠️  API no responde correctamente"
fi

# Mostrar información final
echo ""
echo -e "${GREEN}========================="
echo "🎉 DEPLOYMENT COMPLETADO"
echo "=========================${NC}"
echo ""
info "Información del deployment:"
echo "• Usuario de aplicación: $APP_USER"
echo "• Directorio: $APP_DIR"
echo "• Servicio: $SERVICE_NAME"
echo "• URL: http://$SERVER_NAME"
echo ""
info "URLs disponibles:"
echo "• API Info: http://$SERVER_NAME/"
echo "• Categorías: http://$SERVER_NAME/categories"
echo "• Cache Stats: http://$SERVER_NAME/cache/stats"
echo ""
info "Comandos útiles:"
echo "• Ver logs: sudo journalctl -u $SERVICE_NAME -f"
echo "• Reiniciar: sudo systemctl restart $SERVICE_NAME"
echo "• Estado: sudo systemctl status $SERVICE_NAME"
echo "• Monitoreo: /home/$APP_USER/monitor_rag.sh"
echo "• Backup: /home/$APP_USER/backup_rag.sh"
echo ""

if [[ -n "$DOMAIN" ]]; then
    warn "Para habilitar HTTPS, ejecuta:"
    echo "sudo certbot --nginx -d $DOMAIN"
    echo ""
fi

info "Ejemplo de uso:"
echo "curl -X POST 'http://$SERVER_NAME/ask' \\"
echo "  -H 'Content-Type: application/json' \\"
echo "  -d '{\"question\": \"que es compliance?\", \"category\": \"compliance\", \"format\": \"plain\"}'"
echo ""

log "¡Deployment completado exitosamente! 🚀"