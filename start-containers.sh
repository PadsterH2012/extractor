#!/bin/bash
# Start AI-Powered Extraction v3 with containerized databases

set -e

echo "🐳 Starting AI-Powered Extraction v3 - Full Container Stack"
echo "This will start the application with MongoDB and ChromaDB containers"
echo ""

# Check if .env file exists
if [ ! -f .env ]; then
    echo "📋 Creating .env file from .env.containers template..."
    cp .env.containers .env
fi

# Check if docker is running
if ! docker info > /dev/null 2>&1; then
    echo "❌ Docker is not running. Please start Docker and try again."
    exit 1
fi

# Create necessary directories
mkdir -p uploads documents docker/mongodb/init docker/nginx

# Start services
echo "🚀 Starting services..."
docker compose -f docker-compose.yml -f docker-compose.containers.yml up -d

echo ""
echo "✅ Services started successfully!"
echo ""
echo "📊 Service Status:"
echo "  - Application: http://localhost:5000"
echo "  - MongoDB: localhost:27017"
echo "  - ChromaDB: http://localhost:8000"
echo "  - Nginx Proxy: http://localhost:80"
echo ""
echo "🔍 To check service health:"
echo "  docker compose -f docker-compose.yml -f docker-compose.containers.yml ps"
echo ""
echo "📝 To view logs:"
echo "  docker compose -f docker-compose.yml -f docker-compose.containers.yml logs -f [service_name]"
echo ""
echo "🛑 To stop all services:"
echo "  docker compose -f docker-compose.yml -f docker-compose.containers.yml down"