# Roadmap — Milestones & Issues

Breakdown of [OmniOps_AI_Project_Blueprint.md](OmniOps_AI_Project_Blueprint.md) into 4 milestones, 12 weeks. Local draft — import to GitHub later (`gh` not installed yet).

---

## Milestone 1: Foundation (Weeks 1–2)

- [ ] Scaffold FastAPI backend project structure
- [ ] Set up PostgreSQL + connection layer
- [ ] Implement JWT/OAuth authentication service
- [ ] API Gateway routing skeleton
- [ ] Document ingestion endpoint (upload PDF/CSV)
- [ ] OCR pipeline (Microsoft TrOCR)
- [ ] Chunking + metadata extraction
- [ ] Embedding generation (BAAI/bge-m3)
- [ ] Qdrant vector storage integration
- [ ] BM25 index (Elasticsearch)
- [ ] Hybrid retrieval (vector + BM25)
- [ ] Basic LLM response generation via LiteLLM

## Milestone 2: Multi-Agent System (Weeks 3–5)

- [ ] LangGraph orchestrator setup
- [ ] Planner Agent (tool/model/data-source routing)
- [ ] Vision Agent (Florence-2, BLIP-2, SAM, YOLO)
- [ ] Audio Agent (Whisper, Pyannote, diarization)
- [ ] Document Agent (OCR + chunking + retrieval, formalized)
- [ ] Retrieval Agent (cross-encoder re-ranking w/ bge-reranker-v2)
- [ ] Verification Agent (fact-checking, citation validation, hallucination detection)
- [ ] Report Agent (exec summary, tech report, ticket/email/Slack drafts)
- [ ] Redis + Celery async task queue wiring
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
