import os
import glob
import json
import shutil
import dotenv
from fastapi import FastAPI, HTTPException, UploadFile, File, Depends
from fastapi.responses import StreamingResponse, HTMLResponse
from fastapi.middleware.cors import CORSMiddleware
from pydantic import BaseModel
from langchain_community.document_loaders import PyPDFLoader
from langchain_chroma import Chroma
from langchain_core.output_parsers import StrOutputParser
from langchain_core.runnables import RunnablePassthrough
from langchain_openai import OpenAIEmbeddings
from langchain_text_splitters import RecursiveCharacterTextSplitter
from langchain_openai import ChatOpenAI
import hashlib
from typing import Dict, List, Optional
import unicodedata
from datetime import datetime

# Importar MongoManager
from mongo_manager import get_mongo_manager, close_mongo_connection

# Importar Clerk Auth
from clerk_auth import (
    optional_auth, 
    require_auth, 
    get_session_id_from_user,
    get_user_metadata,
    ClerkUser
)

# Cargar variables de entorno
dotenv.load_dotenv()

# Inicializar FastAPI
app = FastAPI()

# Configurar CORS - DESARROLLO (permite todos los orígenes)
app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],  # ⚠️ TEMPORAL - En producción cambiar por dominios específicos
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

# Configuración de límites de subida de archivos
MAX_FILE_SIZE = 100 * 1024 * 1024  # 100 MB
MAX_FILE_SIZE_MB = MAX_FILE_SIZE / (1024 * 1024)

# Configurar el modelo optimizado
llm = ChatOpenAI(
    model="gpt-4o-mini",
    temperature=0,
    max_tokens=2000,
    request_timeout=30
)

# Cache global
vectorstore_cache: Dict[str, Chroma] = {}
# answer_cache y conversation_history ahora se gestionan con MongoDB
PERSIST_DIRECTORY = "chroma_db"
CATEGORIES_CONFIG_FILE = "categories_config.json"

# Instancia global de MongoDB
mongo = None

def ensure_mongo():
    """Verifica que MongoDB esté inicializado."""
    global mongo
    if mongo is None:
        try:
            mongo = get_mongo_manager()
            print("⚠️ MongoDB inicializado tardíamente")
        except Exception as e:
            raise HTTPException(
                status_code=503,
                detail=f"MongoDB no disponible: {str(e)}"
            )
    return mongo

# Modelos de datos
class QuestionRequest(BaseModel):
    question: str
    category: str
    format: str = "both"
    session_id: Optional[str] = None  # Para mantener contexto conversacional

class VideoQuestionRequest(BaseModel):
    question: str
    video_id: str
    category: str = "geomecanica"
    format: str = "both"

class CategoryCreate(BaseModel):
    name: str
    display_name: str
    description: str
    prompt_html: Optional[str] = None
    prompt_plain: Optional[str] = None

class CategoryUpdate(BaseModel):
    display_name: Optional[str] = None
    description: Optional[str] = None
    prompt_html: Optional[str] = None
    prompt_plain: Optional[str] = None

class PromptUpdate(BaseModel):
    prompt_html: str
    prompt_plain: str

class CategoryInfo(BaseModel):
    name: str
    display_name: str
    description: str
    created_at: str
    updated_at: str
    file_count: int
    has_custom_prompt: bool
    prompt_html: Optional[str] = None
    prompt_plain: Optional[str] = None


def normalize_category(category: str) -> str:
    """Normaliza el nombre de la categoría."""
    category = category.lower()
    category = unicodedata.normalize('NFD', category)
    category = ''.join(char for char in category if unicodedata.category(char) != 'Mn')
    return category


def load_categories_config() -> dict:
    """Carga la configuración de categorías desde archivo JSON."""
    if os.path.exists(CATEGORIES_CONFIG_FILE):
        with open(CATEGORIES_CONFIG_FILE, 'r', encoding='utf-8') as f:
            return json.load(f)
    return {}


def save_categories_config(config: dict):
    """Guarda la configuración de categorías en archivo JSON."""
    with open(CATEGORIES_CONFIG_FILE, 'w', encoding='utf-8') as f:
        json.dump(config, f, ensure_ascii=False, indent=2)


def get_category_info(category_name: str) -> dict:
    """Obtiene información de una categoría específica."""
    config = load_categories_config()
    category_name = normalize_category(category_name)
    
    if category_name not in config:
        return None
    
    # Contar archivos
    docs_path = f"docs/{category_name}"
    file_count = 0
    if os.path.exists(docs_path):
        file_count = len([f for f in os.listdir(docs_path) if f.endswith('.pdf')])
    
    category_data = config[category_name].copy()
    category_data['file_count'] = file_count
    category_data['has_custom_prompt'] = bool(category_data.get('prompt_html') or category_data.get('prompt_plain'))
    
    return category_data


def get_default_prompts(category: str) -> tuple:
    """Retorna prompts por defecto según la categoría."""
    if category == "geomecanica":
        html_prompt = """Eres un Asistente de Geomecánica especializado en minería. Tu objetivo es explicar conceptos de geomecánica de forma clara y educativa, pensando en trabajadores que pueden no tener conocimientos previos.

INFORMACIÓN TÉCNICA DISPONIBLE:
{context}

PREGUNTA: {question}

INSTRUCCIONES:
- Responde de forma cordial, simple y educativa
- Usa lenguaje accesible para trabajadores mineros
- Sé conciso y directo, evita párrafos largos
- Usa listas o viñetas cuando sea apropiado
- Si no hay información específica en los documentos, di: "No tengo información sobre esto en la documentación técnica disponible."
- Enfócate en aspectos prácticos de la geomecánica minera
- Formato HTML: <p>, <ul>, <li>, <strong>

Respuesta:"""
        
        plain_prompt = html_prompt.replace("- Formato HTML: <p>, <ul>, <li>, <strong>", "- Responde en texto plano")
        
    elif category == "compliance":
        html_prompt = """Eres un Asistente de Compliance especializado en normativas mineras. Tu objetivo es explicar regulaciones, procedimientos y requisitos legales de forma clara y precisa.

INFORMACIÓN NORMATIVA DISPONIBLE:
{context}

PREGUNTA: {question}

INSTRUCCIONES:
- Responde de forma profesional y precisa
- Enfócate en aspectos legales y normativos
- Cita artículos o secciones específicas cuando sea relevante
- Sé claro sobre obligaciones y responsabilidades
- Si no hay información específica, di: "No tengo información sobre esta normativa en la base de datos."
- Formato HTML: <p>, <ul>, <li>, <strong>

Respuesta:"""
        
        plain_prompt = html_prompt.replace("- Formato HTML: <p>, <ul>, <li>, <strong>", "- Responde en texto plano")
        
    else:
        # Prompt genérico
        html_prompt = """Basándote en la siguiente información de documentos técnicos, responde de forma directa y concisa:

INFORMACIÓN DISPONIBLE:
{context}

PREGUNTA: {question}

INSTRUCCIONES:
- Responde directamente, sin mencionar "el contexto" o "los documentos"
- Sé conciso y específico
- Si la información no está disponible, di: "No tengo información sobre esto en la base de datos."
- Usa formato HTML: <p>, <ul>, <li>, <strong>

Respuesta:"""
        
        plain_prompt = html_prompt.replace("- Usa formato HTML: <p>, <ul>, <li>, <strong>", "- Usa texto plano")
    
    return html_prompt, plain_prompt


def get_prompts_for_category(category: str) -> tuple:
    """Obtiene los prompts para una categoría (personalizados o por defecto)."""
    config = load_categories_config()
    category = normalize_category(category)
    
    if category in config and (config[category].get('prompt_html') or config[category].get('prompt_plain')):
        # Usar prompts personalizados
        html_prompt = config[category].get('prompt_html')
        plain_prompt = config[category].get('prompt_plain')
        
        # Si falta uno, usar el por defecto
        if not html_prompt or not plain_prompt:
            default_html, default_plain = get_default_prompts(category)
            html_prompt = html_prompt or default_html
            plain_prompt = plain_prompt or default_plain
            
        return html_prompt, plain_prompt
    else:
        # Usar prompts por defecto
        return get_default_prompts(category)


async def reindex_category_auto(category: str):
    """Re-indexa una categoría automáticamente después de cambios en archivos."""
    try:
        category = normalize_category(category)
        docs_path = f"docs/{category}"
        
        if not os.path.exists(docs_path):
            return
        
        pdf_files = glob.glob(os.path.join(docs_path, "*.pdf"))
        
        if not pdf_files:
            # Si no hay PDFs, eliminar vectorstore
            if category in vectorstore_cache:
                del vectorstore_cache[category]
            return
        
        print(f"🔄 Re-indexando categoría '{category}' automáticamente...")
        
        # Eliminar de caché
        if category in vectorstore_cache:
            del vectorstore_cache[category]
        
        # Cargar documentos
        documents = []
        for pdf_file in pdf_files:
            loader = PyPDFLoader(pdf_file)
            documents.extend(loader.load())
        
        if not documents:
            return
        
        # Dividir en chunks
        text_splitter = RecursiveCharacterTextSplitter(
            chunk_size=1500,
            chunk_overlap=150
        )
        splits = text_splitter.split_documents(documents)
        
        # Crear vectorstore
        embeddings = OpenAIEmbeddings()
        
        # Eliminar colección existente
        persist_path = os.path.join(PERSIST_DIRECTORY, category)
        if os.path.exists(persist_path):
            shutil.rmtree(persist_path)
        
        # Crear nueva colección
        vectorstore = Chroma.from_documents(
            documents=splits,
            embedding=embeddings,
            collection_name=category,
            persist_directory=PERSIST_DIRECTORY
        )
        
        # Guardar en caché
        vectorstore_cache[category] = vectorstore
        
        print(f"✅ Categoría '{category}' re-indexada exitosamente ({len(splits)} chunks)")
        
    except Exception as e:
        print(f"❌ Error re-indexando categoría '{category}': {str(e)}")
        raise


def get_cache_key(question: str, category: str, format_type: str) -> str:
    """Genera clave única para caché."""
    content = f"{question.lower().strip()}:{category}:{format_type}"
    return hashlib.md5(content.encode()).hexdigest()


def cache_answer(cache_key: str, answer: dict):
    """Guarda respuesta en caché usando MongoDB."""
    try:
        db = ensure_mongo()
        db.set_cached_answer(cache_key, answer)
    except Exception as e:
        print(f"⚠️ Error al cachear respuesta: {e}")


def get_conversation_history(session_id: str) -> List[dict]:
    """Obtiene el historial de conversación de una sesión desde MongoDB."""
    try:
        db = ensure_mongo()
        return db.get_conversation_history(session_id, limit=20)
    except Exception as e:
        print(f"⚠️ Error al obtener historial: {e}")
        return []


def add_to_conversation(session_id: str, role: str, content: str, metadata: Optional[dict] = None):
    """Agrega un mensaje al historial de conversación en MongoDB."""
    try:
        db = ensure_mongo()
        db.save_conversation_message(session_id, role, content, metadata)
        print(f"💾 Guardado: {role} en session {session_id[:20]}... ({len(content)} chars)")
    except Exception as e:
        print(f"⚠️ Error al guardar mensaje: {e}")


def format_conversation_context(history: List[dict]) -> str:
    """Formatea el historial de conversación para incluirlo en el prompt."""
    if not history:
        return ""
    
    context_lines = [
        "=" * 80,
        "HISTORIAL DE LA CONVERSACIÓN ACTUAL CON ESTE USUARIO",
        "=" * 80,
        "",
        "⚠️ INSTRUCCIÓN CRÍTICA:",
        "Este usuario YA te hizo preguntas antes. Lee el historial completo.",
        "Si pregunta '¿qué me dijiste?', '¿de qué hablamos?', 'explícalo de otra forma',",
        "debes hacer referencia EXPLÍCITA a lo que dijiste antes.",
        "NO respondas con saludos genéricos si hay historial previo.",
        "",
        "MENSAJES PREVIOS EN ESTA CONVERSACIÓN:",
        ""
    ]
    
    for msg in history[-6:]:  # Últimas 3 interacciones (6 mensajes)
        role = "👤 Usuario" if msg["role"] == "user" else "🤖 Tú (Asistente)"
        context_lines.append(f"{role}: {msg['content']}")
        context_lines.append("")  # Línea en blanco entre mensajes
    
    context_lines.append("=" * 80)
    context_lines.append("FIN DEL HISTORIAL - Ahora responde la pregunta actual considerando TODO lo anterior")
    context_lines.append("=" * 80)
    context_lines.append("")
    return "\n".join(context_lines)


def get_or_create_vectorstore(category: str):
    """Obtiene el vectorstore para una categoría (usa nombres simples)."""
    category = normalize_category(category)
    
    # Verificar que la categoría existe
    docs_path = f"docs/{category}"
    if not os.path.exists(docs_path):
        raise HTTPException(status_code=404, detail=f"Category '{category}' not found.")
    
    # Cache en memoria
    if category in vectorstore_cache:
        return vectorstore_cache[category]
    
    # Cargar desde disco usando el nombre de categoría directamente
    embeddings = OpenAIEmbeddings()
    
    try:
        print(f"📦 Cargando vectorstore '{category}' desde disco...")
        vectorstore = Chroma(
            collection_name=category,
            persist_directory=PERSIST_DIRECTORY,
            embedding_function=embeddings
        )
        
        # Verificar que tiene documentos
        test_docs = vectorstore.similarity_search("test", k=1)
        if not test_docs:
            raise HTTPException(
                status_code=500, 
                detail=f"Vectorstore '{category}' existe pero está vacío. Ejecuta: python reindex_documents.py"
            )
        
        vectorstore_cache[category] = vectorstore
        print(f"✅ Vectorstore '{category}' cargado correctamente")
        return vectorstore
        
    except Exception as e:
        raise HTTPException(
            status_code=500,
            detail=f"Error cargando vectorstore '{category}': {str(e)}. Ejecuta: python reindex_documents.py"
        )


def get_video_mapping(category: str = "geomecanica") -> Dict[str, str]:
    """Retorna mapeo de IDs de video a archivos."""
    category = normalize_category(category)
    videos_path = f"videos/{category}"
    
    if not os.path.exists(videos_path):
        return {}
    
    txt_files = glob.glob(os.path.join(videos_path, "*.txt"))
    mapping = {}
    
    for txt_file in txt_files:
        filename = os.path.basename(txt_file)
        if filename.startswith("Modulo_"):
            parts = filename.split("_")
            if len(parts) >= 2 and parts[1].isdigit():
                video_id = f"modulo_{parts[1]}"
                mapping[video_id] = txt_file
        else:
            video_id = os.path.splitext(filename)[0].lower().replace(" ", "_")
            mapping[video_id] = txt_file
    
    return mapping


def load_video_transcription(video_id: str, category: str = "geomecanica"):
    """Carga la transcripción de un video."""
    from langchain.schema import Document
    
    category = normalize_category(category)
    video_mapping = get_video_mapping(category)
    
    if video_id.lower() not in video_mapping:
        available_ids = list(video_mapping.keys())
        raise HTTPException(
            status_code=404, 
            detail=f"Video ID '{video_id}' not found. Available: {available_ids}"
        )
    
    txt_file = video_mapping[video_id.lower()]
    
    with open(txt_file, 'r', encoding='utf-8') as f:
        content = f.read()
    
    document = Document(
        page_content=content,
        metadata={
            "source": txt_file,
            "video_id": video_id,
            "category": category,
            "type": "video_transcription"
        }
    )
    
    return [document]


def get_or_create_video_vectorstore(video_id: str, category: str = "geomecanica"):
    """Crea vectorstore para un video."""
    category = normalize_category(category)
    cache_key = f"video_{category}_{video_id}"
    
    if cache_key in vectorstore_cache:
        return vectorstore_cache[cache_key]
    
    documents = load_video_transcription(video_id, category)
    
    text_splitter = RecursiveCharacterTextSplitter(
        chunk_size=1500,
        chunk_overlap=150
    )
    splits = text_splitter.split_documents(documents)
    
    embeddings = OpenAIEmbeddings()
    persist_path = os.path.join(PERSIST_DIRECTORY, f"video_{category}_{video_id}")
    
    if os.path.exists(persist_path):
        vectorstore = Chroma(
            persist_directory=persist_path,
            embedding_function=embeddings
        )
    else:
        vectorstore = Chroma.from_documents(
            documents=splits,
            embedding=embeddings,
            persist_directory=persist_path
        )
    
    vectorstore_cache[cache_key] = vectorstore
    return vectorstore


@app.post("/ask")
async def ask_question(
    question_request: QuestionRequest,
    user: Optional[ClerkUser] = Depends(optional_auth)
):
    """
    Endpoint simplificado - Deja que la IA evalúe si hay información relevante.
    Sin validaciones complejas, sin filtros de keywords.
    La IA es lo suficientemente inteligente para manejar esto.
    Con autenticación opcional para historial por usuario.
    """
    question = question_request.question
    category = normalize_category(question_request.category)
    format_type = question_request.format.lower()
    
    # Usar user_id si está autenticado, sino usar el session_id del request
    session_id = get_session_id_from_user(user, question_request.session_id)
    
    if format_type not in ["html", "plain", "both"]:
        raise HTTPException(status_code=400, detail="Invalid format")

    try:
        # Asegurar que MongoDB está disponible
        db = ensure_mongo()
        
        # Si hay session_id, NO usar caché (para conversaciones con contexto)
        use_cache = session_id is None
        
        if use_cache:
            # Verificar caché MongoDB solo si no hay sesión
            cache_key = get_cache_key(question, category, format_type)
            cached_answer = db.get_cached_answer(cache_key)
            if cached_answer:
                return cached_answer
        
        # Obtener vectorstore y buscar documentos relevantes
        vectorstore = get_or_create_vectorstore(category)
        retriever = vectorstore.as_retriever(
            search_type="mmr",
            search_kwargs={"k": 2, "fetch_k": 10}
        )
        
        relevant_docs = retriever.invoke(question)
        context = "\n\n".join([doc.page_content for doc in relevant_docs])
        
        # Extraer fuentes
        sources_info = []
        for doc in relevant_docs:
            fuente = doc.metadata.get("source", "Fuente desconocida")
            pagina = doc.metadata.get("page", "Página no especificada")
            sources_info.append(f"{fuente} (pág. {pagina})")
        
        sources_html = "".join(f"<li>{source}</li>" for source in sources_info)
        sources_plain = "\n".join(f"• {source}" for source in sources_info)
        
        result = {
            "question": question,
            "category": category,
            "format": format_type
        }
        
        # Si hay session_id, agregar historial conversacional
        conversation_context = ""
        if session_id:
            history = get_conversation_history(session_id)
            print(f"🔍 DEBUG: session_id={session_id}, historial tiene {len(history)} mensajes")
            if history:
                print(f"🔍 DEBUG: Últimos mensajes: {[m['role'] for m in history[-4:]]}")
            conversation_context = format_conversation_context(history)
            if conversation_context:
                print(f"🔍 DEBUG: Contexto formateado ({len(conversation_context)} chars)")
            result["session_id"] = session_id
            
            # Agregar info del usuario si está autenticado
            if user:
                result["authenticated"] = True
                result["user_email"] = user.email
                result["user_id"] = user.user_id
        
        # Obtener prompts personalizados o por defecto
        html_prompt_template, plain_prompt_template = get_prompts_for_category(category)
        
        # Variable para guardar la respuesta final (evitar duplicados)
        final_answer_for_history = None
        
        if format_type in ["html", "both"]:
            # Insertar historial conversacional si existe
            full_context = f"{conversation_context}\n\nINFORMACIÓN DE DOCUMENTOS:\n{context}" if conversation_context else context
            prompt = html_prompt_template.format(context=full_context, question=question)
            print(f"🤖 DEBUG HTML: Prompt tiene {len(prompt)} chars, historial incluido: {bool(conversation_context)}")
            if conversation_context:
                print(f"📋 MUESTRA DEL CONTEXTO (primeros 500 chars):\n{full_context[:500]}\n")
            answer = llm.invoke(prompt).content
            result["answer"] = answer
            result["sources"] = f"<ul>{sources_html}</ul>"
            final_answer_for_history = answer  # Guardar para historial
        
        if format_type in ["plain", "both"]:
            # Insertar historial conversacional si existe
            full_context = f"{conversation_context}\n\nINFORMACIÓN DE DOCUMENTOS:\n{context}" if conversation_context else context
            prompt = plain_prompt_template.format(context=full_context, question=question)
            print(f"🤖 DEBUG PLAIN: Prompt tiene {len(prompt)} chars, historial incluido: {bool(conversation_context)}")
            if conversation_context:
                print(f"📋 MUESTRA DEL CONTEXTO (primeros 500 chars):\n{full_context[:500]}\n")
            answer_plain = llm.invoke(prompt).content
            result["answer_plain"] = answer_plain
            result["sources_plain"] = sources_plain
            
            # Si no hay HTML, usar plain para el historial
            if format_type == "plain":
                final_answer_for_history = answer_plain
        
        # Guardar en historial UNA SOLA VEZ al final
        if session_id and final_answer_for_history:
            metadata = {"category": category, "format": format_type}
            
            # Agregar metadata del usuario si está autenticado
            if user:
                metadata.update(get_user_metadata(user))
            
            add_to_conversation(session_id, "user", question, metadata)
            add_to_conversation(session_id, "assistant", final_answer_for_history, metadata)
        
        # Guardar en caché solo si no hay sesión
        if use_cache:
            cache_key = get_cache_key(question, category, format_type)
            cache_answer(cache_key, result)
        
        return result
        
    except HTTPException as e:
        raise e
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))


@app.post("/ask-video")
async def ask_video_question(request: VideoQuestionRequest):
    """Endpoint para videos - También simplificado."""
    question = request.question
    video_id = request.video_id.lower()
    category = normalize_category(request.category)
    format_type = request.format.lower()
    
    if format_type not in ["html", "plain", "both"]:
        raise HTTPException(status_code=400, detail="Invalid format")

    try:
        vectorstore = get_or_create_video_vectorstore(video_id, category)
        retriever = vectorstore.as_retriever(search_kwargs={"k": 4})
        
        relevant_docs = retriever.invoke(question)
        context = "\n\n".join([doc.page_content for doc in relevant_docs])
        
        video_metadata = relevant_docs[0].metadata if relevant_docs else {}
        video_source = video_metadata.get("source", "Fuente desconocida")
        
        sources_html = f"<li>Video: {video_id} ({video_source})</li>"
        sources_plain = f"• Video: {video_id} ({video_source})"
        
        result = {
            "question": question,
            "video_id": video_id,
            "category": category,
            "format": format_type
        }
        
        if format_type in ["html", "both"]:
            prompt = f"""Basándote en la transcripción del video, responde de forma directa y concisa:

TRANSCRIPCIÓN:
{context}

PREGUNTA: {question}

INSTRUCCIONES:
- Responde directamente, sin mencionar "la transcripción" o "el video"
- Sé conciso y específico
- Si no hay información, di: "No tengo información sobre esto en este video."
- Usa formato HTML: <p>, <ul>, <strong>

Respuesta:"""
            
            answer = llm.invoke(prompt).content
            result["answer_html"] = f"""
<div>
    <h2>Video {video_id.upper()}</h2>
    {answer}
    <hr>
    <h4>📹 Fuente:</h4>
    <ul>{sources_html}</ul>
</div>
"""
        
        if format_type in ["plain", "both"]:
            prompt = f"""Basándote en la transcripción del video, responde de forma directa y concisa:

TRANSCRIPCIÓN:
{context}

PREGUNTA: {question}

INSTRUCCIONES:
- Responde directamente, sin mencionar "la transcripción" o "el video"
- Sé conciso y específico
- Si no hay información, di: "No tengo información sobre esto en este video."
- Usa texto plano

Respuesta:"""
            
            answer = llm.invoke(prompt).content
            result["answer_plain"] = f"{answer}"
        
        return result
        
    except HTTPException as e:
        raise e
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))


@app.get("/videos/{category}")
async def list_videos(category: str):
    """Lista videos disponibles."""
    try:
        category = normalize_category(category)
        video_mapping = get_video_mapping(category)
        
        if not video_mapping:
            raise HTTPException(status_code=404, detail=f"No videos in '{category}'")
        
        videos_info = {}
        for video_id, filepath in video_mapping.items():
            videos_info[video_id] = {
                "filename": os.path.basename(filepath),
                "path": filepath
            }
        
        return {
            "category": category,
            "total_videos": len(videos_info),
            "videos": videos_info
        }
        
    except HTTPException as e:
        raise e
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))


@app.get("/cache/stats")
async def cache_stats():
    """Estadísticas del caché desde MongoDB."""
    try:
        stats = mongo.get_cache_stats()
        stats["vectorstore_cache_size"] = len(vectorstore_cache)
        return stats
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Error al obtener estadísticas: {str(e)}")


@app.get("/categories/{category_name}/files")
async def list_category_files(category_name: str):
    """Lista archivos de una categoría."""
    try:
        category_name = normalize_category(category_name)
        docs_path = f"docs/{category_name}"
        
        if not os.path.exists(docs_path):
            raise HTTPException(status_code=404, detail=f"Category '{category_name}' not found")
        
        files = []
        for filename in os.listdir(docs_path):
            if filename.endswith('.pdf'):
                filepath = os.path.join(docs_path, filename)
                stat = os.stat(filepath)
                files.append({
                    "filename": filename,
                    "size": stat.st_size,
                    "created_at": datetime.fromtimestamp(stat.st_ctime).isoformat(),
                    "modified_at": datetime.fromtimestamp(stat.st_mtime).isoformat()
                })
        
        return {
            "category": category_name,
            "files": files,
            "total": len(files)
        }
        
    except HTTPException:
        raise
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))


@app.post("/categories/{category_name}/upload")
async def upload_file(category_name: str, file: UploadFile = File(...)):
    """Sube un archivo PDF a una categoría (máx 100 MB)."""
    try:
        category_name = normalize_category(category_name)
        
        # Verificar que es PDF
        if not file.filename.endswith('.pdf'):
            raise HTTPException(status_code=400, detail="Only PDF files are allowed")
        
        # Leer contenido del archivo
        content = await file.read()
        
        # Validar tamaño del archivo
        file_size = len(content)
        if file_size > MAX_FILE_SIZE:
            file_size_mb = file_size / (1024 * 1024)
            raise HTTPException(
                status_code=413,
                detail=f"File too large ({file_size_mb:.2f} MB). Maximum allowed: {MAX_FILE_SIZE_MB:.0f} MB"
            )
        
        # Crear directorio si no existe
        docs_path = f"docs/{category_name}"
        os.makedirs(docs_path, exist_ok=True)
        
        # Guardar archivo
        file_path = os.path.join(docs_path, file.filename)
        
        # Verificar si ya existe
        if os.path.exists(file_path):
            raise HTTPException(status_code=400, detail=f"File '{file.filename}' already exists")
        
        # Escribir archivo
        with open(file_path, "wb") as buffer:
            buffer.write(content)
        
        # Re-indexar automáticamente
        await reindex_category_auto(category_name)
        
        # Limpiar caché de respuestas de esta categoría en MongoDB
        try:
            deleted = mongo.clear_cache(category=category_name)
            print(f"🗑️ Caché limpiado para categoría {category_name}: {deleted} entradas")
        except Exception as e:
            print(f"⚠️ Error al limpiar caché: {e}")
        
        # Calcular tamaño en MB para el mensaje
        file_size_mb = file_size / (1024 * 1024)
        print(f"✅ Archivo subido: {file.filename} ({file_size_mb:.2f} MB)")
        
        return {
            "message": f"File '{file.filename}' uploaded successfully to category '{category_name}'",
            "filename": file.filename,
            "size": file_size,
            "size_mb": round(file_size_mb, 2),
            "category": category_name,
            "max_size_mb": int(MAX_FILE_SIZE_MB)
        }
        
    except HTTPException:
        raise
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))


@app.put("/categories/{category_name}/prompt")
async def update_category_prompt(category_name: str, prompt_data: PromptUpdate):
    """Actualiza el prompt personalizado de una categoría."""
    try:
        category_name = normalize_category(category_name)
        
        # Verificar que la categoría existe
        docs_path = f"docs/{category_name}"
        if not os.path.exists(docs_path):
            raise HTTPException(status_code=404, detail=f"Category '{category_name}' not found")
        
        # Cargar configuración
        config = load_categories_config()
        
        # Si no existe en config, crear entrada básica
        if category_name not in config:
            now = datetime.now().isoformat()
            config[category_name] = {
                "name": category_name,
                "display_name": category_name.title(),
                "description": f"Categoría {category_name}",
                "created_at": now,
                "updated_at": now
            }
        
        # Actualizar prompts
        config[category_name]["prompt_html"] = prompt_data.prompt_html
        config[category_name]["prompt_plain"] = prompt_data.prompt_plain
        config[category_name]["updated_at"] = datetime.now().isoformat()
        
        save_categories_config(config)
        
        # Limpiar caché de respuestas de esta categoría en MongoDB
        try:
            deleted = mongo.clear_cache(category=category_name)
            print(f"🗑️ Caché limpiado para categoría {category_name}: {deleted} entradas")
        except Exception as e:
            print(f"⚠️ Error al limpiar caché: {e}")
        
        return {
            "message": f"Custom prompts updated for category '{category_name}'",
            "category": get_category_info(category_name)
        }
        
    except HTTPException:
        raise
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))


@app.get("/categories/{category_name}/prompt")
async def get_category_prompt(category_name: str):
    """Obtiene los prompts de una categoría (personalizados o por defecto)."""
    try:
        category_name = normalize_category(category_name)
        
        # Obtener prompts (personalizados o por defecto)
        html_prompt, plain_prompt = get_prompts_for_category(category_name)
        
        # Verificar si son personalizados
        config = load_categories_config()
        is_custom = category_name in config and (config[category_name].get('prompt_html') or config[category_name].get('prompt_plain'))
        
        return {
            "category": category_name,
            "prompt_html": html_prompt,
            "prompt_plain": plain_prompt,
            "is_custom": is_custom
        }
        
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))


@app.delete("/categories/{category_name}/prompt")
async def reset_category_prompt(category_name: str):
    """Resetea los prompts de una categoría a los valores por defecto."""
    try:
        category_name = normalize_category(category_name)
        
        # Cargar configuración
        config = load_categories_config()
        
        if category_name in config:
            # Eliminar prompts personalizados
            if 'prompt_html' in config[category_name]:
                del config[category_name]['prompt_html']
            if 'prompt_plain' in config[category_name]:
                del config[category_name]['prompt_plain']
            
            config[category_name]["updated_at"] = datetime.now().isoformat()
            save_categories_config(config)
        
        # Limpiar caché de respuestas de esta categoría en MongoDB
        try:
            deleted = mongo.clear_cache(category=category_name)
            print(f"🗑️ Caché limpiado para categoría {category_name}: {deleted} entradas")
        except Exception as e:
            print(f"⚠️ Error al limpiar caché: {e}")
        
        return {
            "message": f"Prompts reset to default for category '{category_name}'"
        }
        
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))


@app.delete("/cache/clear")
async def clear_cache():
    """Limpia todo el caché de MongoDB."""
    try:
        deleted = mongo.clear_cache()
        return {"message": f"Caché limpiado: {deleted} entradas eliminadas"}
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Error al limpiar caché: {str(e)}")


@app.delete("/cache/clear/{category}")
async def clear_cache_by_category(category: str):
    """Limpia el caché de una categoría específica."""
    try:
        category = normalize_category(category)
        deleted = mongo.clear_cache(category=category)
        return {"message": f"Caché de categoría '{category}' limpiado: {deleted} entradas eliminadas"}
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Error al limpiar caché: {str(e)}")


@app.delete("/cache/clear/older-than/{days}")
async def clear_old_cache(days: int):
    """Limpia entradas del caché más antiguas que N días."""
    try:
        deleted = mongo.clear_cache(older_than_days=days)
        return {"message": f"Caché antiguo limpiado: {deleted} entradas eliminadas (> {days} días)"}
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Error al limpiar caché: {str(e)}")


@app.get("/mongodb/health")
async def mongodb_health():
    """Verifica el estado de salud de MongoDB."""
    try:
        health = mongo.health_check()
        return health
    except Exception as e:
        return {
            "status": "error",
            "error": str(e)
        }


@app.get("/mongodb/metrics")
async def get_mongodb_metrics(hours: int = 24):
    """Obtiene métricas del sistema de las últimas N horas."""
    try:
        metrics = mongo.get_metrics(hours=hours)
        return {
            "hours": hours,
            "total_metrics": len(metrics),
            "metrics": metrics
        }
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Error al obtener métricas: {str(e)}")


@app.delete("/conversations/{session_id}")
async def clear_conversation(session_id: str):
    """Limpia el historial de una conversación específica en MongoDB."""
    try:
        deleted = mongo.clear_conversation(session_id)
        if deleted:
            return {"message": f"Conversación '{session_id}' eliminada exitosamente"}
        else:
            raise HTTPException(status_code=404, detail=f"Sesión '{session_id}' no encontrada")
    except HTTPException:
        raise
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Error al eliminar conversación: {str(e)}")


@app.delete("/conversations")
async def clear_all_conversations():
    """Limpia todas las conversaciones de MongoDB."""
    try:
        result = mongo.conversations_collection.delete_many({})
        return {"message": f"Se eliminaron {result.deleted_count} conversaciones"}
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Error al eliminar conversaciones: {str(e)}")


@app.get("/conversations/{session_id}")
async def get_conversation(session_id: str):
    """Obtiene el historial de una conversación."""
    history = get_conversation_history(session_id)
    
    # Obtener información adicional
    first_message = history[0]["content"] if history else ""
    last_message = history[-1]["content"] if history else ""
    
    return {
        "session_id": session_id,
        "message_count": len(history),
        "first_message": first_message[:100] + "..." if len(first_message) > 100 else first_message,
        "last_message": last_message[:100] + "..." if len(last_message) > 100 else last_message,
        "history": history
    }


@app.get("/conversations")
async def list_conversations():
    """Lista todas las conversaciones activas con resumen desde MongoDB."""
    try:
        # Obtener sesiones activas de las últimas 24 horas
        active_sessions = mongo.get_active_sessions(hours=24)
        
        conversations = []
        for session_data in active_sessions:
            session_id = session_data["session_id"]
            history = mongo.get_conversation_history(session_id, limit=100)
            
            if not history:
                continue
                
            # Obtener primera y última pregunta del usuario
            user_messages = [msg for msg in history if msg["role"] == "user"]
            assistant_messages = [msg for msg in history if msg["role"] == "assistant"]
            
            first_question = user_messages[0]["content"] if user_messages else ""
            last_question = user_messages[-1]["content"] if user_messages else ""
            last_answer = assistant_messages[-1]["content"] if assistant_messages else ""
            
            conversations.append({
                "session_id": session_id,
                "message_count": len(history),
                "interaction_count": len(user_messages),
                "first_question": first_question[:100] + "..." if len(first_question) > 100 else first_question,
                "last_question": last_question[:100] + "..." if len(last_question) > 100 else last_question,
                "last_answer": last_answer[:100] + "..." if len(last_answer) > 100 else last_answer,
                "preview": f"{first_question[:50]}..." if first_question else "Sin mensajes",
                "updated_at": session_data.get("updated_at")
            })
        
        # Ordenar por cantidad de mensajes (más recientes primero)
        conversations.sort(key=lambda x: x["message_count"], reverse=True)
        
        return {
            "total_conversations": len(conversations),
            "conversations": conversations
        }
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Error al listar conversaciones: {str(e)}")


@app.get("/categories")
async def list_categories():
    """Lista categorías disponibles con información detallada."""
    config = load_categories_config()
    
    # Obtener categorías de configuración
    configured_categories = {}
    for name, data in config.items():
        category_info = get_category_info(name)
        if category_info:
            configured_categories[name] = category_info
    
    # Buscar categorías en filesystem que no estén en config
    docs_path = "docs"
    filesystem_categories = {}
    if os.path.exists(docs_path):
        for d in os.listdir(docs_path):
            dir_path = os.path.join(docs_path, d)
            if os.path.isdir(dir_path) and not d.startswith('.'):
                normalized_name = normalize_category(d)
                if normalized_name not in configured_categories:
                    # Crear entrada básica para categorías no configuradas
                    file_count = len([f for f in os.listdir(dir_path) if f.endswith('.pdf')])
                    filesystem_categories[normalized_name] = {
                        "name": normalized_name,
                        "display_name": d.title(),
                        "description": f"Categoría {d} (no configurada)",
                        "created_at": "unknown",
                        "updated_at": "unknown",
                        "file_count": file_count,
                        "has_custom_prompt": False,
                        "prompt_html": None,
                        "prompt_plain": None
                    }
    
    all_categories = {**configured_categories, **filesystem_categories}
    
    return {
        "categories": list(all_categories.values()),
        "total": len(all_categories)
    }


@app.post("/categories")
async def create_category(category: CategoryCreate):
    """Crea una nueva categoría."""
    try:
        category_name = normalize_category(category.name)
        
        # Verificar que no existe
        config = load_categories_config()
        if category_name in config:
            raise HTTPException(status_code=400, detail=f"Category '{category_name}' already exists")
        
        # Crear directorio
        docs_path = f"docs/{category_name}"
        os.makedirs(docs_path, exist_ok=True)
        
        # Crear entrada en configuración
        now = datetime.now().isoformat()
        config[category_name] = {
            "name": category_name,
            "display_name": category.display_name,
            "description": category.description,
            "created_at": now,
            "updated_at": now,
            "prompt_html": category.prompt_html,
            "prompt_plain": category.prompt_plain
        }
        
        save_categories_config(config)
        
        return {
            "message": f"Category '{category_name}' created successfully",
            "category": get_category_info(category_name)
        }
        
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))


@app.get("/categories/{category_name}")
async def get_category(category_name: str):
    """Obtiene información detallada de una categoría."""
    try:
        category_name = normalize_category(category_name)
        category_info = get_category_info(category_name)
        
        if not category_info:
            # Verificar si existe en filesystem
            docs_path = f"docs/{category_name}"
            if os.path.exists(docs_path):
                file_count = len([f for f in os.listdir(docs_path) if f.endswith('.pdf')])
                return {
                    "name": category_name,
                    "display_name": category_name.title(),
                    "description": f"Categoría {category_name} (no configurada)",
                    "created_at": "unknown",
                    "updated_at": "unknown",
                    "file_count": file_count,
                    "has_custom_prompt": False,
                    "prompt_html": None,
                    "prompt_plain": None
                }
            else:
                raise HTTPException(status_code=404, detail=f"Category '{category_name}' not found")
        
        return category_info
        
    except HTTPException:
        raise
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))


@app.put("/categories/{category_name}")
async def update_category(category_name: str, update_data: CategoryUpdate):
    """Actualiza una categoría existente."""
    try:
        category_name = normalize_category(category_name)
        
        # Verificar que existe
        config = load_categories_config()
        if category_name not in config:
            # Si no está en config pero existe en filesystem, crear entrada
            docs_path = f"docs/{category_name}"
            if not os.path.exists(docs_path):
                raise HTTPException(status_code=404, detail=f"Category '{category_name}' not found")
            
            # Crear entrada básica
            now = datetime.now().isoformat()
            config[category_name] = {
                "name": category_name,
                "display_name": category_name.title(),
                "description": f"Categoría {category_name}",
                "created_at": now,
                "updated_at": now
            }
        
        # Actualizar campos
        if update_data.display_name is not None:
            config[category_name]["display_name"] = update_data.display_name
        if update_data.description is not None:
            config[category_name]["description"] = update_data.description
        if update_data.prompt_html is not None:
            config[category_name]["prompt_html"] = update_data.prompt_html
        if update_data.prompt_plain is not None:
            config[category_name]["prompt_plain"] = update_data.prompt_plain
        
        config[category_name]["updated_at"] = datetime.now().isoformat()
        
        save_categories_config(config)
        
        return {
            "message": f"Category '{category_name}' updated successfully",
            "category": get_category_info(category_name)
        }
        
    except HTTPException:
        raise
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))


@app.delete("/categories/{category_name}")
async def delete_category(category_name: str):
    """Elimina una categoría y todos sus archivos."""
    try:
        category_name = normalize_category(category_name)
        
        # Eliminar directorio y archivos
        docs_path = f"docs/{category_name}"
        if os.path.exists(docs_path):
            shutil.rmtree(docs_path)
        
        # Eliminar vectorstore
        if category_name in vectorstore_cache:
            del vectorstore_cache[category_name]
        
        vectorstore_path = os.path.join(PERSIST_DIRECTORY, category_name)
        if os.path.exists(vectorstore_path):
            shutil.rmtree(vectorstore_path)
        
        # Eliminar de configuración
        config = load_categories_config()
        if category_name in config:
            del config[category_name]
            save_categories_config(config)
        
        # Limpiar caché de respuestas relacionadas en MongoDB
        try:
            deleted = mongo.clear_cache(category=category_name)
            print(f"🗑️ Caché limpiado para categoría {category_name}: {deleted} entradas")
        except Exception as e:
            print(f"⚠️ Error al limpiar caché: {e}")
        
        return {
            "message": f"Category '{category_name}' deleted successfully"
        }
        
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))


@app.get("/health")
async def health_check():
    """Health check endpoint."""
    return {
        "status": "healthy",
        "mongodb": "connected" if mongo else "disconnected",
        "version": "4.1"
    }


@app.get("/")
async def root():
    """Info de la API."""
    return {
        "message": "PDF & Video RAG API - 🎛️ GESTIÓN AVANZADA + 💬 CONVERSACIONAL",
        "version": "4.1 - Conversational Memory System",
        "philosophy": "Sistema completo de gestión de categorías, archivos, prompts personalizados y memoria conversacional.",
        "features": [
            "✅ Gestión completa de categorías",
            "✅ Subida/eliminación de archivos por API",
            "✅ Prompts personalizados por categoría",
            "✅ Re-indexación automática",
            "✅ Panel de administración web",
            "✅ Memoria conversacional (historial de chat)",
            "✅ Caché inteligente",
            "✅ gpt-4o-mini optimizado"
        ],
        "endpoints": {
            "management": {
                "/admin": "GET - Panel de administración web",
                "/categories": "GET - Lista categorías, POST - Crear categoría",
                "/categories/{name}": "GET - Info, PUT - Actualizar, DELETE - Eliminar",
                "/categories/{name}/files": "GET - Lista archivos",
                "/categories/{name}/upload": "POST - Subir archivo PDF (máx 100 MB)",
                "/categories/{name}/files/{filename}": "DELETE - Eliminar archivo",
                "/categories/{name}/prompt": "GET/PUT/DELETE - Gestión prompts"
            },
            "queries": {
                "/ask": "POST - Consulta PDFs (con session_id opcional para conversación)",
                "/ask-video": "POST - Consulta videos por ID",
                "/videos/{category}": "GET - Lista videos disponibles"
            },
            "conversations": {
                "/conversations/{session_id}": "GET - Obtiene historial, DELETE - Limpia sesión",
                "/conversations": "DELETE - Limpia todas las conversaciones"
            },
            "system": {
                "/cache/stats": "GET - Estadísticas del caché",
                "/cache/clear": "DELETE - Limpia caché de respuestas"
            }
        },
        "note": "Usa /admin para gestionar el sistema. Agrega 'session_id' en /ask para conversaciones con contexto."
    }


@app.get("/admin", response_class=HTMLResponse)
async def admin_panel():
    """Panel de administración web."""
    html_content = """
<!DOCTYPE html>
<html lang="es">
<head>
    <meta charset="UTF-8">
    <meta name="viewport" content="width=device-width, initial-scale=1.0">
    <title>🎛️ Panel de Administración RAG</title>
    <style>
        * { margin: 0; padding: 0; box-sizing: border-box; }
        body { 
            font-family: 'Segoe UI', Tahoma, Geneva, Verdana, sans-serif; 
            background: linear-gradient(135deg, #667eea 0%, #764ba2 100%);
            min-height: 100vh;
            padding: 20px;
        }
        .container { 
            max-width: 1200px; 
            margin: 0 auto; 
            background: white; 
            border-radius: 15px; 
            box-shadow: 0 20px 40px rgba(0,0,0,0.1);
            overflow: hidden;
        }
        .header { 
            background: linear-gradient(45deg, #667eea, #764ba2); 
            color: white; 
            padding: 30px; 
            text-align: center; 
        }
        .header h1 { font-size: 2.5em; margin-bottom: 10px; }
        .header p { opacity: 0.9; font-size: 1.1em; }
        .nav { 
            background: #f8f9fa; 
            padding: 0; 
            border-bottom: 1px solid #e9ecef; 
        }
        .nav-btn { 
            background: none; 
            border: none; 
            padding: 20px 30px; 
            cursor: pointer; 
            font-size: 1em; 
            transition: all 0.3s;
            border-bottom: 3px solid transparent;
        }
        .nav-btn:hover { background: #e9ecef; }
        .nav-btn.active { 
            background: white; 
            border-bottom-color: #667eea; 
            color: #667eea;
            font-weight: bold;
        }
        .content { padding: 30px; min-height: 400px; }
        .section { display: none; }
        .section.active { display: block; }
        
        .card { 
            background: #f8f9fa; 
            border-radius: 10px; 
            padding: 20px; 
            margin: 20px 0; 
            border-left: 4px solid #667eea; 
        }
        .form-group { margin-bottom: 20px; }
        .form-group label { 
            display: block; 
            margin-bottom: 5px; 
            font-weight: bold; 
            color: #495057; 
        }
        .form-group input, .form-group textarea, .form-group select { 
            width: 100%; 
            padding: 12px; 
            border: 2px solid #e9ecef; 
            border-radius: 5px; 
            font-size: 1em;
            transition: border-color 0.3s;
        }
        .form-group input:focus, .form-group textarea:focus, .form-group select:focus { 
            outline: none; 
            border-color: #667eea; 
        }
        .btn { 
            background: #667eea; 
            color: white; 
            border: none; 
            padding: 12px 24px; 
            border-radius: 5px; 
            cursor: pointer; 
            font-size: 1em;
            transition: background 0.3s;
            margin-right: 10px;
        }
        .btn:hover { background: #5a6fd8; }
        .btn-danger { background: #dc3545; }
        .btn-danger:hover { background: #c82333; }
        .btn-success { background: #28a745; }
        .btn-success:hover { background: #218838; }
        
        .category-item { 
            background: white; 
            border: 1px solid #e9ecef; 
            border-radius: 8px; 
            padding: 20px; 
            margin: 10px 0; 
            transition: box-shadow 0.3s;
        }
        .category-item:hover { box-shadow: 0 5px 15px rgba(0,0,0,0.1); }
        .category-header { 
            display: flex; 
            justify-content: space-between; 
            align-items: center; 
            margin-bottom: 10px; 
        }
        .category-name { font-size: 1.2em; font-weight: bold; color: #495057; }
        .category-info { color: #6c757d; font-size: 0.9em; }
        .file-item { 
            background: #f8f9fa; 
            padding: 10px; 
            margin: 5px 0; 
            border-radius: 5px; 
            display: flex; 
            justify-content: space-between; 
            align-items: center; 
        }
        
        .status { 
            padding: 4px 12px; 
            border-radius: 20px; 
            font-size: 0.8em; 
            font-weight: bold; 
        }
        .status.success { background: #d4edda; color: #155724; }
        .status.warning { background: #fff3cd; color: #856404; }
        .status.info { background: #cce7ff; color: #004085; }
        
        .grid { display: grid; grid-template-columns: repeat(auto-fit, minmax(300px, 1fr)); gap: 20px; }
        .loading { text-align: center; padding: 40px; color: #6c757d; }
        .error { color: #dc3545; background: #f8d7da; padding: 10px; border-radius: 5px; margin: 10px 0; }
        .success { color: #155724; background: #d4edda; padding: 10px; border-radius: 5px; margin: 10px 0; }
        
        #dropZone {
            border: 2px dashed #667eea;
            border-radius: 10px;
            padding: 40px;
            text-align: center;
            background: #f8f9ff;
            margin: 20px 0;
            transition: all 0.3s;
            cursor: pointer;
        }
        #dropZone:hover, #dropZone.dragover {
            border-color: #5a6fd8;
            background: #f0f2ff;
        }
    </style>
</head>
<body>
    <div class="container">
        <div class="header">
            <h1>🎛️ Panel de Administración RAG</h1>
            <p>Gestión completa de categorías, archivos y prompts personalizados</p>
        </div>
        
        <div class="nav">
            <button class="nav-btn active" onclick="showSection('categories')">📁 Categorías</button>
            <button class="nav-btn" onclick="showSection('upload')">📤 Subir Archivos</button>
            <button class="nav-btn" onclick="showSection('prompts')">🤖 Prompts</button>
            <button class="nav-btn" onclick="showSection('system')">⚙️ Sistema</button>
        </div>
        
        <div class="content">
            <div id="categories" class="section active">
                <h2>📁 Gestión de Categorías</h2>
                <div class="card">
                    <h3>Crear Nueva Categoría</h3>
                    <form id="createCategoryForm">
                        <div class="form-group">
                            <label for="categoryName">Nombre interno (sin espacios, minúsculas):</label>
                            <input type="text" id="categoryName" placeholder="ej: seguridad_industrial" required>
                        </div>
                        <div class="form-group">
                            <label for="categoryDisplayName">Nombre para mostrar:</label>
                            <input type="text" id="categoryDisplayName" placeholder="ej: Seguridad Industrial" required>
                        </div>
                        <div class="form-group">
                            <label for="categoryDescription">Descripción:</label>
                            <textarea id="categoryDescription" rows="3" placeholder="Descripción de la categoría..."></textarea>
                        </div>
                        <button type="submit" class="btn">Crear Categoría</button>
                    </form>
                </div>
                
                <div class="card">
                    <h3>Categorías Existentes</h3>
                    <div id="categoriesList" class="loading">Cargando categorías...</div>
                </div>
            </div>
            
            <div id="upload" class="section">
                <h2>📤 Subir Archivos</h2>
                <div class="card">
                    <h3>Seleccionar Categoría y Archivos</h3>
                    <div class="form-group">
                        <label for="uploadCategory">Categoría:</label>
                        <select id="uploadCategory">
                            <option value="">Selecciona una categoría...</option>
                        </select>
                    </div>
                    
                    <div id="dropZone" onclick="document.getElementById('fileInput').click()">
                        <p>📎 Arrastra archivos PDF aquí o haz clic para seleccionar</p>
                        <p style="color: #6c757d; margin-top: 10px;">Solo archivos PDF son permitidos</p>
                    </div>
                    <input type="file" id="fileInput" multiple accept=".pdf" style="display: none;">
                    
                    <div id="uploadProgress" style="display: none;">
                        <h4>Subiendo archivos...</h4>
                        <div id="uploadList"></div>
                    </div>
                </div>
                
                <div class="card" id="filesSection" style="display: none;">
                    <h3>Archivos en Categoría</h3>
                    <div id="filesList"></div>
                </div>
            </div>
            
            <div id="prompts" class="section">
                <h2>🤖 Gestión de Prompts</h2>
                <div class="card">
                    <h3>Configurar Prompts Personalizados</h3>
                    <div class="form-group">
                        <label for="promptCategory">Categoría:</label>
                        <select id="promptCategory">
                            <option value="">Selecciona una categoría...</option>
                        </select>
                    </div>
                    
                    <div id="promptEditor" style="display: none;">
                        <div class="form-group">
                            <label for="promptHtml">Prompt para formato HTML:</label>
                            <textarea id="promptHtml" rows="10" placeholder="Prompt para respuestas en HTML..."></textarea>
                            <small style="color: #6c757d;">Usa {context} y {question} como variables</small>
                        </div>
                        <div class="form-group">
                            <label for="promptPlain">Prompt para formato texto:</label>
                            <textarea id="promptPlain" rows="10" placeholder="Prompt para respuestas en texto plano..."></textarea>
                            <small style="color: #6c757d;">Usa {context} y {question} como variables</small>
                        </div>
                        <button type="button" class="btn" onclick="savePrompt()">Guardar Prompts</button>
                        <button type="button" class="btn btn-danger" onclick="resetPrompt()">Restaurar por Defecto</button>
                    </div>
                </div>
            </div>
            
            <div id="system" class="section">
                <h2>⚙️ Estado del Sistema</h2>
                <div class="grid">
                    <div class="card">
                        <h3>📊 Estadísticas</h3>
                        <div id="systemStats" class="loading">Cargando estadísticas...</div>
                    </div>
                    <div class="card">
                        <h3>🧹 Mantenimiento</h3>
                        <button class="btn btn-danger" onclick="clearCache()">Limpiar Caché</button>
                        <p style="margin-top: 10px; color: #6c757d;">Elimina todas las respuestas cacheadas</p>
                    </div>
                </div>
            </div>
        </div>
    </div>

    <script>
        // Variables globales
        let categories = [];
        
        // Funciones de navegación
        function showSection(sectionName) {
            document.querySelectorAll('.section').forEach(s => s.classList.remove('active'));
            document.querySelectorAll('.nav-btn').forEach(b => b.classList.remove('active'));
            
            document.getElementById(sectionName).classList.add('active');
            event.target.classList.add('active');
            
            if (sectionName === 'categories') loadCategories();
            if (sectionName === 'upload') loadCategoriesForUpload();
            if (sectionName === 'prompts') loadCategoriesForPrompts();
            if (sectionName === 'system') loadSystemStats();
        }
        
        // Cargar categorías
        async function loadCategories() {
            try {
                const response = await fetch('/categories');
                const data = await response.json();
                categories = data.categories;
                
                const html = categories.map(cat => `
                    <div class="category-item">
                        <div class="category-header">
                            <div>
                                <div class="category-name">${cat.display_name}</div>
                                <div class="category-info">
                                    ${cat.name} • ${cat.file_count} archivos • 
                                    <span class="status ${cat.has_custom_prompt ? 'success' : 'info'}">
                                        ${cat.has_custom_prompt ? 'Prompt personalizado' : 'Prompt por defecto'}
                                    </span>
                                </div>
                            </div>
                            <div>
                                <button class="btn" onclick="editCategory('${cat.name}')">Editar</button>
                                <button class="btn btn-danger" onclick="deleteCategory('${cat.name}')">Eliminar</button>
                            </div>
                        </div>
                        <p>${cat.description}</p>
                    </div>
                `).join('');
                
                document.getElementById('categoriesList').innerHTML = html || '<p>No hay categorías configuradas.</p>';
            } catch (error) {
                document.getElementById('categoriesList').innerHTML = '<div class="error">Error cargando categorías: ' + error.message + '</div>';
            }
        }
        
        // Crear categoría
        document.getElementById('createCategoryForm').addEventListener('submit', async (e) => {
            e.preventDefault();
            
            const data = {
                name: document.getElementById('categoryName').value,
                display_name: document.getElementById('categoryDisplayName').value,
                description: document.getElementById('categoryDescription').value
            };
            
            try {
                const response = await fetch('/categories', {
                    method: 'POST',
                    headers: { 'Content-Type': 'application/json' },
                    body: JSON.stringify(data)
                });
                
                if (response.ok) {
                    document.getElementById('createCategoryForm').reset();
                    loadCategories();
                    showMessage('Categoría creada exitosamente', 'success');
                } else {
                    const error = await response.json();
                    showMessage('Error: ' + error.detail, 'error');
                }
            } catch (error) {
                showMessage('Error creando categoría: ' + error.message, 'error');
            }
        });
        
        // Eliminar categoría
        async function deleteCategory(name) {
            if (!confirm(`¿Estás seguro de que quieres eliminar la categoría "${name}" y todos sus archivos?`)) return;
            
            try {
                const response = await fetch(`/categories/${name}`, { method: 'DELETE' });
                if (response.ok) {
                    loadCategories();
                    showMessage('Categoría eliminada exitosamente', 'success');
                } else {
                    const error = await response.json();
                    showMessage('Error: ' + error.detail, 'error');
                }
            } catch (error) {
                showMessage('Error eliminando categoría: ' + error.message, 'error');
            }
        }
        
        // Cargar categorías para upload
        async function loadCategoriesForUpload() {
            const select = document.getElementById('uploadCategory');
            select.innerHTML = '<option value="">Selecciona una categoría...</option>';
            
            categories.forEach(cat => {
                select.innerHTML += `<option value="${cat.name}">${cat.display_name}</option>`;
            });
            
            select.addEventListener('change', loadCategoryFiles);
        }
        
        // Cargar archivos de categoría
        async function loadCategoryFiles() {
            const category = document.getElementById('uploadCategory').value;
            if (!category) {
                document.getElementById('filesSection').style.display = 'none';
                return;
            }
            
            try {
                const response = await fetch(`/categories/${category}/files`);
                const data = await response.json();
                
                const html = data.files.map(file => `
                    <div class="file-item">
                        <div>
                            <strong>${file.filename}</strong>
                            <small style="color: #6c757d; margin-left: 10px;">
                                ${(file.size / 1024 / 1024).toFixed(2)} MB
                            </small>
                        </div>
                        <button class="btn btn-danger" onclick="deleteFile('${category}', '${file.filename}')">
                            Eliminar
                        </button>
                    </div>
                `).join('');
                
                document.getElementById('filesList').innerHTML = html || '<p>No hay archivos en esta categoría.</p>';
                document.getElementById('filesSection').style.display = 'block';
            } catch (error) {
                showMessage('Error cargando archivos: ' + error.message, 'error');
            }
        }
        
        // Configurar drag & drop y upload
        const dropZone = document.getElementById('dropZone');
        const fileInput = document.getElementById('fileInput');
        
        ['dragenter', 'dragover', 'dragleave', 'drop'].forEach(eventName => {
            dropZone.addEventListener(eventName, preventDefaults, false);
        });
        
        ['dragenter', 'dragover'].forEach(eventName => {
            dropZone.addEventListener(eventName, () => dropZone.classList.add('dragover'), false);
        });
        
        ['dragleave', 'drop'].forEach(eventName => {
            dropZone.addEventListener(eventName, () => dropZone.classList.remove('dragover'), false);
        });
        
        dropZone.addEventListener('drop', handleDrop, false);
        fileInput.addEventListener('change', handleFileSelect, false);
        
        function preventDefaults(e) {
            e.preventDefault();
            e.stopPropagation();
        }
        
        function handleDrop(e) {
            const files = Array.from(e.dataTransfer.files);
            uploadFiles(files);
        }
        
        function handleFileSelect(e) {
            const files = Array.from(e.target.files);
            uploadFiles(files);
        }
        
        async function uploadFiles(files) {
            const category = document.getElementById('uploadCategory').value;
            if (!category) {
                showMessage('Selecciona una categoría primero', 'error');
                return;
            }
            
            const pdfFiles = files.filter(file => file.type === 'application/pdf');
            if (pdfFiles.length === 0) {
                showMessage('Solo se permiten archivos PDF', 'error');
                return;
            }
            
            const uploadProgress = document.getElementById('uploadProgress');
            const uploadList = document.getElementById('uploadList');
            uploadProgress.style.display = 'block';
            uploadList.innerHTML = '';
            
            for (const file of pdfFiles) {
                const formData = new FormData();
                formData.append('file', file);
                
                uploadList.innerHTML += `<div id="file-${file.name}">📄 ${file.name} - Subiendo...</div>`;
                
                try {
                    const response = await fetch(`/categories/${category}/upload`, {
                        method: 'POST',
                        body: formData
                    });
                    
                    if (response.ok) {
                        document.getElementById(`file-${file.name}`).innerHTML = `✅ ${file.name} - Completado`;
                    } else {
                        const error = await response.json();
                        document.getElementById(`file-${file.name}`).innerHTML = `❌ ${file.name} - Error: ${error.detail}`;
                    }
                } catch (error) {
                    document.getElementById(`file-${file.name}`).innerHTML = `❌ ${file.name} - Error: ${error.message}`;
                }
            }
            
            loadCategoryFiles();
            showMessage('Subida completada', 'success');
        }
        
        // Eliminar archivo
        async function deleteFile(category, filename) {
            if (!confirm(`¿Eliminar el archivo "${filename}"?`)) return;
            
            try {
                const response = await fetch(`/categories/${category}/files/${filename}`, { method: 'DELETE' });
                if (response.ok) {
                    loadCategoryFiles();
                    showMessage('Archivo eliminado exitosamente', 'success');
                } else {
                    const error = await response.json();
                    showMessage('Error: ' + error.detail, 'error');
                }
            } catch (error) {
                showMessage('Error eliminando archivo: ' + error.message, 'error');
            }
        }
        
        // Gestión de prompts
        async function loadCategoriesForPrompts() {
            const select = document.getElementById('promptCategory');
            select.innerHTML = '<option value="">Selecciona una categoría...</option>';
            
            categories.forEach(cat => {
                select.innerHTML += `<option value="${cat.name}">${cat.display_name}</option>`;
            });
            
            select.addEventListener('change', loadCategoryPrompt);
        }
        
        async function loadCategoryPrompt() {
            const category = document.getElementById('promptCategory').value;
            if (!category) {
                document.getElementById('promptEditor').style.display = 'none';
                return;
            }
            
            try {
                const response = await fetch(`/categories/${category}/prompt`);
                const data = await response.json();
                
                document.getElementById('promptHtml').value = data.prompt_html || '';
                document.getElementById('promptPlain').value = data.prompt_plain || '';
                document.getElementById('promptEditor').style.display = 'block';
            } catch (error) {
                showMessage('Error cargando prompt: ' + error.message, 'error');
            }
        }
        
        async function savePrompt() {
            const category = document.getElementById('promptCategory').value;
            const data = {
                prompt_html: document.getElementById('promptHtml').value,
                prompt_plain: document.getElementById('promptPlain').value
            };
            
            try {
                const response = await fetch(`/categories/${category}/prompt`, {
                    method: 'PUT',
                    headers: { 'Content-Type': 'application/json' },
                    body: JSON.stringify(data)
                });
                
                if (response.ok) {
                    showMessage('Prompts guardados exitosamente', 'success');
                } else {
                    const error = await response.json();
                    showMessage('Error: ' + error.detail, 'error');
                }
            } catch (error) {
                showMessage('Error guardando prompts: ' + error.message, 'error');
            }
        }
        
        async function resetPrompt() {
            const category = document.getElementById('promptCategory').value;
            if (!confirm('¿Restaurar prompts por defecto?')) return;
            
            try {
                const response = await fetch(`/categories/${category}/prompt`, { method: 'DELETE' });
                if (response.ok) {
                    loadCategoryPrompt();
                    showMessage('Prompts restaurados por defecto', 'success');
                } else {
                    const error = await response.json();
                    showMessage('Error: ' + error.detail, 'error');
                }
            } catch (error) {
                showMessage('Error restaurando prompts: ' + error.message, 'error');
            }
        }
        
        // Estadísticas del sistema
        async function loadSystemStats() {
            try {
                const response = await fetch('/cache/stats');
                const data = await response.json();
                
                document.getElementById('systemStats').innerHTML = `
                    <p><strong>Caché de respuestas:</strong> ${data.answer_cache_size}/${data.answer_cache_max} items</p>
                    <p><strong>Vectorstores cargados:</strong> ${data.vectorstore_cache_size} categorías</p>
                    <p><strong>Categorías totales:</strong> ${categories.length}</p>
                `;
            } catch (error) {
                document.getElementById('systemStats').innerHTML = '<div class="error">Error cargando estadísticas</div>';
            }
        }
        
        async function clearCache() {
            if (!confirm('¿Limpiar toda la caché de respuestas?')) return;
            
            try {
                const response = await fetch('/cache/clear', { method: 'DELETE' });
                if (response.ok) {
                    loadSystemStats();
                    showMessage('Caché limpiada exitosamente', 'success');
                } else {
                    showMessage('Error limpiando caché', 'error');
                }
            } catch (error) {
                showMessage('Error: ' + error.message, 'error');
            }
        }
        
        // Mostrar mensajes
        function showMessage(message, type) {
            const messageDiv = document.createElement('div');
            messageDiv.className = type;
            messageDiv.textContent = message;
            messageDiv.style.position = 'fixed';
            messageDiv.style.top = '20px';
            messageDiv.style.right = '20px';
            messageDiv.style.zIndex = '1000';
            messageDiv.style.padding = '15px';
            messageDiv.style.borderRadius = '5px';
            messageDiv.style.boxShadow = '0 5px 15px rgba(0,0,0,0.2)';
            
            document.body.appendChild(messageDiv);
            
            setTimeout(() => {
                messageDiv.remove();
            }, 5000);
        }
        
        // Cargar datos iniciales
        loadCategories();
    </script>
</body>
</html>
    """
    return HTMLResponse(content=html_content)


@app.on_event("startup")
async def startup():
    """Inicialización al arrancar."""
    global mongo
    try:
        mongo = get_mongo_manager()
        print("✅ Sistema iniciado con MongoDB")
        print(f"✅ MongoDB conectado: {mongo is not None}")
    except Exception as e:
        print(f"❌ Error al inicializar MongoDB: {e}")
        print("⚠️ El sistema funcionará en modo limitado")
        # Intentar reinicializar
        import traceback
        traceback.print_exc()
        raise  # Re-lanzar para que sea visible


@app.get("/my-history")
async def get_my_history(
    limit: int = 100,
    user: ClerkUser = Depends(require_auth)
):
    """Obtiene el historial de conversaciones del usuario autenticado."""
    try:
        # Usar el user_id como session_id
        history = mongo.get_conversation_history(user.user_id, limit=limit)
        
        return {
            "user_id": user.user_id,
            "user_email": user.email,
            "history": history,
            "total_messages": len(history)
        }
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))


@app.delete("/my-history")
async def clear_my_history(
    user: ClerkUser = Depends(require_auth)
):
    """Elimina el historial de conversaciones del usuario autenticado."""
    try:
        mongo.clear_conversation(user.user_id)
        
        return {
            "message": "Historial eliminado correctamente",
            "user_email": user.email
        }
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))


@app.get("/my-conversations")
async def get_my_conversations(
    user: ClerkUser = Depends(require_auth)
):
    """Lista todas las sesiones de conversación del usuario."""
    try:
        # Obtener todas las conversaciones del usuario
        conversations = mongo.conversations_collection.find({
            "session_id": user.user_id
        }).sort("updated_at", -1)
        
        result = []
        for conv in conversations:
            # Calcular el message_count manualmente desde el array de messages
            messages = conv.get("messages", [])
            message_count = len(messages)
            
            result.append({
                "session_id": conv["session_id"],
                "message_count": message_count,
                "created_at": conv["created_at"].isoformat(),
                "updated_at": conv["updated_at"].isoformat(),
                "last_message": messages[-1]["content"][:100] if messages else ""
            })
        
        return {
            "user_email": user.email,
            "conversations": result,
            "total": len(result)
        }
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))


@app.get("/conversations/{conversation_id}")
async def get_conversation_detail(
    conversation_id: str,
    user: ClerkUser = Depends(require_auth)
):
    """Obtiene el detalle completo de una conversación específica."""
    try:
        # Buscar la conversación
        conversation = mongo.conversations_collection.find_one({
            "_id": conversation_id,
            "session_id": user.user_id  # Verificar que pertenece al usuario
        })
        
        if not conversation:
            raise HTTPException(status_code=404, detail="Conversación no encontrada")
        
        messages = conversation.get("messages", [])
        
        return {
            "conversation_id": str(conversation["_id"]),
            "session_id": conversation["session_id"],
            "user_email": user.email,
            "messages": messages,
            "message_count": len(messages),
            "created_at": conversation["created_at"].isoformat(),
            "updated_at": conversation["updated_at"].isoformat()
        }
    except HTTPException:
        raise
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))


@app.post("/conversations/{conversation_id}/ask")
async def ask_in_conversation(
    conversation_id: str,
    question_request: QuestionRequest,
    user: ClerkUser = Depends(require_auth)
):
    """
    Hace una pregunta dentro de una conversación existente.
    Mantiene todo el contexto de mensajes previos.
    """
    try:
        # Verificar que la conversación existe y pertenece al usuario
        conversation = mongo.conversations_collection.find_one({
            "_id": conversation_id,
            "session_id": user.user_id
        })
        
        if not conversation:
            raise HTTPException(status_code=404, detail="Conversación no encontrada")
        
        question = question_request.question
        category = normalize_category(question_request.category)
        format_type = question_request.format.lower()
        
        if format_type not in ["html", "plain", "both"]:
            raise HTTPException(status_code=400, detail="Invalid format")
        
        # Obtener vectorstore y buscar documentos relevantes
        vectorstore = get_or_create_vectorstore(category)
        retriever = vectorstore.as_retriever(
            search_type="mmr",
            search_kwargs={"k": 2, "fetch_k": 10}
        )
        
        relevant_docs = retriever.invoke(question)
        context = "\n\n".join([doc.page_content for doc in relevant_docs])
        
        # Extraer fuentes
        sources_info = []
        for doc in relevant_docs:
            fuente = doc.metadata.get("source", "Fuente desconocida")
            pagina = doc.metadata.get("page", "Página no especificada")
            sources_info.append(f"{fuente} (pág. {pagina})")
        
        sources_html = "".join(f"<li>{source}</li>" for source in sources_info)
        sources_plain = "\n".join(f"• {source}" for source in sources_info)
        
        # ⭐ CLAVE: Obtener TODO el historial de la conversación
        history = mongo.get_conversation_history(user.user_id, limit=100)
        conversation_context = format_conversation_context(history)
        
        result = {
            "question": question,
            "category": category,
            "format": format_type,
            "conversation_id": conversation_id,
            "authenticated": True,
            "user_email": user.email
        }
        
        # Obtener prompts personalizados
        html_prompt_template, plain_prompt_template = get_prompts_for_category(category)
        
        if format_type in ["html", "both"]:
            # ⭐ CLAVE: Combinar contexto conversacional + documentos
            full_context = f"{conversation_context}\n\nINFORMACIÓN DE DOCUMENTOS:\n{context}"
            prompt = html_prompt_template.format(context=full_context, question=question)
            answer = llm.invoke(prompt).content
            result["answer"] = answer
            result["sources"] = f"<ul>{sources_html}</ul>"
            
            # Guardar en MongoDB con metadata
            metadata = {
                "category": category,
                "format": "html",
                "conversation_id": conversation_id,
                **get_user_metadata(user)
            }
            add_to_conversation(user.user_id, "user", question, metadata)
            add_to_conversation(user.user_id, "assistant", answer, metadata)
        
        if format_type in ["plain", "both"]:
            full_context = f"{conversation_context}\n\nINFORMACIÓN DE DOCUMENTOS:\n{context}"
            prompt = plain_prompt_template.format(context=full_context, question=question)
            answer_plain = llm.invoke(prompt).content
            result["answer_plain"] = answer_plain
            result["sources_plain"] = sources_plain
            
            if format_type == "plain":
                metadata = {
                    "category": category,
                    "format": "plain",
                    "conversation_id": conversation_id,
                    **get_user_metadata(user)
                }
                add_to_conversation(user.user_id, "user", question, metadata)
                add_to_conversation(user.user_id, "assistant", answer_plain, metadata)
        
        return result
        
    except HTTPException:
        raise
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))


@app.post("/conversations/new")
async def create_new_conversation(
    user: ClerkUser = Depends(require_auth)
):
    """Crea una nueva conversación vacía para el usuario."""
    try:
        from bson import ObjectId
        from datetime import datetime
        
        conversation_id = str(ObjectId())
        
        new_conversation = {
            "_id": conversation_id,
            "session_id": user.user_id,
            "messages": [],
            "created_at": datetime.utcnow(),
            "updated_at": datetime.utcnow(),
            "message_count": 0
        }
        
        mongo.conversations_collection.insert_one(new_conversation)
        
        return {
            "conversation_id": conversation_id,
            "session_id": user.user_id,
            "user_email": user.email,
            "created_at": new_conversation["created_at"].isoformat(),
            "message": "Nueva conversación creada"
        }
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))


@app.on_event("shutdown")
def cleanup():
    """Limpieza al cerrar."""
    vectorstore_cache.clear()
    close_mongo_connection()
    print("👋 Sistema cerrado correctamente")
