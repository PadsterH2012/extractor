# Docker Deployment Guide

This guide covers how to deploy AI-Powered Extraction v3 using Docker with two different architecture options.

## Architecture Options

### Option 1: Full Container Stack
- **Description**: Self-contained deployment with all databases in containers
- **Components**: App + MongoDB + ChromaDB + Nginx
- **Resource Usage**: ~1.5GB RAM
- **Best For**: Development, testing, isolated environments

### Option 2: External Databases
- **Description**: App container only, connecting to external databases
- **Components**: App container only
- **Resource Usage**: ~200MB RAM
- **Best For**: Production with managed databases (MongoDB Atlas, etc.)

## Quick Start

### Option 1: Full Container Stack

```bash
# Clone and navigate to the repository
git clone <repository-url>
cd extractor

# Start the full stack
./start-containers.sh
```

**Services will be available at:**
- Application UI: http://localhost:5000
- MongoDB: localhost:27017
- ChromaDB: http://localhost:8000
- Nginx Proxy: http://localhost:80

### Option 2: External Databases

```bash
# Clone and navigate to the repository
git clone <repository-url>
cd extractor

# Configure external databases
cp .env.external .env
# Edit .env file with your external database details

# Start the application
./start-external.sh
```

**Service will be available at:**
- Application UI: http://localhost:5000

## Configuration

### Environment Variables

The application uses environment variables for configuration. Two template files are provided:

- **`.env.containers`** - For full container stack
- **`.env.external`** - For external databases

### Database Configuration

#### MongoDB
- **Container mode**: Uses local MongoDB container
- **External mode**: Requires external MongoDB connection details

#### ChromaDB
- **Container mode**: Uses local ChromaDB container
- **External mode**: Requires external ChromaDB instance

### AI Provider Configuration

Set your AI provider API keys in the `.env` file:

```bash
# Claude/Anthropic
ANTHROPIC_API_KEY=sk-ant-your-key-here

# OpenAI
OPENAI_API_KEY=sk-your-key-here

# OpenRouter
OPENROUTER_API_KEY=sk-or-your-key-here
```

## Management Commands

### Full Container Stack

```bash
# Start services
./start-containers.sh

# Check service status
docker-compose -f docker-compose.yml -f docker-compose.containers.yml ps

# View logs
docker-compose -f docker-compose.yml -f docker-compose.containers.yml logs -f [service_name]

# Stop services
docker-compose -f docker-compose.yml -f docker-compose.containers.yml down

# Stop and remove volumes (⚠️ This will delete all data)
docker-compose -f docker-compose.yml -f docker-compose.containers.yml down -v
```

### External Databases

```bash
# Start application
./start-external.sh

# Check application status
docker-compose -f docker-compose.yml -f docker-compose.external.yml ps

# View logs
docker-compose -f docker-compose.yml -f docker-compose.external.yml logs -f app

# Stop application
docker-compose -f docker-compose.yml -f docker-compose.external.yml down
```

## Health Monitoring

### Health Check Endpoints

- **Application Health**: http://localhost:5000/api/health
- **ChromaDB Health**: http://localhost:8000/api/v1/heartbeat (container mode only)

### Monitoring Services

```bash
# Check all container health
docker ps --format "table {{.Names}}\t{{.Status}}"

# View real-time resource usage
docker stats
```

## Data Persistence

### Container Mode
- **MongoDB data**: Stored in `mongodb_data` Docker volume
- **ChromaDB data**: Stored in `chromadb_data` Docker volume
- **Application uploads**: Mapped to `./uploads` directory

### External Mode
- **Application uploads**: Mapped to `./uploads` directory
- **Database data**: Managed by external services

## Troubleshooting

### Common Issues

1. **Port conflicts**: Ensure ports 5000, 27017, 8000, and 80 are available
2. **Permission issues**: Ensure the user can access Docker
3. **Memory issues**: Container stack requires ~1.5GB RAM
4. **Database connections**: Check network connectivity for external databases

### Logs and Debugging

```bash
# Application logs
docker logs extractor-app

# Database logs
docker logs extractor-mongodb
docker logs extractor-chromadb

# All services logs
docker-compose logs -f
```

### Reset Environment

```bash
# Stop all services and remove data (⚠️ Destructive)
docker-compose -f docker-compose.yml -f docker-compose.containers.yml down -v
docker system prune -f

# Rebuild from scratch
docker-compose -f docker-compose.yml -f docker-compose.containers.yml build --no-cache
```

## Security Considerations

1. **Change default passwords** in production environments
2. **Use HTTPS** with proper SSL certificates (configure in nginx)
3. **Network security** - restrict database access in external mode
4. **API keys** - keep AI provider keys secure and rotate regularly
5. **File uploads** - monitor upload directory disk usage

## Performance Tuning

### Container Limits

```yaml
# Add to docker-compose.yml services
deploy:
  resources:
    limits:
      memory: 512M
      cpus: '1.0'
    reservations:
      memory: 256M
      cpus: '0.5'
```

### Database Optimization

- **MongoDB**: Configure appropriate indexes for your use case
- **ChromaDB**: Adjust collection parameters for performance
- **Storage**: Use SSD storage for database volumes

## Migration Guide

See [migration-guide.md](migration-guide.md) for detailed instructions on migrating between deployment modes.