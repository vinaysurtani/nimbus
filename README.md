# Nimbus Cloud-Native AI Microservices Platform

A cloud-native AI microservices suite with text, sentiment, and image processing capabilities.

## Architecture

- **AI Microservices**: FastAPI + gRPC (Python)
- **API Gateway**: Go with Redis caching + PostgreSQL
- **Orchestration**: Kubernetes
- **IaC**: Pulumi
- **CI/CD**: GitHub Actions + ArgoCD
- **Monitoring**: OpenTelemetry + Grafana

## Quick Start

**Windows:**
```cmd
run-local.bat
```

**Linux/Mac:**
```bash
./run-local.sh
```

**Manual Docker:**
```bash
docker-compose up --build -d

# Test text processing
curl -X POST http://localhost:8080/api/v1/text/process \
  -H "Content-Type: application/json" \
  -d '{"text": "Hello world from Nimbus!"}'
```

## Services

- **Text Service**: Port 8001 (HTTP), 50051 (gRPC)
- **Gateway**: Port 8080
- **Redis**: Port 6379
- **PostgreSQL**: Port 5432

## Development

Each service can be developed independently. See individual service directories for specific instructions.

## CI/CD Pipeline

**GitHub Actions:**
- Automated testing on push/PR
- Multi-service Docker builds
- Security vulnerability scanning
- Automatic deployment to staging

**ArgoCD GitOps:**
- Continuous deployment to production
- Automatic sync from Git repository
- Self-healing deployments

## Deployment

**Local Development:**
```bash
./run-local.sh
```

**Kubernetes:**
```bash
./deploy.sh
```

**ArgoCD:**
```bash
kubectl apply -f infrastructure/argocd/application.yaml
```