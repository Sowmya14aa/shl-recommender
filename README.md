# SHL Assessment Recommender 🎯

A conversational AI agent that helps hiring managers find relevant SHL assessments through natural dialogue. Built as part of the SHL Labs AI Intern take-home assignment.

---

## What it does

Instead of manually searching through the SHL catalog, users describe the role they are hiring for in plain language. The system asks follow-up questions when needed and recommends relevant assessments based on the conversation.

The agent can:

- ask ONE clarifying question when the query is vague
- recommend 1–10 relevant SHL assessments with real catalog URLs
- update recommendations when requirements change during the conversation
- compare assessments using only catalog information
- refuse unrelated or unsupported requests

---

## Live API

```text
Base URL: https://sowmyaindurthi-shl-recommender.hf.space
Health:   https://sowmyaindurthi-shl-recommender.hf.space/health
Chat:     https://sowmyaindurthi-shl-recommender.hf.space/chat
Docs:     https://sowmyaindurthi-shl-recommender.hf.space/docs
```

---

## Example Conversations

### Vague query → clarification

```text
User: I need an assessment
Bot: What role or skill are you looking to assess?
```

---

### Specific role → recommendations

```text
User: I am hiring a mid-level Java developer

Bot:
1. Java 8 (New)
2. Core Java (Advanced Level)
3. OPQ32r
```

---

### Refinement

```text
User: Also add personality assessments

Bot:
Updated recommendations with personality-based assessments included.
```

---

### Comparison

```text
User: What is the difference between OPQ and MQ?

Bot:
OPQ measures workplace behavioral style while MQ focuses on workplace motivation and drivers.
```

---

### Off-topic refusal

```text
User: What is the best hiring strategy for startups?

Bot:
I can only help with SHL assessment recommendations.
```

---

## Tech Stack

| Component | Tool | Why it was chosen |
|---|---|---|
| Backend API | FastAPI | Lightweight, simple to structure, automatic docs and validation |
| LLM | Groq (LLaMA 3.3 70B) | Fast responses and free API access |
| Embeddings | sentence-transformers (`all-MiniLM-L6-v2`) | Local semantic embeddings without API cost |
| Vector Search | FAISS | Lightweight local vector similarity search |
| Web Scraping | BeautifulSoup + requests | Simple and easy to debug |
| Deployment | HuggingFace Spaces (Docker) | Better memory support for PyTorch models |

---

## Why Certain Tools Were Avoided

| Tool | Reason |
|---|---|
| Render free tier | Memory limitations for PyTorch models |
| Gemini free tier | API quota unavailable in India |
| LangChain | Added unnecessary complexity for this assignment |
| Redis/PostgreSQL | Not needed because the API is stateless |
| ChromaDB | FAISS was simpler for this project size |

---

## Project Structure

```text
shl-recommender/
│
├── app/
│   ├── __init__.py
│   ├── main.py
│   ├── schemas.py
│   ├── chat_handler.py
│   ├── retriever.py
│   └── prompts.py
│
├── data/
│   ├── scraper.py
│   ├── fix_descriptions.py
│   ├── build_index.py
│   └── catalog.json
│
├── startup.py
├── Dockerfile
├── requirements.txt
└── README.md
```

---

## How it works

### 1. Data Collection

The scraper visits the SHL catalog pages and extracts assessment names, URLs, descriptions, and metadata. The processed catalog is stored locally as `catalog.json`.

---

### 2. Embedding Generation

Each assessment's name, description, and metadata are combined into a single text string and converted into embeddings using the `all-MiniLM-L6-v2` model.

---

### 3. Vector Search

When a user sends a message, the conversation is embedded and FAISS retrieves the most semantically relevant assessments from the catalog.

---

### 4. Conversation Logic

The chatbot first checks whether the user has provided enough information. If the request is too broad, it asks a clarification question before recommending assessments.

The system also supports:

- recommendation refinement
- assessment comparison
- refusal handling

---

### 5. Stateless API Design

Every `/chat` request contains the full conversation history. The backend does not store sessions or conversation state.

---

## API Reference

### GET `/health`

```json
{
  "status": "ok"
}
```

---

### POST `/chat`

#### Request

```json
{
  "messages": [
    {
      "role": "user",
      "content": "Hiring a Java developer"
    },
    {
      "role": "assistant",
      "content": "What seniority level?"
    },
    {
      "role": "user",
      "content": "Mid-level with 4 years experience"
    }
  ]
}
```

---

#### Response

```json
{
  "reply": "Here are assessments suitable for a mid-level Java developer.",
  "recommendations": [
    {
      "name": "Java 8 (New)",
      "url": "https://www.shl.com/products/product-catalog/view/java-8-new/",
      "test_type": "K"
    }
  ],
  "end_of_conversation": false
}
```

---

## Schema Rules

- `recommendations` remains empty while clarifying or refusing
- recommendations contain 1–10 items when recommending
- `end_of_conversation` becomes `true` only when the interaction is complete

---

## Local Setup

### 1. Clone Repository

```bash
git clone https://github.com/Sowmya14aa/shl-recommender.git
cd shl-recommender
```

---

### 2. Create Virtual Environment

#### Windows

```powershell
py -m venv venv
venv\Scripts\Activate.ps1
```

#### Mac/Linux

```bash
python3 -m venv venv
source venv/bin/activate
```

---

### 3. Install Dependencies

```bash
pip install -r requirements.txt
```

---

### 4. Configure Environment Variables

Create a `.env` file:

```env
GROQ_API_KEY=your_api_key_here
```

Get a free API key from:

```text
https://console.groq.com
```

---

### 5. Build FAISS Index

```bash
python startup.py
```

---

### 6. Run the Application

```bash
uvicorn app.main:app --reload
```

---

### 7. Open API Docs

```text
http://localhost:8000/docs
```

---

## Design Decisions

### Why FastAPI?

FastAPI is lightweight, beginner-friendly, and provides automatic API documentation and schema validation.

---

### Why FAISS?

FAISS allows fast local semantic search without requiring an external database service.

---

### Why Stateless API Design?

The assignment specifically requires stateless APIs. Including the full conversation in every request keeps the backend simple.

---

### Why Sentence Transformers?

Sentence Transformers provide good semantic retrieval quality locally without depending on external embedding APIs.

---

## Limitations

- recommendations depend on publicly scraped SHL catalog data
- if the SHL website changes, the catalog may need to be scraped again
- free LLM APIs can have rate limits
- HuggingFace free tier may take time to wake after inactivity

---

## Future Improvements

Some improvements that could be added in the future:

- hybrid keyword + semantic retrieval
- reranking retrieved assessments
- caching embeddings
- improved metadata extraction
- frontend UI integration

---

## Assignment Context

Built as part of the SHL Labs AI Intern take-home assignment.

---

## Author

Built by Sowmya.
