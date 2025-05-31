# Migration Guide: Moving to rpger-content-extractor

This guide covers migrating the dockerized AI-Powered Extraction v3 to the new `rpger-content-extractor` repository.

## Overview

The Docker infrastructure created here is designed to be easily transferred to the new repository with minimal changes. Both deployment architectures (container stack and external databases) will work in the new environment.

## Files to Migrate

### Core Docker Files
```
├── Dockerfile                          # Application container definition
├── docker-compose.yml                  # Base compose configuration
├── docker-compose.containers.yml       # Full container stack
├── docker-compose.external.yml         # External databases configuration
├── .dockerignore                       # Build context exclusions
├── start-containers.sh                 # Container stack startup script
├── start-external.sh                   # External DB startup script
├── .env.containers                     # Container stack environment template
├── .env.external                       # External DB environment template
└── DOCKER_README.md                    # Quick start guide
```

### Supporting Configuration
```
├── docker/
│   ├── nginx/
│   │   └── nginx.conf                  # Reverse proxy configuration
│   └── mongodb/
│       └── init/
│           └── init-db.sh              # MongoDB initialization
└── docs/
    └── deployment/
        ├── DOCKER_DEPLOYMENT.md       # Complete deployment guide
        ├── container-stack-setup.md   # Container stack details
        └── external-db-setup.md       # External database details
```

### Application Changes
```
ui/app.py                               # Added health check and connection test endpoints
ui/templates/index.html                 # Enhanced settings with deployment mode selector
ui/static/js/app.js                     # Added deployment mode toggle functions
```

## Migration Steps

### 1. Repository Setup

```bash
# Create new repository
git clone <new-repository-url>
cd rpger-content-extractor

# Copy Docker infrastructure
cp -r ../extractor/{Dockerfile,docker-compose*.yml,.dockerignore} .
cp -r ../extractor/{start-*.sh,.env.*,DOCKER_README.md} .
cp -r ../extractor/docker/ .
cp -r ../extractor/docs/deployment/ docs/
```

### 2. Application Updates

**Update import paths** (if module structure changes):
```python
# In Dockerfile, update Python path setup if needed
# In app.py, update import statements for new module structure
```

**Update service names** (if desired):
```yaml
# In docker-compose files, update container names
container_name: rpger-content-extractor-app
container_name: rpger-content-extractor-mongodb
container_name: rpger-content-extractor-chromadb
```

### 3. Environment Configuration

```bash
# Update environment templates with new defaults
# .env.containers - update for new repository name
# .env.external - update example URLs/hostnames
```

### 4. Documentation Updates

```bash
# Update repository URLs in documentation
# Update any specific instructions for new repository
# Update quick start commands in DOCKER_README.md
```

## Validation Checklist

After migration, verify:

- [ ] **Docker files validate**: `docker compose config --quiet`
- [ ] **Startup scripts work**: Test both `start-containers.sh` and `start-external.sh`
- [ ] **Environment templates**: Verify `.env.containers` and `.env.external`
- [ ] **Health endpoints**: Test `/api/health` and `/api/test_connections`
- [ ] **UI enhancements**: Check deployment mode selector in settings
- [ ] **Documentation**: Review all guides for accuracy

## Testing Both Modes

### Container Stack Testing

```bash
# Start full stack
./start-containers.sh

# Verify services
docker compose -f docker-compose.yml -f docker-compose.containers.yml ps
curl http://localhost:5000/api/health

# Test functionality
# Upload a PDF, run extraction, check databases

# Clean up
docker compose -f docker-compose.yml -f docker-compose.containers.yml down -v
```

### External Database Testing

```bash
# Configure external databases
cp .env.external .env
# Edit .env with test database connections

# Start application only
./start-external.sh

# Verify application
docker compose -f docker-compose.yml -f docker-compose.external.yml ps
curl http://localhost:5000/api/health

# Test database connections via UI
# Use "Test Connections" button in Settings

# Clean up
docker compose -f docker-compose.yml -f docker-compose.external.yml down
```

## Architecture Benefits in New Repository

### Development Workflow
- **Consistent Environment**: Docker ensures same environment across developers
- **Easy Setup**: New contributors can start with `./start-containers.sh`
- **Database Management**: No need to install/configure MongoDB and ChromaDB locally

### Production Deployment
- **Flexible Architecture**: Choose between container stack or managed databases
- **Scalability**: External database mode allows independent scaling
- **Cloud Ready**: Works with MongoDB Atlas, hosted ChromaDB, etc.

### CI/CD Integration
```yaml
# Example GitHub Actions workflow
- name: Test Container Stack
  run: |
    ./start-containers.sh
    sleep 30  # Wait for services to start
    curl -f http://localhost:5000/api/health
    docker compose down
```

## Configuration Examples for New Repository

### Production External Setup

```bash
# .env for production
SETUP_MODE=external

# MongoDB Atlas
EXTERNAL_MONGODB_CONNECTION_STRING=mongodb+srv://user:pass@cluster.mongodb.net/rpger

# Hosted ChromaDB
EXTERNAL_CHROMA_BASE_URL=https://chroma-instance.example.com/api/v1

# Production AI keys
ANTHROPIC_API_KEY=sk-ant-production-key
OPENAI_API_KEY=sk-production-key

# Flask production settings
FLASK_ENV=production
FLASK_DEBUG=false
```

### Development Container Setup

```bash
# .env for development
SETUP_MODE=containers

# Development AI keys (or use mock)
ANTHROPIC_API_KEY=sk-ant-dev-key
DEFAULT_AI_PROVIDER=mock

# Flask development settings
FLASK_ENV=development
FLASK_DEBUG=true
```

## Advanced Features for New Repository

### Load Balancing
```yaml
# Multiple app instances
services:
  app1:
    build: .
    ports: ["5001:5000"]
  app2:
    build: .
    ports: ["5002:5000"]
  
  nginx:
    # Configure load balancing in nginx.conf
```

### Monitoring Stack
```yaml
# Add monitoring services
services:
  prometheus:
    image: prom/prometheus
  grafana:
    image: grafana/grafana
```

### Backup and Recovery
```bash
# Automated backup scripts
./scripts/backup-mongodb.sh
./scripts/backup-chromadb.sh
./scripts/restore-data.sh
```

## Future Enhancements

Consider these additions in the new repository:

1. **Helm Charts** for Kubernetes deployment
2. **Docker Swarm** configuration for multi-node deployment
3. **Automated SSL** certificate management
4. **Backup automation** with retention policies
5. **Monitoring and alerting** stack
6. **Performance profiling** tools
7. **Security scanning** integration

## Support and Troubleshooting

The migration includes comprehensive documentation to help users:

- **Quick Start**: DOCKER_README.md for immediate setup
- **Detailed Guides**: Complete deployment documentation
- **Troubleshooting**: Common issues and solutions
- **Architecture**: Clear explanation of both deployment modes

## Conclusion

This Docker infrastructure provides a solid foundation for the new `rpger-content-extractor` repository with:

- **Dual deployment options** for flexibility
- **Production-ready** configuration
- **Developer-friendly** setup
- **Comprehensive documentation**
- **Easy migration path**

The architecture scales from single-developer setup to production deployment with managed databases, making it suitable for the entire lifecycle of the new repository.