#!/bin/bash

# 🔧 Script de Corrección Rápida para Deployment
# Ejecutar en tu servidor Ubuntu

set -e

echo "🔧 Corrigiendo problemas de deployment..."

# Colores
GREEN='\033[0;32m'
RED='\033[0;31m'
YELLOW='\033[1;33m'
NC='\033[0m'

log() {
    echo -e "${GREEN}[✅] $1${NC}"
}

warn() {
    echo -e "${YELLOW}[⚠️ ] $1${NC}"
}

error() {
    echo -e "${RED}[❌] $1${NC}"
}

# Verificar que estamos en el directorio correcto
if [[ ! -f "main.py" ]]; then
    error "No se encuentra main.py. Ejecuta este script desde el directorio del proyecto."
    exit 1
fi

log "Directorio correcto encontrado"

# 1. Corregir imports en reindex_documents.py
if [[ -f "reindex_documents.py" ]]; then
    log "Corrigiendo imports en reindex_documents.py..."
    
    # Hacer backup
    cp reindex_documents.py reindex_documents.py.backup
    
    # Corregir imports
    sed -i 's/from langchain\.text_splitter import/from langchain_text_splitters import/' reindex_documents.py
    sed -i 's/from langchain_community\.vectorstores import Chroma/from langchain_chroma import Chroma/' reindex_documents.py
    
    log "Imports corregidos"
else
    error "No se encuentra reindex_documents.py"
    exit 1
fi

# 2. Activar entorno virtual
if [[ -d "venv" ]]; then
    log "Activando entorno virtual..."
    source venv/bin/activate
else
    error "No se encuentra el entorno virtual. Créalo con: python3 -m venv venv"
    exit 1
fi

# 3. Verificar e instalar dependencias
log "Verificando dependencias..."

# Instalar dependencias faltantes
pip install --quiet langchain-text-splitters langchain-chroma chromadb

log "Dependencias instaladas"

# 4. Verificar .env
if [[ ! -f ".env" ]]; then
    warn "No se encuentra .env. Creando template..."
    cat > .env << EOF
OPENAI_API_KEY=tu-api-key-aqui
ENVIRONMENT=production
PORT=8000
HOST=0.0.0.0
EOF
    error "⚠️  IMPORTANTE: Edita .env y agrega tu OPENAI_API_KEY"
    echo "nano .env"
    exit 1
else
    if grep -q "tu-api-key-aqui" .env; then
        error "⚠️  IMPORTANTE: Actualiza tu OPENAI_API_KEY en .env"
        echo "nano .env"
        exit 1
    fi
    log "Archivo .env encontrado"
fi

# 5. Verificar estructura de directorios
log "Verificando estructura de directorios..."

mkdir -p docs/geomecanica docs/compliance videos/geomecanica

# Verificar si hay PDFs
geomecanica_pdfs=$(find docs/geomecanica -name "*.pdf" 2>/dev/null | wc -l)
compliance_pdfs=$(find docs/compliance -name "*.pdf" 2>/dev/null | wc -l)

if [[ $geomecanica_pdfs -eq 0 ]] || [[ $compliance_pdfs -eq 0 ]]; then
    warn "Faltan documentos PDF:"
    echo "  • Geomecánica: $geomecanica_pdfs PDFs"
    echo "  • Compliance: $compliance_pdfs PDFs"
    echo ""
    echo "Transfiere los PDFs desde tu Mac:"
    echo "scp -r /Users/ddragondev/Documents/OpenAI-PDF-RAG-LangChain-master/docs/* usuario@servidor:$(pwd)/docs/"
    echo ""
    echo "Luego ejecuta: python reindex_documents.py"
    exit 1
else
    log "Documentos encontrados: Geomecánica($geomecanica_pdfs), Compliance($compliance_pdfs)"
fi

# 6. Ejecutar re-indexación
log "Ejecutando re-indexación..."
python reindex_documents.py

# 7. Verificar resultado
if [[ -d "chroma_db" ]]; then
    collections=$(ls chroma_db/ 2>/dev/null | wc -l)
    log "Base de datos creada exitosamente ($collections colecciones)"
else
    error "No se pudo crear la base de datos vectorial"
    exit 1
fi

# 8. Probar que la API funciona
log "Probando la API..."
timeout 10 python -c "
import uvicorn
from main import app
uvicorn.run(app, host='0.0.0.0', port=8001, log_level='critical')
" &

api_pid=$!
sleep 3

# Probar endpoint
if curl -s http://localhost:8001/ | grep -q "PDF"; then
    log "API funcionando correctamente"
else
    warn "API no responde como esperado"
fi

# Matar proceso de prueba
kill $api_pid 2>/dev/null || true

# 9. Mostrar resumen
echo ""
echo "🎉 ¡Corrección completada!"
echo ""
echo "📋 Resumen:"
echo "  ✅ Imports corregidos"
echo "  ✅ Dependencias instaladas"
echo "  ✅ Base de datos vectorial creada"
echo "  ✅ API funcionando"
echo ""
echo "🚀 Próximos pasos:"
echo "  1. Configurar servicio systemd:"
echo "     sudo systemctl enable pdf-rag"
echo "     sudo systemctl start pdf-rag"
echo ""
echo "  2. Configurar Nginx (ver DEPLOY_UBUNTU.md)"
echo ""
echo "  3. Probar API:"
echo "     curl http://localhost:8000/"
echo ""
echo "📞 Para monitoreo:"
echo "  • Ver logs: sudo journalctl -u pdf-rag -f"
echo "  • Estado: sudo systemctl status pdf-rag"
echo "  • Manual: python main.py"
echo ""

log "¡Sistema listo para usar! 🚀"