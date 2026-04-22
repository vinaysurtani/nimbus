# Nimbus

A production-grade AI backend platform built with Go and Python microservices. Nimbus demonstrates real-world AI engineering: LLM integration, RAG pipelines, streaming, and observability — all wired together with a working React frontend.

## What it does

| Feature | Endpoint | Description |
|---------|----------|-------------|
| Text processing | `POST /api/v1/text/process` | Cleans and summarizes text via Claude |
| Keyword extraction | `POST /api/v1/text/keywords` | Extracts meaningful keywords via Claude |
| Sentiment analysis | `POST /api/v1/sentiment/analyze` | Returns sentiment, confidence, polarity via Claude |
| Streaming chat | `POST /api/v1/chat/stream` | SSE token-by-token streaming from Claude |
| Image captioning | `POST /api/v1/image/caption` | Single-sentence caption via Claude Vision |
| Image analysis | `POST /api/v1/image/analyze` | Scene description, objects, colors, mood |
| RAG ingest | `POST /api/v1/rag/ingest` | Chunks + embeds documents into Qdrant |
| RAG query | `POST /api/v1/rag/query` | Retrieves context, answers with Claude |
| Metrics | `GET /api/v1/metrics` | Request counts, latency, cache hit rate per endpoint |

## Architecture

```
Browser (React + Vite)
        │
        ▼
  Go Gateway :8080
  ├── Redis cache
  ├── PostgreSQL request log
  └── Routes to:
       ├── text-service    :8001  (FastAPI + Claude)
       ├── sentiment-service :8002 (FastAPI + Claude)
       ├── image-service   :8003  (FastAPI + Claude Vision)
       └── rag-service     :8004  (FastAPI + Qdrant + fastembed + Claude)
                                        │
                                        ▼
                                  Qdrant :6333
```

**Stack:**
- **Gateway** — Go, Gin, Redis (caching), PostgreSQL (request logging)
- **AI services** — Python, FastAPI, Anthropic SDK (`claude-haiku-4-5-20251001`)
- **RAG** — fastembed (`BAAI/bge-small-en-v1.5`), Qdrant vector DB
- **Frontend** — React, TypeScript, Vite
- **Infra** — Docker Compose (local), Kubernetes manifests, GitHub Actions CI/CD

## Quick start

**Prerequisites:** Docker Desktop, an [Anthropic API key](https://console.anthropic.com)

```bash
git clone https://github.com/vinaysurtani/nimbus
cd nimbus
cp .env.example .env
# Add your ANTHROPIC_API_KEY to .env
```

**Windows (PowerShell):**
```powershell
$env:DOCKER_BUILDKIT=0
$env:COMPOSE_DOCKER_CLI_BUILD=0
docker-compose up --build -d
```

**Linux/Mac:**
```bash
docker-compose up --build -d
```

Open **http://localhost:3000** for the UI, or hit the API directly at **http://localhost:8080**.

## Try it

```powershell
# Text processing
curl -Method POST http://localhost:8080/api/v1/text/process `
  -ContentType "application/json" `
  -Body '{"text": "so basically i went to the store and bought stuff"}'

# Sentiment
curl -Method POST http://localhost:8080/api/v1/sentiment/analyze `
  -ContentType "application/json" `
  -Body '{"text": "I love building things that actually work"}'

# RAG — ingest then query
curl -Method POST http://localhost:8080/api/v1/rag/ingest `
  -ContentType "application/json" `
  -Body '{"text": "Nimbus uses Redis for caching and Qdrant for vector storage."}'

curl -Method POST http://localhost:8080/api/v1/rag/query `
  -ContentType "application/json" `
  -Body '{"question": "What does Nimbus use for caching?"}'
```

## Services

| Service | Port | Language |
|---------|------|----------|
| Gateway | 8080 | Go |
| Text service | 8001 | Python |
| Sentiment service | 8002 | Python |
| Image service | 8003 | Python |
| RAG service | 8004 | Python |
| Frontend | 3000 | TypeScript |
| Redis | 6379 | — |
| PostgreSQL | 5432 | — |
| Qdrant | 6333 | — |

## CI/CD

GitHub Actions pipeline on every push:
- Tests (Go + Python)
- Multi-service Docker builds → pushed to `ghcr.io`
- Security scan (Trivy + SARIF upload)
- Auto-updates K8s manifests with new image tags on `main`

## Kubernetes

Manifests in `infrastructure/k8s/` cover all services, Qdrant (with PVC), PostgreSQL, Redis, and secrets.

```bash
kubectl apply -f infrastructure/k8s/namespace.yaml
kubectl apply -f infrastructure/k8s/secrets.yaml
kubectl apply -f infrastructure/k8s/
```

## License

MIT
