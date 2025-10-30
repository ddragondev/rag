#!/bin/bash

# 🎥 Ejemplo Simple: Chat con Video usando cURL
# 
# Este script muestra cómo chatear con un video específico usando cURL

echo "════════════════════════════════════════════════════════════════════"
echo "🎥 CHAT CON VIDEO: modulo_1"
echo "════════════════════════════════════════════════════════════════════"

# Video a consultar
VIDEO_ID="modulo_1"
CATEGORY="geomecanica"

# ============================================
# PREGUNTA 1: ¿De qué trata este módulo?
# ============================================
echo ""
echo "────────────────────────────────────────────────────────────────────"
echo "❓ PREGUNTA 1: ¿De qué trata este módulo?"
echo "────────────────────────────────────────────────────────────────────"
echo ""

curl -X POST http://localhost:8000/ask-video \
  -H "Content-Type: application/json" \
  -d "{
    \"question\": \"¿De qué trata este módulo?\",
    \"video_id\": \"$VIDEO_ID\",
    \"category\": \"$CATEGORY\",
    \"format\": \"plain\"
  }" \
  2>/dev/null | python3 -c "
import sys, json
data = json.load(sys.stdin)
print('💡 RESPUESTA:')
print(data.get('answer_plain', 'Sin respuesta'))
"

# ============================================
# PREGUNTA 2: ¿Cuáles son los conceptos principales?
# ============================================
echo ""
echo "────────────────────────────────────────────────────────────────────"
echo "❓ PREGUNTA 2: ¿Cuáles son los conceptos principales?"
echo "────────────────────────────────────────────────────────────────────"
echo ""

curl -X POST http://localhost:8000/ask-video \
  -H "Content-Type: application/json" \
  -d "{
    \"question\": \"¿Cuáles son los conceptos principales que se cubren?\",
    \"video_id\": \"$VIDEO_ID\",
    \"category\": \"$CATEGORY\",
    \"format\": \"plain\"
  }" \
  2>/dev/null | python3 -c "
import sys, json
data = json.load(sys.stdin)
print('💡 RESPUESTA:')
print(data.get('answer_plain', 'Sin respuesta'))
"

# ============================================
# PREGUNTA 3: Resume lo más importante
# ============================================
echo ""
echo "────────────────────────────────────────────────────────────────────"
echo "❓ PREGUNTA 3: Resume lo más importante"
echo "────────────────────────────────────────────────────────────────────"
echo ""

curl -X POST http://localhost:8000/ask-video \
  -H "Content-Type: application/json" \
  -d "{
    \"question\": \"Resume los puntos más importantes en 3 puntos\",
    \"video_id\": \"$VIDEO_ID\",
    \"category\": \"$CATEGORY\",
    \"format\": \"plain\"
  }" \
  2>/dev/null | python3 -c "
import sys, json
data = json.load(sys.stdin)
print('💡 RESPUESTA:')
print(data.get('answer_plain', 'Sin respuesta'))
"

echo ""
echo "════════════════════════════════════════════════════════════════════"
echo "✅ Chat completado"
echo "════════════════════════════════════════════════════════════════════"
