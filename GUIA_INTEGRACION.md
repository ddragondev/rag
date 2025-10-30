# 🔧 Guía de Integración - Parámetro `format`

## 🌐 Frontend Web (React/Vue/Angular)

### React Example

```jsx
import { useState } from "react";

function QuestionAsker() {
  const [question, setQuestion] = useState("");
  const [answer, setAnswer] = useState("");
  const [loading, setLoading] = useState(false);

  const askQuestion = async () => {
    setLoading(true);

    const response = await fetch("http://localhost:8000/ask", {
      method: "POST",
      headers: { "Content-Type": "application/json" },
      body: JSON.stringify({
        question: question,
        category: "geomecanica",
        format: "html", // ⚡ Solo HTML para web
      }),
    });

    const data = await response.json();
    setAnswer(data.answer); // HTML listo para renderizar
    setLoading(false);
  };

  return (
    <div>
      <input
        value={question}
        onChange={(e) => setQuestion(e.target.value)}
        placeholder="Haz una pregunta..."
      />
      <button onClick={askQuestion} disabled={loading}>
        {loading ? "Consultando..." : "Preguntar"}
      </button>

      {answer && (
        <div
          className="prose max-w-none"
          dangerouslySetInnerHTML={{ __html: answer }}
        />
      )}
    </div>
  );
}
```

### Vue Example

```vue
<template>
  <div>
    <input v-model="question" placeholder="Haz una pregunta..." />
    <button @click="askQuestion" :disabled="loading">
      {{ loading ? "Consultando..." : "Preguntar" }}
    </button>

    <div v-if="answer" v-html="answer" class="prose"></div>
  </div>
</template>

<script>
export default {
  data() {
    return {
      question: "",
      answer: "",
      loading: false,
    };
  },
  methods: {
    async askQuestion() {
      this.loading = true;

      const response = await fetch("http://localhost:8000/ask", {
        method: "POST",
        headers: { "Content-Type": "application/json" },
        body: JSON.stringify({
          question: this.question,
          category: "geomecanica",
          format: "html", // ⚡ Solo HTML
        }),
      });

      const data = await response.json();
      this.answer = data.answer;
      this.loading = false;
    },
  },
};
</script>
```

---

## 🖥️ CLI / Terminal Apps (Python)

### Simple CLI

```python
#!/usr/bin/env python3
import requests
import sys

def ask(question, category='geomecanica'):
    """CLI para hacer preguntas en texto plano."""

    response = requests.post('http://localhost:8000/ask', json={
        'question': question,
        'category': category,
        'format': 'plain'  # ⚡ Solo texto plano para terminal
    })

    if response.status_code != 200:
        print(f"Error: {response.status_code}")
        return

    data = response.json()

    print("\n" + "="*70)
    print("RESPUESTA:")
    print("="*70)
    print(data['answer_plain'])

    print("\n" + "="*70)
    print("FUENTES:")
    print("="*70)
    print(data['sources_plain'])

if __name__ == '__main__':
    if len(sys.argv) < 2:
        print("Uso: python cli.py 'tu pregunta aquí'")
        sys.exit(1)

    question = ' '.join(sys.argv[1:])
    ask(question)
```

**Uso:**

```bash
python cli.py "¿Qué es la fortificación?"
```

### Rich CLI (con colores)

```python
#!/usr/bin/env python3
import requests
import sys
from rich.console import Console
from rich.markdown import Markdown
from rich.panel import Panel

console = Console()

def ask(question, category='geomecanica'):
    """CLI avanzada con Rich."""

    with console.status("[bold green]Consultando...", spinner="dots"):
        response = requests.post('http://localhost:8000/ask', json={
            'question': question,
            'category': category,
            'format': 'plain'  # ⚡ Texto plano
        })

    if response.status_code != 200:
        console.print(f"[red]Error: {response.status_code}[/red]")
        return

    data = response.json()

    # Mostrar pregunta
    console.print(Panel(f"[bold cyan]{question}[/bold cyan]", title="Pregunta"))

    # Mostrar respuesta
    console.print("\n[bold green]Respuesta:[/bold green]")
    console.print(data['answer_plain'])

    # Mostrar fuentes
    console.print(f"\n[bold yellow]Fuentes:[/bold yellow]")
    console.print(data['sources_plain'])

if __name__ == '__main__':
    if len(sys.argv) < 2:
        console.print("[red]Uso:[/red] python rich_cli.py 'tu pregunta'")
        sys.exit(1)

    question = ' '.join(sys.argv[1:])
    ask(question)
```

**Instalación:**

```bash
pip install rich
```

---

## 📊 Backend APIs (FastAPI/Flask)

### FastAPI Proxy

```python
from fastapi import FastAPI, HTTPException
from pydantic import BaseModel
import httpx

app = FastAPI()

class Question(BaseModel):
    question: str

@app.post("/ask-html")
async def ask_html(q: Question):
    """Endpoint que solo devuelve HTML."""
    async with httpx.AsyncClient() as client:
        response = await client.post(
            'http://localhost:8000/ask',
            json={
                'question': q.question,
                'category': 'geomecanica',
                'format': 'html'  # ⚡ Solo HTML
            },
            timeout=120.0
        )

    if response.status_code != 200:
        raise HTTPException(status_code=response.status_code)

    return response.json()

@app.post("/ask-text")
async def ask_text(q: Question):
    """Endpoint que solo devuelve texto plano."""
    async with httpx.AsyncClient() as client:
        response = await client.post(
            'http://localhost:8000/ask',
            json={
                'question': q.question,
                'category': 'geomecanica',
                'format': 'plain'  # ⚡ Solo texto
            },
            timeout=120.0
        )

    if response.status_code != 200:
        raise HTTPException(status_code=response.status_code)

    return response.json()
```

### Flask Wrapper

```python
from flask import Flask, request, jsonify
import requests

app = Flask(__name__)

@app.route('/ask', methods=['POST'])
def ask():
    """Wrapper de Flask sobre la API RAG."""
    data = request.get_json()
    question = data.get('question')
    format_type = data.get('format', 'html')  # Default a HTML para web

    response = requests.post('http://localhost:8000/ask', json={
        'question': question,
        'category': 'geomecanica',
        'format': format_type  # ⚡ Formato dinámico
    })

    return jsonify(response.json())

if __name__ == '__main__':
    app.run(port=5000)
```

---

## 📧 Integración con Email

### Enviar respuestas por email

```python
import smtplib
from email.mime.text import MIMEText
from email.mime.multipart import MIMEMultipart
import requests

def send_answer_email(question, recipient):
    """Envía respuesta por email."""

    # Obtener respuesta en HTML para email
    response = requests.post('http://localhost:8000/ask', json={
        'question': question,
        'category': 'geomecanica',
        'format': 'html'  # ⚡ HTML para email
    })

    data = response.json()

    # Crear mensaje
    msg = MIMEMultipart('alternative')
    msg['Subject'] = f"Respuesta: {question[:50]}..."
    msg['From'] = "noreply@example.com"
    msg['To'] = recipient

    # Parte HTML
    html = f"""
    <html>
      <body>
        <h2>Pregunta:</h2>
        <p>{question}</p>

        <h2>Respuesta:</h2>
        {data['answer']}

        <h2>Fuentes:</h2>
        {data['sources']}
      </body>
    </html>
    """

    part = MIMEText(html, 'html')
    msg.attach(part)

    # Enviar (configura tu SMTP)
    # with smtplib.SMTP('smtp.gmail.com', 587) as server:
    #     server.starttls()
    #     server.login('user', 'password')
    #     server.send_message(msg)

    print(f"Email enviado a {recipient}")

# Uso
send_answer_email("¿Qué es el RMR?", "user@example.com")
```

---

## 🤖 Chatbot Integration

### Discord Bot

```python
import discord
from discord.ext import commands
import requests

bot = commands.Bot(command_prefix='!')

@bot.command()
async def ask(ctx, *, question):
    """Comando !ask para hacer preguntas."""

    await ctx.send("🔍 Consultando...")

    response = requests.post('http://localhost:8000/ask', json={
        'question': question,
        'category': 'geomecanica',
        'format': 'plain'  # ⚡ Texto plano para Discord
    })

    if response.status_code != 200:
        await ctx.send("❌ Error al consultar")
        return

    data = response.json()

    # Discord tiene límite de 2000 caracteres
    answer = data['answer_plain'][:1900]

    embed = discord.Embed(
        title="Respuesta",
        description=answer,
        color=discord.Color.blue()
    )
    embed.add_field(
        name="Fuentes",
        value=data['sources_plain'][:1024],
        inline=False
    )

    await ctx.send(embed=embed)

bot.run('YOUR_BOT_TOKEN')
```

### Slack Bot

```python
from slack_bolt import App
import requests

app = App(token="YOUR_SLACK_BOT_TOKEN")

@app.command("/ask")
def handle_ask(ack, command, say):
    """Comando /ask en Slack."""
    ack()

    question = command['text']

    response = requests.post('http://localhost:8000/ask', json={
        'question': question,
        'category': 'geomecanica',
        'format': 'plain'  # ⚡ Texto plano para Slack
    })

    if response.status_code != 200:
        say("❌ Error al consultar")
        return

    data = response.json()

    say({
        "blocks": [
            {
                "type": "section",
                "text": {
                    "type": "mrkdwn",
                    "text": f"*Pregunta:* {question}"
                }
            },
            {
                "type": "section",
                "text": {
                    "type": "mrkdwn",
                    "text": f"*Respuesta:*\n{data['answer_plain']}"
                }
            },
            {
                "type": "section",
                "text": {
                    "type": "mrkdwn",
                    "text": f"*Fuentes:*\n{data['sources_plain']}"
                }
            }
        ]
    })

if __name__ == "__main__":
    app.start(port=3000)
```

---

## 📱 Mobile Apps

### Swift (iOS)

```swift
import Foundation

struct QuestionRequest: Codable {
    let question: String
    let category: String
    let format: String
}

struct AnswerResponse: Codable {
    let question: String
    let category: String
    let format: String
    let answer: String?
    let answerPlain: String?
    let sources: String?
    let sourcesPlain: String?

    enum CodingKeys: String, CodingKey {
        case question, category, format, answer, sources
        case answerPlain = "answer_plain"
        case sourcesPlain = "sources_plain"
    }
}

func askQuestion(question: String, completion: @escaping (String?) -> Void) {
    let url = URL(string: "http://localhost:8000/ask")!
    var request = URLRequest(url: url)
    request.httpMethod = "POST"
    request.setValue("application/json", forHTTPHeaderField: "Content-Type")

    let body = QuestionRequest(
        question: question,
        category: "geomecanica",
        format: "plain"  // ⚡ Texto plano para móvil
    )

    request.httpBody = try? JSONEncoder().encode(body)

    URLSession.shared.dataTask(with: request) { data, response, error in
        guard let data = data else {
            completion(nil)
            return
        }

        let answer = try? JSONDecoder().decode(AnswerResponse.self, from: data)
        completion(answer?.answerPlain)
    }.resume()
}
```

### Kotlin (Android)

```kotlin
import kotlinx.coroutines.*
import okhttp3.*
import org.json.JSONObject

suspend fun askQuestion(question: String): String? = withContext(Dispatchers.IO) {
    val client = OkHttpClient()

    val json = JSONObject().apply {
        put("question", question)
        put("category", "geomecanica")
        put("format", "plain")  // ⚡ Texto plano para móvil
    }

    val body = RequestBody.create(
        MediaType.parse("application/json"),
        json.toString()
    )

    val request = Request.Builder()
        .url("http://localhost:8000/ask")
        .post(body)
        .build()

    val response = client.newCall(request).execute()
    val responseData = JSONObject(response.body()?.string() ?: "")

    responseData.optString("answer_plain")
}
```

---

## 💡 Recomendaciones por Plataforma

| Plataforma           | Formato Recomendado | Razón                                |
| -------------------- | ------------------- | ------------------------------------ |
| Web (React/Vue)      | `html`              | Renderizado directo en DOM           |
| Mobile (iOS/Android) | `plain`             | Texto simple, menos procesamiento    |
| CLI/Terminal         | `plain`             | Salida estándar, fácil procesamiento |
| Discord/Slack        | `plain`             | Límites de caracteres, markdown      |
| Email                | `html`              | Mejor presentación visual            |
| API Backend          | Depende del cliente | Flexible según necesidad             |
| Logs/Analytics       | `plain`             | Fácil parsing y análisis             |

---

**Última actualización:** 23 de octubre de 2025
