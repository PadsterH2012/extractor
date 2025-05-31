# Docker Deployment for AI-Powered Extraction v3

This repository now supports Docker deployment with two architecture options for maximum flexibility.

## Quick Start

### Option 1: Full Container Stack (Recommended for Development)

```bash
# Start all services (app + databases)
./start-containers.sh
```

**What gets started:**
- Application container (port 5000)
- MongoDB container (port 27017) 
- ChromaDB container (port 8000)
- Nginx reverse proxy (port 80)

### Option 2: External Databases (Recommended for Production)

```bash
# Configure external databases
cp .env.external .env
# Edit .env with your database connection details

# Start only the application
./start-external.sh
```

**What gets started:**
- Application container only (port 5000)
- Connects to your external MongoDB and ChromaDB instances

## Resource Requirements

| Mode | RAM Usage | Storage | Best For |
|------|-----------|---------|----------|
| Full Container Stack | ~1.5GB | ~10GB | Development, Testing, Isolated Deployments |
| External Databases | ~200MB | ~1GB | Production with Managed Databases |

## Configuration

### Environment Templates

Two environment templates are provided:

- **`.env.containers`** - For full container stack
- **`.env.external`** - For external databases

### AI Provider Setup

Add your API keys to the `.env` file:

```bash
# Choose your AI provider
ANTHROPIC_API_KEY=sk-ant-your-key-here
OPENAI_API_KEY=sk-your-key-here
OPENROUTER_API_KEY=sk-or-your-key-here
```

## Management Commands

### Container Stack Mode

```bash
# Start all services
./start-containers.sh

# Check status
docker compose -f docker-compose.yml -f docker-compose.containers.yml ps

# View logs
docker compose -f docker-compose.yml -f docker-compose.containers.yml logs -f

# Stop all services
docker compose -f docker-compose.yml -f docker-compose.containers.yml down
```

### External Database Mode

```bash
# Start application
./start-external.sh

# Check status
docker compose -f docker-compose.yml -f docker-compose.external.yml ps

# View logs
docker compose -f docker-compose.yml -f docker-compose.external.yml logs -f

# Stop application
docker compose -f docker-compose.yml -f docker-compose.external.yml down
```

## Health Monitoring

- **Application Health**: http://localhost:5000/api/health
- **Real-time Status**: `docker ps`
- **Resource Usage**: `docker stats`

## External Database Examples

### MongoDB Atlas

```bash
# In .env file
EXTERNAL_MONGODB_CONNECTION_STRING=mongodb+srv://user:pass@cluster.mongodb.net/rpger
```

### Self-Hosted MongoDB

```bash
# In .env file
EXTERNAL_MONGODB_HOST=your-mongodb-server.com
EXTERNAL_MONGODB_PORT=27017
EXTERNAL_MONGODB_USERNAME=username
EXTERNAL_MONGODB_PASSWORD=password
EXTERNAL_MONGODB_DATABASE=rpger
```

### Self-Hosted ChromaDB

```bash
# In .env file
EXTERNAL_CHROMA_HOST=your-chromadb-server.com
EXTERNAL_CHROMA_PORT=8000
```

## Migration to New Repository

This Docker setup is designed to be easily moved to the new `rpger-content-extractor` repository:

1. Copy all Docker-related files
2. Copy documentation from `docs/deployment/`
3. Minimal application changes required
4. Both deployment modes work independently

## Documentation

Detailed guides available in `docs/deployment/`:

- [Docker Deployment Guide](docs/deployment/DOCKER_DEPLOYMENT.md)
- [Container Stack Setup](docs/deployment/container-stack-setup.md)
- [External Database Setup](docs/deployment/external-db-setup.md)

## Troubleshooting

### Common Issues

1. **Port conflicts**: Check if ports 5000, 27017, 8000, 80 are available
2. **Memory issues**: Ensure 2GB+ RAM available for container stack
3. **Docker not running**: Start Docker Desktop/daemon

### Quick Fixes

```bash
# Reset everything (⚠️ loses data)
docker compose down -v
docker system prune -f

# Rebuild from scratch
docker compose build --no-cache
```

### Get Help

```bash
# Check application health
curl http://localhost:5000/api/health

# Test database connections (external mode)
# Use the "Test Connections" button in Settings UI
```

---

**Next Steps**: This setup provides the foundation for moving to the new `rpger-content-extractor` repository with flexible deployment options.