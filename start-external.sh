#!/bin/bash
# Start AI-Powered Extraction v3 with external databases

set -e

echo "🐳 Starting AI-Powered Extraction v3 - External Databases Mode"
echo "This will start only the application container, connecting to external databases"
echo ""

# Check if .env file exists
if [ ! -f .env ]; then
    echo "📋 Creating .env file from .env.external template..."
    cp .env.external .env
    echo "⚠️  Please configure your external database connections in .env file"
fi

# Check if docker is running
if ! docker info > /dev/null 2>&1; then
    echo "❌ Docker is not running. Please start Docker and try again."
    exit 1
fi

# Create necessary directories
mkdir -p uploads documents

# Start services
echo "🚀 Starting application container..."
docker compose -f docker-compose.yml -f docker-compose.external.yml up -d

echo ""
echo "✅ Application started successfully!"
echo ""
echo "📊 Service Status:"
echo "  - Application: http://localhost:5000"
echo ""
echo "⚠️  Note: Make sure your external databases are accessible:"
echo "  - MongoDB: Check EXTERNAL_MONGODB_* variables in .env"
echo "  - ChromaDB: Check EXTERNAL_CHROMA_* variables in .env"
echo ""
echo "🔍 To check application health:"
echo "  docker compose -f docker-compose.yml -f docker-compose.external.yml ps"
echo ""
echo "📝 To view logs:"
echo "  docker compose -f docker-compose.yml -f docker-compose.external.yml logs -f app"
echo ""
echo "🛑 To stop the application:"
echo "  docker compose -f docker-compose.yml -f docker-compose.external.yml down"