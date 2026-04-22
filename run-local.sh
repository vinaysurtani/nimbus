#!/bin/bash
echo "Starting Nimbus Platform..."

# Check if Docker is installed
if ! command -v docker &> /dev/null; then
    echo "Error: Docker is not installed"
    echo "Please install Docker and make sure it's running"
    exit 1
fi

echo "Building and starting services..."
docker-compose up --build -d

echo "Waiting for services to start..."
sleep 10

echo "Testing services..."
echo
echo "Testing Text Service directly:"
curl -X POST http://localhost:8001/process -H "Content-Type: application/json" -d '{"text": "Hello Nimbus!"}'

echo
echo "Testing Gateway:"
curl -X POST http://localhost:8080/api/v1/text/process -H "Content-Type: application/json" -d '{"text": "Hello via Gateway!"}'

echo
echo "Testing Sentiment Service:"
curl -X POST http://localhost:8002/analyze -H "Content-Type: application/json" -d '{"text": "I love this amazing product!"}'

echo
echo "Testing Sentiment via Gateway:"
curl -X POST http://localhost:8080/api/v1/sentiment/analyze -H "Content-Type: application/json" -d '{"text": "This is terrible and I hate it!"}'

echo
echo "Services are running:"
echo "- Text Service: http://localhost:8001"
echo "- Sentiment Service: http://localhost:8002"
echo "- Image Service: http://localhost:8003"
echo "- Gateway: http://localhost:8080"
echo "- Redis: localhost:6379"
echo "- PostgreSQL: localhost:5432"
echo
echo "API Documentation:"
echo "- Text Service: http://localhost:8001/docs"
echo "- Sentiment Service: http://localhost:8002/docs"
echo "- Image Service: http://localhost:8003/docs"

echo
echo "To stop services: docker-compose down"