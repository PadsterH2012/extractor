# Container Stack Setup Guide

This guide provides detailed instructions for setting up AI-Powered Extraction v3 with the full container stack (App + MongoDB + ChromaDB).

## Prerequisites

- Docker Engine 20.10+
- Docker Compose 2.0+
- 2GB+ available RAM
- 10GB+ available disk space

## Architecture Overview

```
┌─────────────────────────────────────┐
│           Docker Compose            │
├─────────────────────────────────────┤
│ ┌─────────┐ ┌─────────┐ ┌─────────┐ │
│ │   App   │ │ MongoDB │ │ChromaDB │ │
│ │Container│ │Container│ │Container│ │
│ └─────────┘ └─────────┘ └─────────┘ │
│ ┌─────────────────────────────────┐ │
│ │         Nginx Proxy             │ │
│ └─────────────────────────────────┘ │
└─────────────────────────────────────┘
```

## Step-by-Step Setup

### 1. System Preparation

```bash
# Verify Docker installation
docker --version
docker-compose --version

# Ensure Docker daemon is running
docker info

# Check available resources
docker system df
```

### 2. Repository Setup

```bash
# Clone the repository
git clone <repository-url>
cd extractor

# Create necessary directories
mkdir -p uploads documents docker/nginx docker/mongodb/init
```

### 3. Configuration

```bash
# Copy container environment template
cp .env.containers .env

# Edit configuration (optional)
nano .env
```

**Key Configuration Options:**

```bash
# AI Provider (choose one)
ANTHROPIC_API_KEY=sk-ant-your-key-here
OPENAI_API_KEY=sk-your-key-here
OPENROUTER_API_KEY=sk-or-your-key-here

# Database Credentials (change in production)
MONGODB_USERNAME=root
MONGODB_PASSWORD=extractor123

# AI Behavior
AI_TEMPERATURE=0.3
AI_MAX_TOKENS=4000
```

### 4. Start Services

```bash
# Start all services
./start-containers.sh

# Or manually:
docker-compose -f docker-compose.yml -f docker-compose.containers.yml up -d
```

### 5. Verify Installation

```bash
# Check service status
docker-compose ps

# Test application health
curl http://localhost:5000/api/health

# Test database connections
curl http://localhost:8000/api/v1/heartbeat  # ChromaDB
docker exec extractor-mongodb mongosh --eval "db.adminCommand('ping')"  # MongoDB
```

## Service Details

### Application Container
- **Image**: Custom built from Dockerfile
- **Port**: 5000
- **Health**: http://localhost:5000/api/health
- **Logs**: `docker logs extractor-app`

### MongoDB Container
- **Image**: mongo:7.0
- **Port**: 27017
- **Database**: rpger
- **Credentials**: root/extractor123
- **Data**: mongodb_data volume

### ChromaDB Container
- **Image**: chromadb/chroma:0.4.15
- **Port**: 8000
- **API**: http://localhost:8000/api/v1
- **Data**: chromadb_data volume

### Nginx Container
- **Image**: nginx:alpine
- **Ports**: 80, 443
- **Config**: docker/nginx/nginx.conf
- **Purpose**: Reverse proxy and load balancing

## Data Management

### Volumes

```bash
# List volumes
docker volume ls

# Inspect volume
docker volume inspect extractor_mongodb_data
docker volume inspect extractor_chromadb_data

# Backup volumes
docker run --rm -v extractor_mongodb_data:/data -v $(pwd):/backup alpine tar czf /backup/mongodb-backup.tar.gz -C /data .
docker run --rm -v extractor_chromadb_data:/data -v $(pwd):/backup alpine tar czf /backup/chromadb-backup.tar.gz -C /data .
```

### Database Access

```bash
# MongoDB shell
docker exec -it extractor-mongodb mongosh

# MongoDB with authentication
docker exec -it extractor-mongodb mongosh -u root -p extractor123

# ChromaDB API
curl http://localhost:8000/api/v1/collections
```

## Monitoring and Maintenance

### Service Monitoring

```bash
# Real-time status
watch docker-compose ps

# Resource usage
docker stats

# Service logs
docker-compose logs -f app
docker-compose logs -f mongodb
docker-compose logs -f chromadb
docker-compose logs -f nginx
```

### Health Checks

```bash
# Application health
curl -s http://localhost:5000/api/health | jq .

# MongoDB health
docker exec extractor-mongodb mongosh --eval "db.stats()" --quiet

# ChromaDB health
curl -s http://localhost:8000/api/v1/heartbeat
```

### Updates and Maintenance

```bash
# Pull latest images
docker-compose pull

# Rebuild application
docker-compose build --no-cache app

# Restart specific service
docker-compose restart app

# Update with minimal downtime
docker-compose up -d --no-deps app
```

## Scaling and Performance

### Resource Limits

Edit `docker-compose.containers.yml`:

```yaml
services:
  app:
    deploy:
      resources:
        limits:
          memory: 1G
          cpus: '1.0'
        reservations:
          memory: 512M
          cpus: '0.5'
  
  mongodb:
    deploy:
      resources:
        limits:
          memory: 1G
          cpus: '1.0'
```

### MongoDB Optimization

```bash
# Connect to MongoDB
docker exec -it extractor-mongodb mongosh -u root -p extractor123

# Create additional indexes
db.extractions.createIndex({"metadata.game_type": 1, "metadata.edition": 1})
db.extractions.createIndex({"created_at": -1})

# Monitor performance
db.serverStatus()
db.stats()
```

### ChromaDB Optimization

- Configure collection parameters for your use case
- Monitor memory usage with large document collections
- Consider collection sharding for very large datasets

## Troubleshooting

### Common Issues

1. **Port Conflicts**
   ```bash
   # Check port usage
   netstat -tulpn | grep -E ':(5000|27017|8000|80)'
   
   # Change ports in docker-compose.yml if needed
   ```

2. **Memory Issues**
   ```bash
   # Check available memory
   free -h
   
   # Adjust container limits
   # Edit docker-compose.containers.yml
   ```

3. **Permission Issues**
   ```bash
   # Fix file permissions
   sudo chown -R $USER:$USER .
   
   # Fix Docker permissions
   sudo usermod -aG docker $USER
   # Logout and login again
   ```

4. **Database Connection Issues**
   ```bash
   # Check container networking
   docker network ls
   docker network inspect extractor_extractor-network
   
   # Test connectivity
   docker exec extractor-app ping mongodb
   docker exec extractor-app ping chromadb
   ```

### Recovery Procedures

```bash
# Restart all services
docker-compose restart

# Reset containers (keeps data)
docker-compose down
docker-compose up -d

# Full reset (⚠️ loses data)
docker-compose down -v
docker system prune -f
./start-containers.sh
```

## Security Hardening

### Production Security

1. **Change Default Passwords**
   ```bash
   # Edit .env file
   MONGODB_PASSWORD=your-secure-password
   ```

2. **Enable SSL/TLS**
   - Configure SSL certificates in nginx
   - Update nginx.conf for HTTPS

3. **Network Security**
   ```yaml
   # Add to docker-compose.containers.yml
   networks:
     extractor-network:
       driver: bridge
       internal: true  # Isolate from external networks
   ```

4. **File Permissions**
   ```bash
   # Secure configuration files
   chmod 600 .env
   chmod 600 docker/mongodb/init/*
   ```

### Monitoring and Alerting

Consider adding monitoring stack:
- Prometheus for metrics
- Grafana for dashboards
- AlertManager for alerts

## Next Steps

After successful setup:

1. **Test the application** with sample PDFs
2. **Configure AI providers** with your API keys
3. **Set up backup procedures** for production use
4. **Review security settings** for your environment
5. **Consider monitoring and alerting** for production deployments

For external database setup, see [external-db-setup.md](external-db-setup.md).