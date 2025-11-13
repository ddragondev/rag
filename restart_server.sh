#!/bin/bash

echo "🔄 Reiniciando servidor FastAPI..."

# Matar el proceso anterior
pkill -f "uvicorn main:app"
sleep 2

# Iniciar el servidor
cd /Users/ddragondev/Documents/OpenAI-PDF-RAG-LangChain-master
source venv/bin/activate
uvicorn main:app --reload --host 0.0.0.0 --port 8000 &

echo "✅ Servidor reiniciado en http://0.0.0.0:8000"
echo "📋 Logs disponibles con: tail -f nohup.out"
