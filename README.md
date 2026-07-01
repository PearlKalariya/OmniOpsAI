# OmniOps AI

**Autonomous Enterprise Operations Platform** — a production-grade multimodal AI platform that understands documents, images, audio, video, and enterprise data to autonomously solve operational problems.

Full design doc: [OmniOps_AI_Project_Blueprint.md](OmniOps_AI_Project_Blueprint.md)

## Vision

An AI Operating System for enterprises combining Hybrid RAG, Multi-Agent Orchestration, Multimodal AI, LLM Evaluation, LLMOps, and production-grade deployment. Instead of a simple chatbot, it ingests enterprise knowledge, understands multiple data modalities, integrates with business tools, and autonomously performs complex workflows.

## Architecture

```
User → API Gateway → Auth Service → Request Orchestrator (LangGraph)
  → [Vision Agent | Audio Agent | Document Agent] → Planner
  → Retrieval Agent → Hybrid Search (Vector + BM25 + Graph)
  → Knowledge Store → Enterprise Connectors
  → Response Synthesizer → Evaluation & Monitoring
```

Agents: Planner, Vision, Audio, Document, Retrieval, Verification, Report.

## Tech Stack

| Layer | Tech |
|---|---|
| Backend | FastAPI (Python) |
| Agent Framework | LangGraph |
| Vector DB | Qdrant |
| Database | PostgreSQL |
| Queue | Redis + Celery |
| Storage | MinIO / S3 |
| Search | Elasticsearch |
| Auth | JWT / OAuth |
| Monitoring | Langfuse, OpenTelemetry, Prometheus, Grafana |
| LLM Gateway | LiteLLM |
| Frontend | Next.js, Tailwind CSS, shadcn/ui |

## Roadmap (12 Weeks)

- **Weeks 1–2** — Backend, Auth, Document Ingestion, Hybrid RAG
- **Weeks 3–5** — Multi-Agent System, Vision Agent, Audio Agent, Enterprise Integrations
- **Weeks 6–8** — Evaluation, Monitoring, Dashboards
- **Weeks 9–12** — UI Polish, Docker, Kubernetes, CI/CD, Documentation, Public Deployment

## Status

Early planning stage — no application code yet. See blueprint for full scope (agents, RAG pipeline, integrations, HF models, LLMOps metrics, UI pages).
