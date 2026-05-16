# SHL Assessment Recommender 🎯

A conversational AI agent that helps hiring managers find relevant SHL assessments through natural dialogue. Built as part of the SHL Labs AI Intern take-home assignment.

---

## What it does

This project is a conversational recommendation system for SHL assessments.

Instead of manually searching through the SHL catalog, users can describe the type of role they are hiring for in natural language. The system asks follow-up questions when needed and recommends relevant assessments based on the conversation.

The chatbot can:

- ask clarification questions for vague hiring requirements
- recommend relevant SHL assessments
- update recommendations when requirements change
- compare assessments using catalog information
- refuse unrelated or unsupported requests

---

## Example Conversations

### Clarification Flow

```text
User: I need an assessment
Assistant: Could you tell me the role you are hiring for?
```

### Recommendation Flow

```text
User: I am hiring a mid-level Java developer
Assistant: Here are assessments suitable for a mid-level Java developer:
1. Java 8 (New)
2. Core Java (Advanced Level)
3. OPQ32r
```

### Refinement Flow

```text
User: Also include personality assessments
Assistant: Updated recommendations with personality-based assessments:
1. Java 8 (New)
2. OPQ32r
3. Occupational Personality Questionnaire
```

### Comparison Flow

```text
User: What is the difference between OPQ and GSA?
Assistant: OPQ focuses on personality and behavioral preferences, while GSA measures general cognitive ability and reasoning skills.
```

---

## Tech Stack

| Component | Technology |
|---|---|
| Backend API | FastAPI |
| LLM | Groq / Gemini / OpenAI |
| Embeddings | sentence-transformers |
| Vector Search | FAISS |
| Web Scraping | BeautifulSoup + requests |
| Data Handling | Pandas |
| Deployment | Render |

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
│   ├── catalog.json
│   └── faiss_index/
│
├── tests/
│   └── test_conversations.py
│
├── .env
├── .env.example
├── requirements.txt
├── runtime.txt
└── README.md
```

---

## System Workflow

### 1. Catalog Collection

The SHL product catalog is scraped using BeautifulSoup and requests. Relevant assessment information is extracted and stored in a structured JSON format.

Collected fields include:

- assessment name
- URL
- description
- test type
- skills
- duration
- remote testing support
- adaptive support

---

### 2. Embedding Generation

Assessment descriptions and metadata are converted into semantic embeddings using the `all-MiniLM-L6-v2` sentence transformer model.

---

### 3. Vector Search

FAISS is used to store embeddings and retrieve semantically relevant assessments based on the user conversation.

---

### 4. Conversational Logic

The chatbot first checks whether the user has provided enough information. If the query is too broad, it asks follow-up questions before recommending assessments.

The system also supports:

- recommendation refinement
- assessment comparison
- refusal of unsupported queries

The API is stateless, so every request contains the full conversation history.

---

## API Endpoints

### GET `/health`

Returns service health status.

### Response

```json
{
  "status": "ok"
}
```

---

### POST `/chat`

Receives conversation history and returns the next assistant response.

### Request

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

### Response

```json
{
  "reply": "Here are assessments suitable for a mid-level Java developer.",
  "recommendations": [
    {
      "name": "Java 8 (New)",
      "url": "https://www.shl.com/",
      "test_type": "K"
    }
  ],
  "end_of_conversation": false
}
```

---

## Schema Rules

- `recommendations` remains empty while clarifying
- recommendations contain 1–10 assessments when recommending
- `end_of_conversation` becomes `true` only when the interaction is complete

---

## Local Setup

### 1. Clone Repository

```bash
git clone https://github.com/YOUR_USERNAME/shl-recommender.git
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

Create a `.env` file and add:

```env
GROQ_API_KEY=your_api_key
```

---

### 5. Run the Application

```bash
uvicorn app.main:app --reload
```

---

### 6. Open API Docs

```text
http://localhost:8000/docs
```

---

## Design Decisions

### Why FastAPI?

FastAPI was chosen because it is lightweight, easy to structure, and provides automatic API documentation and schema validation.

---

### Why FAISS?

FAISS allows local semantic search without requiring an external database service. Since the catalog size is relatively small, it is fast and simple to manage.

---

### Why Stateless API Design?

The assignment requires stateless APIs. Every request includes the full conversation history, so the backend does not need to store session data.

---

### Why Sentence Transformers?

Sentence Transformers provide good semantic search quality locally without depending on paid embedding APIs.

---

## Limitations

- recommendations depend on publicly scraped SHL catalog data
- if the SHL website changes, the catalog may need to be scraped again
- free LLM APIs can have rate limits
- very vague conversations may require multiple clarification turns

---

## Evaluation Goals

The implementation was built while keeping the assignment evaluation criteria in mind:

- correct schema compliance
- relevant recommendations
- clarification handling
- recommendation refinement
- assessment comparison
- refusal behavior
- hallucination prevention

---

## Future Improvements

Some improvements that could be added in the future:

- hybrid keyword + semantic retrieval
- reranking retrieved assessments
- embedding caching
- improved metadata extraction
- frontend UI integration

---

## Assignment Context

Built as part of the SHL Labs AI Intern take-home assignment.

---

## Author

Built by [Sowmya]
