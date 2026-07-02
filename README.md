# SHL Assessment Recommender

A conversational AI agent that helps hiring managers find the right SHL assessments through natural dialogue.

## Architecture

```
├── backend/          # FastAPI service (Python)
│   ├── app/
│   │   ├── agent/    # Orchestrator, behaviors, guardrails, prompts
│   │   ├── catalog/  # Assessment data models and loader
│   │   ├── llm/      # Gemini client wrapper
│   │   ├── retrieval/# FAISS vector store + semantic search
│   │   ├── routes/   # /health and /chat endpoints
│   │   └── schemas/  # Pydantic request/response models
│   ├── data/         # Catalog JSON + FAISS index
│   └── scripts/      # Index builder + evaluation
├── frontend/         # React SPA (Vite + TypeScript + Tailwind)
└── docs/             # Assignment + approach document
```

## Quick Start

### Backend

```bash
cd backend
python -m venv venv
source venv/bin/activate
pip install -r requirements.txt

# Set your Gemini API key
echo "GEMINI_API_KEY=your-key-here" > .env

# Build the FAISS index (first time only)
python -m scripts.build_index

# Run the server
uvicorn app.main:app --reload --port 8000
```

### Frontend

```bash
cd frontend
npm install
npm run dev
```

The frontend runs at http://localhost:3000 and proxies API calls to the backend.

## API Endpoints

### GET /health
Returns `{"status": "ok"}` when the service is ready.

### POST /chat
Stateless conversational endpoint.

**Request:**
```json
{
  "messages": [
    {"role": "user", "content": "Hiring a Java developer"},
    {"role": "assistant", "content": "What seniority level?"},
    {"role": "user", "content": "Mid-level, 4 years experience"}
  ]
}
```

**Response:**
```json
{
  "reply": "Here are 5 assessments for a mid-level Java developer.",
  "recommendations": [
    {"name": "Java 8 (New)", "url": "https://www.shl.com/...", "test_type": "K"},
    {"name": "OPQ32r", "url": "https://www.shl.com/...", "test_type": "P"}
  ],
  "end_of_conversation": true
}
```

## Design Decisions

| Decision | Rationale |
|----------|-----------|
| Gemini 2.0 Flash | Free tier, fast inference, structured output |
| FAISS + MiniLM-L6 | Lightweight semantic search, <100ms retrieval |
| Two LLM calls/req | Intent (~2s) + generation (~5-8s) = well under 30s |
| Hard-coded intent rules | Deterministic routing for clear patterns |
| Post-gen URL validation | Zero hallucinated URLs in responses |

## Evaluation

```bash
cd backend
python -m scripts.evaluate
```

Reports Mean Recall@10 across test traces.
