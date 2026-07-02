# Approach Document — SHL Conversational Assessment Recommender

## System Design

### Architecture
The system comprises a **FastAPI backend** and a **React frontend** deployed as separate services on Render. The backend exposes a stateless `/chat` endpoint that processes full conversation histories using a three-stage pipeline: **guardrails → intent classification → behavior dispatch**.

### Agent Design
The orchestrator classifies each user turn into one of five intents: CLARIFY, RECOMMEND, REFINE, COMPARE, or REFUSE. Hard-coded rules handle unambiguous cases (vague turn-1 queries → CLARIFY, turn 7+ → force RECOMMEND, off-topic → REFUSE), with Gemini 2.0 Flash as fallback for ambiguous inputs. This hybrid approach ensures deterministic behavior on clear patterns while handling nuance through the LLM.

### Retrieval Strategy
1. **Catalog**: 100+ SHL Individual Test Solutions scraped and stored as a committed JSON file with structured metadata (name, test_type, category, description, duration, languages, job_levels).
2. **Embedding**: `all-MiniLM-L6-v2` encodes each assessment's composite text (name + category + description + type + duration) into 384-dim normalized vectors.
3. **FAISS Index**: Pre-built `IndexFlatIP` provides <100ms cosine-similarity search at runtime.
4. **Re-ranking**: Gemini selects the final 1–10 assessments from the top 15 FAISS candidates, grounding selections in conversation context.

### Prompt Design
Prompts are structured with role separation: a system prompt enforces scope rules, then task-specific templates (query builder, re-ranker, comparator) use JSON-mode output for reliable parsing. All prompts instruct the model to ONLY use catalog data — never general knowledge.

### Guardrails & Safety
- **URL validation**: Every recommendation is post-checked against the catalog URL set. Hallucinated URLs are filtered before response.
- **Turn cap enforcement**: Hard limit at 8 turns; agent forces recommendations at turn 7.
- **Injection detection**: Regex patterns catch common prompt-injection attempts.
- **Scope boundary**: Off-topic keyword detection with assessment-context override (prevents false positives).

## Evaluation Approach

### Metrics
- **Recall@10**: Primary metric — fraction of expected assessments appearing in recommendations.
- **Schema compliance**: Automated validation that every response matches the required JSON schema.
- **Behavior probes**: Binary assertions for key behaviors (refuses off-topic, doesn't recommend on vague turn-1, honors edits).

### What Didn't Work
- **Single-call approach**: Combining intent classification with response generation in one LLM call caused intent confusion on edge cases. Splitting into two calls added ~2s latency but dramatically improved routing accuracy.
- **Pure embedding search without re-ranking**: FAISS alone surfaced relevant but not optimally ordered results. The Gemini re-ranking step improved Recall@10 by filtering candidates that were semantically similar but contextually wrong.
- **Overly aggressive clarification**: Early versions asked 3-4 questions before recommending. Reducing to 1-2 targeted questions per turn and accepting partial context improved both user experience and evaluation scores.

## Tools Used
- **Claude Code** (AI-assisted coding): Architecture design, code scaffolding, prompt iteration
- **Google Gemini 2.0 Flash**: Runtime LLM for intent classification and generation
- **sentence-transformers + FAISS**: Semantic retrieval pipeline
- **Render**: Deployment platform (free tier)

## Stack Justification
| Component | Choice | Reason |
|-----------|--------|--------|
| LLM | Gemini 2.0 Flash | Free tier, fast (~2-5s), structured output support |
| Embeddings | all-MiniLM-L6-v2 | Lightweight (80MB), 384-dim, fast inference |
| Vector Store | FAISS | In-memory, no external dependency, <100ms search |
| Backend | FastAPI | Async-native, auto-generated docs, Pydantic validation |
| Frontend | React + Vite + Tailwind | Fast development, good DX, responsive by default |
