# Roadmap — Milestones & Issues

Breakdown of [OmniOps_AI_Project_Blueprint.md](OmniOps_AI_Project_Blueprint.md) into 4 milestones, 12 weeks. Local draft — import to GitHub later (`gh` not installed yet).

---

## Milestone 1: Foundation (Weeks 1–2) — ✅ COMPLETE

- [x] Scaffold FastAPI backend project structure
- [x] Set up PostgreSQL + connection layer
- [x] Implement JWT authentication service (OAuth social login moved to Milestone 4 — needs frontend + provider registration)
- [x] API Gateway routing skeleton (FastAPI app as single entrypoint w/ routers)
- [x] Document ingestion endpoint (upload PDF/CSV/images)
- [x] OCR pipeline (Microsoft TrOCR, line-level printed text; full-page detection comes with M2 Vision Agent)
- [x] Chunking + metadata extraction (size/pages/chars/chunks)
- [x] Embedding generation (BAAI/bge-m3)
- [x] Qdrant vector storage integration
- [x] BM25 index (Elasticsearch)
- [x] Hybrid retrieval (vector + BM25, RRF fusion)
- [x] Basic LLM response generation via LiteLLM (+ hardening: rate limiting, password policy, magic-byte checks, 0 known CVEs)

## Milestone 2: Multi-Agent System (Weeks 3–5)

- [x] LangGraph orchestrator setup (planner→retrieval→answer→verifier graph, /api/agent/ask w/ node trace)
- [x] Planner Agent (LLM picks retrieval mode+limit, heuristic fallback)
- [ ] Vision Agent (Florence-2, BLIP-2, SAM, YOLO)
- [x] Audio Agent v1 (faster-whisper STT: audio upload → transcript → chunks → searchable/askable; diarization deferred — pyannote models gated behind HF access token)
- [x] Document Agent (OCR + chunking + metadata + dual indexing formalized as agents/document_agent.py; used by Celery task + inline path)
- [x] Retrieval Agent (cross-encoder re-ranking w/ bge-reranker-v2-m3; agent overfetches 3x then reranks, search endpoint has rerank=true flag)
- [x] Verification Agent (LLM groundedness verdict + mechanical citation validation: used/phantom/uncited; phantom citations override verdict to not-grounded)
- [x] Report Agent (graph node after verifier: summary/report/ticket/slack/email via /api/agent/report)
- [x] Redis + Celery async task queue wiring (upload returns instantly w/ status=queued; worker ingests; GET /documents/{id} polling; inline fallback when broker down; INGEST_SYNC env escape hatch)
- [ ] Enterprise connectors: GitHub, Jira, Slack
- [ ] Enterprise connectors: Gmail, Google Drive, Google Calendar
- [ ] Enterprise connectors: Notion, Confluence, Zendesk
- [ ] Enterprise connectors: News API, Weather API

## Milestone 3: Evaluation & Monitoring (Weeks 6–8)

- [ ] Langfuse integration for tracing
- [ ] OpenTelemetry instrumentation
- [ ] Prometheus + Grafana metrics/dashboards
- [ ] Automated eval pipeline (Question → Answer → Judge LLM → Metrics)
- [ ] RAGAS / DeepEval integration
- [ ] Track cost, latency, token usage
- [ ] Track hallucination rate, faithfulness, groundedness
- [ ] Track retrieval precision, tool success rate
- [ ] Cost Dashboard (UI)
- [ ] Evaluation Dashboard (UI)

## Milestone 4: UI, Deployment, Polish (Weeks 9–12)

- [ ] Next.js + Tailwind + shadcn/ui frontend scaffold
- [ ] OAuth social login (moved from M1 — needs frontend + provider registration)
- [ ] Dashboard page
- [ ] Chat page
- [ ] Agent Execution Graph page
- [ ] Retrieval Inspector page
- [ ] Admin Panel page
- [ ] MinIO/S3 storage wiring for file assets
- [ ] Dockerize all services
- [ ] Kubernetes manifests / Helm chart
- [ ] GitHub Actions CI: unit tests, integration tests, eval benchmarks, docker build
- [ ] CD: automated deployment pipeline
- [ ] GPU worker pool setup for model inference
- [ ] Documentation pass
- [ ] Public deployment

> **Free deployment options** (researched 2026-07): full stack needs ~6GB RAM (bge-m3 + reranker + ES) — no PaaS free tier fits.
> 1. **Oracle Cloud Always Free** ARM VM (4 cores/24GB) — whole docker compose as-is, zero code changes.
> 2. **Managed free tiers** (Render + Neon PG + Qdrant Cloud 1GB + Groq) — needs swaps: ES→Postgres FTS, local embeddings→API embeddings.
> 3. **No hosting** — README + demo GIF + `docker compose up` instructions.

---

## Backlog / Future Extensions (unscheduled)

- [ ] Fine-tuned domain models
- [ ] MCP support
- [ ] RL for agent planning
- [ ] Graph RAG
- [ ] Long-term memory
- [ ] Autonomous scheduling
- [ ] Mobile application
- [ ] Voice assistant

---

## To import into GitHub later

```bash
brew install gh
gh auth login
# then create 4 milestones + issues per checklist above, e.g.:
gh api repos/PearlKalariya/OmniOpsAI/milestones -f title="M1: Foundation" -f description="Weeks 1-2"
gh issue create --title "Scaffold FastAPI backend" --milestone "M1: Foundation"
```
