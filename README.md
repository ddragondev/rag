### OpenAI PDF RAG with LangChain

Ask ChatGPT to answer questions based on your PDF files with optimized performance.

#### Features

- 🚀 **Persistent vector cache** - 84% faster responses with Chroma persistence
- 🎯 **Format selection** - Choose HTML, plain text, or both formats
- 🌊 **Streaming responses** - Progressive loading for better UX
- 📚 **Category-based organization** - Organize PDFs by topic
- ⚡ **Smart caching** - Automatic vectorstore management

#### How does this work

This API uses GPT-4o for inference and Chroma database for storing embeddings of PDF files. PDFs are split into chunks, embedded, and stored in a persistent vector database. When a question is asked, we use LangChain's Retriever to perform similarity search, then pass the relevant context to ChatGPT for answering.

**Key optimizations:**

- Vector embeddings are cached on disk (only generated once)
- Retriever limits results to top 3 most relevant documents
- Format parameter allows requesting only needed output format
- Streaming endpoint for progressive response delivery

#### How to run

Install dependencies:

```bash
# Opción 1: Instalar desde requirements.txt (recomendado)
pip install -r requirements.txt

# Opción 2: Instalar manualmente
pip install langchain langchain-community langchain-openai langchain-chroma fastapi uvicorn pypdf python-dotenv pydantic cryptography
```

Add `OPENAI_API_KEY` to `.env` and run:

```bash
uvicorn main:app --reload --host 0.0.0.0 --port 8000
```

#### API Usage

**1. Ask endpoint (complete response)**

```bash
# HTML format only (faster)
curl -X POST http://localhost:8000/ask \
  -H "Content-Type: application/json" \
  -d '{
    "question": "¿Qué es la mecánica de rocas?",
    "category": "geomecanica",
    "format": "html"
  }'

# Plain text only (faster)
curl -X POST http://localhost:8000/ask \
  -H "Content-Type: application/json" \
  -d '{
    "question": "¿Qué es la mecánica de rocas?",
    "category": "geomecanica",
    "format": "plain"
  }'

# Both formats (slower, 2 LLM calls)
curl -X POST http://localhost:8000/ask \
  -H "Content-Type: application/json" \
  -d '{
    "question": "¿Qué es la mecánica de rocas?",
    "category": "geomecanica",
    "format": "both"
  }'
```

**2. Streaming endpoint**

```bash
curl -N -X POST http://localhost:8000/ask-stream \
  -H "Content-Type: application/json" \
  -d '{
    "question": "¿Qué es la fortificación?",
    "category": "geomecanica",
    "format": "plain"
  }'
```

**3. List categories**

```bash
curl http://localhost:8000/categories
```

#### Response formats

**HTML format (`format="html"`):**

```json
{
  "question": "...",
  "category": "...",
  "format": "html",
  "answer": "<p class='text-lg'>La mecánica de rocas es...</p>",
  "sources": "<ul><li>doc.pdf (pág. 5)</li></ul>"
}
```

**Plain text format (`format="plain"`):**

```json
{
  "question": "...",
  "category": "...",
  "format": "plain",
  "answer_plain": "La mecánica de rocas es una disciplina...",
  "sources_plain": "• doc.pdf (pág. 5)\n• doc2.pdf (pág. 12)"
}
```

**Both formats (`format="both"`):**

```json
{
  "question": "...",
  "category": "...",
  "format": "both",
  "answer": "<p>HTML response...</p>",
  "answer_plain": "Plain text response...",
  "sources": "<ul><li>...</li></ul>",
  "sources_plain": "• ..."
}
```

#### Interactive Documentation

- **Swagger UI**: http://localhost:8000/docs
- **ReDoc**: http://localhost:8000/redoc

#### Performance Tips

- Use `format="html"` or `format="plain"` for ~50% faster responses
- First query per category is slower (generates embeddings)
- Subsequent queries are 84% faster (uses cached embeddings)
- Use streaming endpoint for better perceived performance

#### Project Structure

```
├── main.py                      # FastAPI application
├── docs/                        # PDF documents organized by category
│   └── geomecanica/            # Example category
├── chroma_db/                   # Persistent vector database (auto-generated)
├── .env                         # Environment variables (OPENAI_API_KEY)
├── test_format_optimization.py  # Format parameter tests
└── API_EXAMPLES.md             # Detailed usage examples
```

#### Example output

```
Question: ¿Qué es la fortificación en minería?

Format: plain
Time: 5.2s (with cache)

Answer:
La fortificación en minería es el conjunto de técnicas y elementos estructurales
utilizados para asegurar la estabilidad de las excavaciones subterráneas y
superficiales...

Sources:
• docs/geomecanica/7.fortificacion-acunadura.pdf (pág. 3)
• docs/geomecanica/G5FortificacionAcunadura.pdf (pág. 1)
```
