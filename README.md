# OmniOps AI

**Autonomous enterprise operations platform** — ingests documents, images, and audio into a hybrid-retrieval knowledge base, answers questions through a multi-agent graph, and scores its own answers with an LLM judge.

Built to be *verifiable*: every answer carries citations, a groundedness verdict, and a per-node execution trace. Retrieval quality and hallucination rate are measured by an automated evaluation pipeline rather than asserted.

```
Upload  →  Extract  →  Chunk  →  ┌ Elasticsearch (BM25) ┐
(pdf/img/audio)  (OCR/STT)       └ Qdrant (bge-m3)      ┘
                                          ↓
Question → Planner → Retrieval → Rerank → Answer → Verifier → Report
                                                      ↓
                                          Judge LLM → faithfulness /
                                                      relevance /
                                                      context precision
```

---

## What works today

Every item below was verified end-to-end against the running stack.

**Multimodal ingestion** — text-layer PDFs (pypdf), CSV/text, images (TrOCR OCR **+** BLIP captioning, so an image is searchable by what it *shows* and what it *says*), and audio (faster-whisper transcription). Ingestion runs asynchronously on a Celery worker: upload returns in ~20 ms with `status: queued` instead of blocking ~10 s.

**Hybrid retrieval** — BM25 (Elasticsearch) and dense vectors (BAAI/bge-m3 → Qdrant) fused with Reciprocal Rank Fusion, then re-ranked by a bge-reranker-v2-m3 cross-encoder.

> Why both: asked *"vehicle repairs"* against a document that says *"automobile fleet… brake pads worn"* — zero keyword overlap. BM25 returned nothing; the vector side found it. On a document stuffed with distractor passages, the cross-encoder scored the correct passage **0.988** against **0.001** for the decoys.

**Multi-agent graph** (LangGraph) — a planner picks the retrieval strategy, retrieval fetches and re-ranks, an answerer writes with citations, a verifier judges groundedness, and an optional report agent reformats the result as an executive summary, technical report, Jira ticket, email, or Slack message (which it can post directly to Slack).

**Answer verification** — the verifier combines an LLM groundedness verdict with *mechanical* citation checks. Citations pointing at passages that don't exist force the verdict to "not grounded" regardless of what the LLM says.

**Automated evaluation** — a question set runs through the full agent, then a judge LLM scores faithfulness, answer relevance, and context precision (RAGAS-style), persisted per run.

> The metric discriminates rather than rubber-stamping: on-topic questions scored **1.0** faithfulness, while an off-topic question ("What is the CEO salary?" against an incident-response corpus) correctly scored **0.0** context precision — catching retriever noise.

**Cost & tracing** — every LLM call is metered (calls, tokens, cost, latency, per-model) at a single choke point and exposed at `/api/metrics`. Optional Langfuse tracing switches on by setting two env keys, and is failure-safe: bad Langfuse credentials never break an LLM call.

**Connectors** — GitHub (repos/issues), Slack (list channels, post messages, self-joins a channel when not a member), OpenWeather, NewsAPI.

**Console** (Next.js) — dashboard, document upload with live ingestion status, chat showing the agent execution graph and retrieval inspector, and an evaluation runner.

---

## Stack

| Layer | Choice |
|---|---|
| API | FastAPI · SQLAlchemy · PostgreSQL |
| Agents | LangGraph |
| Retrieval | Elasticsearch (BM25) + Qdrant (dense) + RRF + cross-encoder rerank |
| Models | bge-m3 · bge-reranker-v2-m3 · TrOCR · BLIP · faster-whisper |
| LLM gateway | LiteLLM (provider-agnostic — swap models via one env var) |
| Async | Celery + Redis |
| Frontend | Next.js 16 · React 19 · Tailwind v4 · shadcn/ui |
| Observability | Langfuse (optional) · in-process cost/token meter |

---

## Running it

```bash
# 1. Infrastructure (Postgres, Elasticsearch, Qdrant, Redis, MinIO)
docker compose up -d

# 2. Backend
cd backend
python -m venv .venv && source .venv/bin/activate
pip install -r requirements.txt
cp .env.example .env          # set LLM_API_KEY (Groq's free tier works)
uvicorn app.main:app --port 8000

# 3. Ingestion worker (separate shell)
celery -A app.core.celery_app worker --pool=solo

# 4. Console (separate shell)
cd frontend && npm install && npm run dev     # → http://localhost:3000
```

A zero-dependency fallback console is served at `http://localhost:8000/ui/` if you'd rather skip the Node toolchain. API docs at `/docs`.

**First run downloads models** (~4 GB total: bge-m3, reranker, TrOCR, BLIP, Whisper) and the first agent call after a restart takes ~20 s while the reranker loads. Subsequent calls are ~1 s.

**`INGEST_SYNC=true`** processes uploads inline if you don't want to run a worker.

---

## API

| Endpoint | Purpose |
|---|---|
| `POST /api/auth/register` · `/login` | JWT auth |
| `POST /api/documents/upload` | Ingest a file (async) |
| `GET /api/documents/{id}` | Poll ingestion status |
| `GET /api/documents/search` | Raw retrieval — `mode=hybrid\|bm25\|vector`, `rerank=true` |
| `POST /api/agent/ask` | Full agent run: answer + trace + verification + sources |
| `POST /api/agent/report` | Same, reformatted (summary/ticket/email/slack) |
| `POST /api/eval/run` · `GET /api/eval` | Run and review evaluations |
| `GET /api/metrics` | LLM calls, tokens, cost, latency |
| `GET /api/connectors/*` | GitHub · Slack · weather · news |

---

## Engineering notes

Things that were less obvious than they looked:

**An empty retrieval result is not an empty corpus.** The planner would sometimes choose BM25 for a semantically-phrased question ("what is my name" against a résumé), get zero keyword matches, and the graph would report "no relevant documents" — while the answer sat in the vector index. Retrieval now falls back to hybrid when the planned mode comes back empty, and records `fallback_from` in the trace so the substitution is visible rather than silent.

**Dual-store writes need an owner.** Chunks live in Postgres, Elasticsearch, *and* Qdrant. Postgres commits first as the source of truth; if either index write fails, both index writes are rolled back and the document is marked `index_failed` — so a partial failure never leaves orphaned vectors that retrieval would surface.

**Re-rank even when nothing is truncated.** The cross-encoder isn't only for trimming candidates — it fixes citation *order*, so `[1]` is genuinely the most relevant passage.

**Security is checked, not assumed.** `pip-audit`, `bandit`, and `npm audit` all report zero findings. Along the way that meant replacing `python-jose` (unpatched CVE) with PyJWT, pinning Hugging Face model revisions so a hijacked upstream repo can't swap weights, and rejecting a `npm audit fix --force` that wanted to "fix" three advisories by downgrading Next.js 16 → 9.3.3 (forced the transitive deps up with `overrides` instead). User-supplied values are validated before they reach a URL path, LLM prompts treat retrieved passages as data rather than instructions, and provider errors are sanitised before they reach a client.

---

## Status

Working end-to-end locally. Deployment (Docker packaging of the app tier, CI, public hosting) is the remaining milestone — see [ROADMAP.md](ROADMAP.md). Deferred by choice: Google Workspace / Notion / Confluence / Zendesk connectors, speaker diarization (gated model), and the heavier vision models (BLIP-2, SAM, YOLO).

Full design scope: [OmniOps_AI_Project_Blueprint.md](OmniOps_AI_Project_Blueprint.md).
