#!/bin/bash

# 🚀 Script Helper para Sistema RAG con MongoDB
# Facilita operaciones comunes del sistema

set -e

# Colores para output
RED='\033[0;31m'
GREEN='\033[0;32m'
YELLOW='\033[1;33m'
BLUE='\033[0;34m'
NC='\033[0m' # No Color

# Configuración
BASE_URL="http://localhost:8000"

# Funciones helper
print_header() {
    echo -e "\n${BLUE}========================================${NC}"
    echo -e "${BLUE}  $1${NC}"
    echo -e "${BLUE}========================================${NC}\n"
}

print_success() {
    echo -e "${GREEN}✅ $1${NC}"
}

print_error() {
    echo -e "${RED}❌ $1${NC}"
}

print_warning() {
    echo -e "${YELLOW}⚠️  $1${NC}"
}

print_info() {
    echo -e "${BLUE}ℹ️  $1${NC}"
}

# Verificar que el servidor está corriendo
check_server() {
    if curl -s "${BASE_URL}/" > /dev/null 2>&1; then
        return 0
    else
        return 1
    fi
}

# Comando: help
cmd_help() {
    print_header "Sistema RAG con MongoDB - Comandos Disponibles"
    
    cat << EOF
${GREEN}Gestión General:${NC}
  ${BLUE}./mongodb_helper.sh help${NC}              Muestra esta ayuda
  ${BLUE}./mongodb_helper.sh status${NC}            Estado del sistema
  ${BLUE}./mongodb_helper.sh migrate${NC}           Migra datos a MongoDB

${GREEN}Gestión de Caché:${NC}
  ${BLUE}./mongodb_helper.sh cache-stats${NC}       Estadísticas del caché
  ${BLUE}./mongodb_helper.sh cache-clear${NC}       Limpia todo el caché
  ${BLUE}./mongodb_helper.sh cache-clear-cat${NC}   Limpia caché de una categoría
  ${BLUE}./mongodb_helper.sh cache-clear-old${NC}   Limpia caché antiguo (> N días)

${GREEN}Gestión de Conversaciones:${NC}
  ${BLUE}./mongodb_helper.sh conversations${NC}     Lista conversaciones activas
  ${BLUE}./mongodb_helper.sh conversation-get${NC}  Obtiene historial de sesión
  ${BLUE}./mongodb_helper.sh conversation-clear${NC} Limpia una conversación
  ${BLUE}./mongodb_helper.sh conversations-clear${NC} Limpia todas

${GREEN}MongoDB:${NC}
  ${BLUE}./mongodb_helper.sh mongodb-health${NC}    Verifica salud de MongoDB
  ${BLUE}./mongodb_helper.sh mongodb-metrics${NC}   Obtiene métricas del sistema

${GREEN}Testing:${NC}
  ${BLUE}./mongodb_helper.sh test${NC}              Ejecuta suite de pruebas
  ${BLUE}./mongodb_helper.sh test-question${NC}     Prueba una pregunta

${GREEN}Ejemplos:${NC}
  ${BLUE}./mongodb_helper.sh cache-clear-cat geomecanica${NC}
  ${BLUE}./mongodb_helper.sh cache-clear-old 30${NC}
  ${BLUE}./mongodb_helper.sh conversation-get session-123${NC}
  ${BLUE}./mongodb_helper.sh test-question "¿Qué es la geomecánica?"${NC}

EOF
}

# Comando: status
cmd_status() {
    print_header "Estado del Sistema"
    
    if ! check_server; then
        print_error "El servidor no está corriendo"
        print_info "Inicia el servidor con: uvicorn main:app --reload --host 0.0.0.0 --port 8000"
        exit 1
    fi
    
    print_success "Servidor corriendo en ${BASE_URL}"
    
    # MongoDB Health
    print_info "Verificando MongoDB..."
    health=$(curl -s "${BASE_URL}/mongodb/health")
    status=$(echo $health | jq -r '.status // "unknown"')
    
    if [ "$status" = "healthy" ]; then
        print_success "MongoDB está saludable"
        echo "$health" | jq .
    else
        print_error "MongoDB tiene problemas"
        echo "$health" | jq .
    fi
}

# Comando: migrate
cmd_migrate() {
    print_header "Migración a MongoDB"
    
    print_info "Ejecutando script de migración..."
    python migrate_to_mongo.py
    
    if [ $? -eq 0 ]; then
        print_success "Migración completada"
    else
        print_error "Error en la migración"
        exit 1
    fi
}

# Comando: cache-stats
cmd_cache_stats() {
    print_header "Estadísticas del Caché"
    
    if ! check_server; then
        print_error "El servidor no está corriendo"
        exit 1
    fi
    
    curl -s "${BASE_URL}/cache/stats" | jq .
}

# Comando: cache-clear
cmd_cache_clear() {
    print_header "Limpiar Caché Completo"
    
    if ! check_server; then
        print_error "El servidor no está corriendo"
        exit 1
    fi
    
    print_warning "Esto eliminará TODO el caché"
    read -p "¿Estás seguro? (y/N): " confirm
    
    if [ "$confirm" = "y" ] || [ "$confirm" = "Y" ]; then
        result=$(curl -s -X DELETE "${BASE_URL}/cache/clear")
        print_success "Caché limpiado"
        echo "$result" | jq .
    else
        print_info "Operación cancelada"
    fi
}

# Comando: cache-clear-cat
cmd_cache_clear_cat() {
    print_header "Limpiar Caché por Categoría"
    
    if ! check_server; then
        print_error "El servidor no está corriendo"
        exit 1
    fi
    
    category=$1
    if [ -z "$category" ]; then
        print_error "Debes especificar una categoría"
        print_info "Uso: ./mongodb_helper.sh cache-clear-cat <categoria>"
        exit 1
    fi
    
    result=$(curl -s -X DELETE "${BASE_URL}/cache/clear/${category}")
    print_success "Caché de categoría '${category}' limpiado"
    echo "$result" | jq .
}

# Comando: cache-clear-old
cmd_cache_clear_old() {
    print_header "Limpiar Caché Antiguo"
    
    if ! check_server; then
        print_error "El servidor no está corriendo"
        exit 1
    fi
    
    days=$1
    if [ -z "$days" ]; then
        days=30
        print_info "Usando valor por defecto: $days días"
    fi
    
    result=$(curl -s -X DELETE "${BASE_URL}/cache/clear/older-than/${days}")
    print_success "Caché antiguo limpiado (> ${days} días)"
    echo "$result" | jq .
}

# Comando: conversations
cmd_conversations() {
    print_header "Conversaciones Activas"
    
    if ! check_server; then
        print_error "El servidor no está corriendo"
        exit 1
    fi
    
    curl -s "${BASE_URL}/conversations" | jq .
}

# Comando: conversation-get
cmd_conversation_get() {
    print_header "Historial de Conversación"
    
    if ! check_server; then
        print_error "El servidor no está corriendo"
        exit 1
    fi
    
    session_id=$1
    if [ -z "$session_id" ]; then
        print_error "Debes especificar un session_id"
        print_info "Uso: ./mongodb_helper.sh conversation-get <session_id>"
        exit 1
    fi
    
    curl -s "${BASE_URL}/conversations/${session_id}" | jq .
}

# Comando: conversation-clear
cmd_conversation_clear() {
    print_header "Limpiar Conversación"
    
    if ! check_server; then
        print_error "El servidor no está corriendo"
        exit 1
    fi
    
    session_id=$1
    if [ -z "$session_id" ]; then
        print_error "Debes especificar un session_id"
        print_info "Uso: ./mongodb_helper.sh conversation-clear <session_id>"
        exit 1
    fi
    
    result=$(curl -s -X DELETE "${BASE_URL}/conversations/${session_id}")
    print_success "Conversación '${session_id}' eliminada"
    echo "$result" | jq .
}

# Comando: conversations-clear
cmd_conversations_clear() {
    print_header "Limpiar Todas las Conversaciones"
    
    if ! check_server; then
        print_error "El servidor no está corriendo"
        exit 1
    fi
    
    print_warning "Esto eliminará TODAS las conversaciones"
    read -p "¿Estás seguro? (y/N): " confirm
    
    if [ "$confirm" = "y" ] || [ "$confirm" = "Y" ]; then
        result=$(curl -s -X DELETE "${BASE_URL}/conversations")
        print_success "Todas las conversaciones eliminadas"
        echo "$result" | jq .
    else
        print_info "Operación cancelada"
    fi
}

# Comando: mongodb-health
cmd_mongodb_health() {
    print_header "Salud de MongoDB"
    
    if ! check_server; then
        print_error "El servidor no está corriendo"
        exit 1
    fi
    
    curl -s "${BASE_URL}/mongodb/health" | jq .
}

# Comando: mongodb-metrics
cmd_mongodb_metrics() {
    print_header "Métricas de MongoDB"
    
    if ! check_server; then
        print_error "El servidor no está corriendo"
        exit 1
    fi
    
    hours=${1:-24}
    print_info "Obteniendo métricas de las últimas ${hours} horas..."
    
    curl -s "${BASE_URL}/mongodb/metrics?hours=${hours}" | jq .
}

# Comando: test
cmd_test() {
    print_header "Ejecutando Suite de Pruebas"
    
    python test_mongodb_migration.py
}

# Comando: test-question
cmd_test_question() {
    print_header "Prueba de Pregunta"
    
    if ! check_server; then
        print_error "El servidor no está corriendo"
        exit 1
    fi
    
    question=$1
    if [ -z "$question" ]; then
        question="¿Qué es la geomecánica?"
        print_info "Usando pregunta por defecto: $question"
    fi
    
    print_info "Enviando pregunta..."
    
    result=$(curl -s -X POST "${BASE_URL}/ask" \
        -H "Content-Type: application/json" \
        -d "{\"question\": \"$question\", \"category\": \"geomecanica\", \"format\": \"plain\"}")
    
    answer=$(echo "$result" | jq -r '.answer_plain // .answer // "Sin respuesta"')
    
    print_success "Respuesta recibida:"
    echo ""
    echo "$answer" | fold -w 80
    echo ""
}

# Main
main() {
    command=${1:-help}
    shift || true
    
    case "$command" in
        help)
            cmd_help
            ;;
        status)
            cmd_status
            ;;
        migrate)
            cmd_migrate
            ;;
        cache-stats)
            cmd_cache_stats
            ;;
        cache-clear)
            cmd_cache_clear
            ;;
        cache-clear-cat)
            cmd_cache_clear_cat "$@"
            ;;
        cache-clear-old)
            cmd_cache_clear_old "$@"
            ;;
        conversations)
            cmd_conversations
            ;;
        conversation-get)
            cmd_conversation_get "$@"
            ;;
        conversation-clear)
            cmd_conversation_clear "$@"
            ;;
        conversations-clear)
            cmd_conversations_clear
            ;;
        mongodb-health)
            cmd_mongodb_health
            ;;
        mongodb-metrics)
            cmd_mongodb_metrics "$@"
            ;;
        test)
            cmd_test
            ;;
        test-question)
            cmd_test_question "$@"
            ;;
        *)
            print_error "Comando desconocido: $command"
            echo ""
            cmd_help
            exit 1
            ;;
    esac
}

# Verificar dependencias
if ! command -v jq &> /dev/null; then
    print_warning "jq no está instalado (recomendado para formatear JSON)"
    print_info "Instala con: brew install jq (macOS) o apt-get install jq (Ubuntu)"
fi

# Ejecutar
main "$@"
