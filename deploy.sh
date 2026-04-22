#!/bin/bash

echo "🚀 Deploying Nimbus Platform to Kubernetes..."

# Check if kubectl is available
if ! command -v kubectl &> /dev/null; then
    echo "❌ kubectl is not installed"
    exit 1
fi

# Apply namespace and config
echo "📦 Creating namespace and configuration..."
kubectl apply -f infrastructure/k8s/namespace.yaml

# Deploy infrastructure components
echo "🗄️ Deploying Redis and PostgreSQL..."
kubectl apply -f infrastructure/k8s/redis.yaml
kubectl apply -f infrastructure/k8s/postgres.yaml

# Wait for infrastructure to be ready
echo "⏳ Waiting for infrastructure to be ready..."
kubectl wait --for=condition=available --timeout=300s deployment/redis -n nimbus
kubectl wait --for=condition=available --timeout=300s deployment/postgres -n nimbus

# Deploy services
echo "🔧 Deploying microservices..."
kubectl apply -f infrastructure/k8s/text-service.yaml
kubectl apply -f infrastructure/k8s/gateway.yaml

# Wait for services to be ready
echo "⏳ Waiting for services to be ready..."
kubectl wait --for=condition=available --timeout=300s deployment/text-service -n nimbus
kubectl wait --for=condition=available --timeout=300s deployment/gateway -n nimbus

# Get service status
echo "✅ Deployment complete!"
echo
echo "📊 Service Status:"
kubectl get pods -n nimbus
echo
echo "🌐 Services:"
kubectl get services -n nimbus

# Get gateway URL
GATEWAY_URL=$(kubectl get service gateway -n nimbus -o jsonpath='{.status.loadBalancer.ingress[0].ip}')
if [ -z "$GATEWAY_URL" ]; then
    GATEWAY_URL="localhost"
    echo "🔗 Gateway URL: http://$GATEWAY_URL:8080 (use port-forward: kubectl port-forward service/gateway 8080:8080 -n nimbus)"
else
    echo "🔗 Gateway URL: http://$GATEWAY_URL:8080"
fi

echo
echo "🧪 Test the deployment:"
echo "curl -X POST http://$GATEWAY_URL:8080/api/v1/text/process -H 'Content-Type: application/json' -d '{\"text\": \"Hello Kubernetes!\"}'"