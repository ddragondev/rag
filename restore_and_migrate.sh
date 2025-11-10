#!/bin/bash
# Script para restaurar backup y re-migrar a MongoDB

echo "🔄 Restaurando categories_config.json desde backup..."

# Buscar el archivo de backup más reciente
BACKUP_FILE=$(ls -t categories_config.json.backup_* 2>/dev/null | head -n 1)

if [ -z "$BACKUP_FILE" ]; then
    echo "❌ No se encontró archivo de backup"
    exit 1
fi

echo "📁 Encontrado: $BACKUP_FILE"

# Restaurar el archivo
cp "$BACKUP_FILE" categories_config.json

if [ $? -eq 0 ]; then
    echo "✅ Archivo restaurado exitosamente"
    echo ""
    echo "🚀 Ejecutando migración a MongoDB..."
    echo ""
    python migrate_to_mongo.py
else
    echo "❌ Error al restaurar archivo"
    exit 1
fi
