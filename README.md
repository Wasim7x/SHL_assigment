# SHL Assessment Recommender

A conversational AI agent that helps hiring managers find the right SHL assessments through natural dialogue. Built with FastAPI + Groq (Llama 3.1) + FAISS semantic search.

## 🚀 Deploy in 5 Minutes

### Option A: Render (Recommended — Free Tier)

1. **Fork/push this repo to GitHub**
2. Go to [render.com](https://render.com) → New → Web Service
3. Connect your GitHub repo, set **Root Directory** to `backend`
4. Settings:
   - **Build Command**: `chmod +x build.sh && ./build.sh`
   - **Start Command**: `uvicorn app.main:app --host 0.0.0.0 --port $PORT`
   - **Environment**: Add `GROQ_API_KEY` (get free key at [console.groq.com](https://console.groq.com/keys))
5. Deploy! Your URL will be `https://your-app.onrender.com`

### Option B: Railway (Free $5 credit)

1. Push repo to GitHub
2. Go to [railway.app](https://railway.app) → New Project → Deploy from GitHub
3. Set **Root Directory** to `backend`
4. Add env var: `GROQ_API_KEY=gsk_your_key`
5. Railway auto-detects the Dockerfile and deploys

### Option C: Hugging Face Spaces (Free, Docker)

1. Create a new Space at [huggingface.co/spaces](https://huggingface.co/spaces)
2. Choose **Docker** as the SDK
3. Upload the `backend/` folder contents
4. Add `GROQ_API_KEY` as a Secret in Settings
5. The Space will build and deploy automatically

### Option D: Fly.io (Free tier)

```bash
cd backend
fly launch --no-deploy
fly secrets set GROQ_API_KEY=gsk_your_key
fly deploy
```

---

## 📋 API Endpoints

### GET /health
```bash
curl https://your-app.onrender.com/health
# → {"status": "ok"}
```

### POST /chat
```bash
curl -X POST https://shl-assigment-mc2f.onrender.com/chat \
  -H "Content-Type: application/json" \
  -d '{
    "messages": [
      {"role": "user", "content": "I need to hire a Java developer who works with stakeholders"},
      {"role": "assistant", "content": "What seniority level are you looking for?"},
      {"role": "user", "content": "Mid-level, around 4 years experience"}
    ]
  }'
```

**Response:**
```json
{
  "reply": "Here are 5 assessments for a mid-level Java developer with stakeholder skills.",
  "recommendations": [
    {"name": "Java 8 (New)", "url": "https://www.shl.com/solutions/products/product-catalog/view/java-8-new/", "test_type": "K"},
    {"name": "OPQ32r (Occupational Personality Questionnaire)", "url": "https://www.shl.com/solutions/products/product-catalog/view/opq32r/", "test_type": "P"}
  ],
  "end_of_conversation": true
}
```

---

## 🏗️ Architecture

```
backend/
├── app/
│   ├── main.py              # FastAPI app, CORS, lifespan
│   ├── config.py            # Settings from env vars
│   ├── routes/
│   │   ├── health.py        # GET /health
│   │   └── chat.py          # POST /chat
│   ├── schemas/             # Pydantic request/response models
│   ├── agent/
│   │   ├── orchestrator.py  # Intent classify → dispatch
│   │   ├── behaviors.py     # clarify/recommend/refine/compare/refuse
│   │   ├── guardrails.py    # Injection detection, URL validation
│   │   └── prompts.py       # All LLM prompt templates
│   ├── retrieval/
│   │   ├── embeddings.py    # MiniLM-L6-v2 encoder
│   │   ├── vector_store.py  # FAISS index
│   │   └── retriever.py     # Semantic search pipeline
│   ├── catalog/             # Assessment data model + loader
│   └── llm/
│       └── gemini.py        # Groq/Llama client (OpenAI-compatible)
├── data/
│   ├── catalog.json         # 124 SHL assessments
│   └── faiss_index/         # Pre-built vector index
├── Dockerfile               # Production container
├── Procfile                 # Render/Heroku process file
├── build.sh                 # Build script (model download + index)
└── requirements.txt
```

## 🔑 Get Your Free Groq API Key

1. Go to [console.groq.com](https://console.groq.com)
2. Sign up (no credit card needed)
3. Go to API Keys → Create API Key
4. Copy the key starting with `gsk_...`

## 💡 Cold Start

The free tier on Render/Railway has a **cold start delay** (~30-60 seconds) after inactivity. The SHL evaluator allows up to **2 minutes** for the first `/health` call. After the first request, subsequent responses are fast (5-15 seconds).

## Local Development

```bash
cd backend
python -m venv venv && source venv/bin/activate
pip install -r requirements.txt
echo "GROQ_API_KEY=gsk_your_key" > .env
python -m scripts.build_index
uvicorn app.main:app --reload --port 8000
```
