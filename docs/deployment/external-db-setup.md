# External Database Setup Guide

This guide provides detailed instructions for setting up AI-Powered Extraction v3 with external databases (MongoDB Atlas, managed ChromaDB, etc.).

## Prerequisites

- Docker Engine 20.10+
- External MongoDB instance (MongoDB Atlas, self-hosted, etc.)
- External ChromaDB instance (Chroma hosted, self-hosted, etc.)
- Network connectivity to external databases

## Architecture Overview

```
┌─────────────────┐    ┌─────────────────┐
│   App Container │────│  External       │
│                 │    │  MongoDB Atlas  │
│                 │    │  (or self-host) │
│                 │────┼─────────────────┤
│                 │    │  External       │
│                 │    │  ChromaDB       │
│                 │    │  (or Pinecone)  │
└─────────────────┘    └─────────────────┘
```

## Step-by-Step Setup

### 1. Prepare External Databases

#### MongoDB Setup Options

**Option A: MongoDB Atlas (Recommended)**

1. Create MongoDB Atlas account at https://cloud.mongodb.com
2. Create a new cluster
3. Configure network access (whitelist your IP or 0.0.0.0/0 for any IP)
4. Create database user with read/write permissions
5. Get connection string

**Option B: Self-Hosted MongoDB**

1. Install MongoDB on your server
2. Configure authentication and networking
3. Create database and user
4. Ensure firewall allows connections

#### ChromaDB Setup Options

**Option A: Chroma Hosted Service**

1. Sign up for Chroma hosted service
2. Create your database instance
3. Get API endpoint and credentials

**Option B: Self-Hosted ChromaDB**

```bash
# Install ChromaDB on your server
pip install chromadb

# Run ChromaDB server
chroma run --host 0.0.0.0 --port 8000
```

### 2. Application Configuration

```bash
# Clone the repository
git clone <repository-url>
cd extractor

# Copy external database template
cp .env.external .env

# Edit configuration
nano .env
```

**Configure External MongoDB:**

```bash
# Option 1: Individual parameters
EXTERNAL_MONGODB_HOST=your-cluster.mongodb.net
EXTERNAL_MONGODB_PORT=27017
EXTERNAL_MONGODB_DATABASE=rpger
EXTERNAL_MONGODB_USERNAME=your_username
EXTERNAL_MONGODB_PASSWORD=your_password

# Option 2: Full connection string (overrides individual parameters)
EXTERNAL_MONGODB_CONNECTION_STRING=mongodb+srv://user:pass@cluster.mongodb.net/rpger?retryWrites=true&w=majority
```

**Configure External ChromaDB:**

```bash
# Option 1: Individual parameters
EXTERNAL_CHROMA_HOST=your-chromadb-host.com
EXTERNAL_CHROMA_PORT=8000

# Option 2: Full URL (overrides individual parameters)
EXTERNAL_CHROMA_BASE_URL=https://your-chromadb-instance.com/api/v1
```

### 3. Start Application

```bash
# Start the application
./start-external.sh

# Or manually:
docker-compose -f docker-compose.yml -f docker-compose.external.yml up -d
```

### 4. Verify Connections

```bash
# Check application health
curl http://localhost:5000/api/health

# Check application logs
docker logs extractor-app

# Test database connections through the app
curl -X POST http://localhost:5000/test_connections
```

## Database-Specific Configuration

### MongoDB Atlas Configuration

**Connection String Format:**
```
mongodb+srv://<username>:<password>@<cluster-name>.mongodb.net/<database>?retryWrites=true&w=majority
```

**Security Considerations:**
- Use database-specific users, not the root user
- Enable network access restrictions
- Use strong passwords
- Enable auditing in production

**Performance Optimization:**
- Choose appropriate cluster tier
- Configure read preferences
- Use appropriate indexes
- Monitor performance metrics

### Self-Hosted MongoDB

**Configuration Example:**
```bash
# /etc/mongod.conf
net:
  port: 27017
  bindIp: 0.0.0.0

security:
  authorization: enabled

storage:
  dbPath: /var/lib/mongodb
```

**User Setup:**
```javascript
// Connect as admin
use admin
db.createUser({
  user: "admin",
  pwd: "secure_password",
  roles: [ { role: "userAdminAnyDatabase", db: "admin" } ]
})

// Create application user
use rpger
db.createUser({
  user: "extractor_user",
  pwd: "secure_app_password",
  roles: [ { role: "readWrite", db: "rpger" } ]
})
```

### ChromaDB Configuration

**Hosted ChromaDB:**
- Follow provider-specific setup instructions
- Configure authentication tokens
- Set appropriate collection parameters

**Self-Hosted ChromaDB:**
```bash
# Basic setup
pip install chromadb

# Run with persistence
chroma run --host 0.0.0.0 --port 8000 --path /path/to/data

# Run with authentication (if configured)
chroma run --host 0.0.0.0 --port 8000 --auth-provider basic
```

## Networking and Security

### Network Configuration

**Firewall Rules:**
```bash
# Allow application to connect to MongoDB (example)
sudo ufw allow out 27017

# Allow application to connect to ChromaDB (example)
sudo ufw allow out 8000
```

**Docker Network Configuration:**
```yaml
# If databases are on the same host
networks:
  extractor-network:
    driver: bridge
  external-db-network:
    external: true
```

### SSL/TLS Configuration

**MongoDB with SSL:**
```bash
EXTERNAL_MONGODB_CONNECTION_STRING=mongodb+srv://user:pass@cluster.mongodb.net/rpger?ssl=true&authSource=admin
```

**ChromaDB with HTTPS:**
```bash
EXTERNAL_CHROMA_BASE_URL=https://your-chromadb-instance.com/api/v1
```

### Authentication

**MongoDB Authentication:**
- Use SCRAM-SHA-256 (default in MongoDB 4.0+)
- Implement role-based access control
- Regular password rotation

**ChromaDB Authentication:**
- Configure authentication tokens
- Use HTTPS for secure communication
- Implement proper access controls

## Monitoring and Maintenance

### Connection Monitoring

```bash
# Application-level monitoring
curl -s http://localhost:5000/api/health | jq '.mongodb, .chromadb'

# Database-level monitoring
# MongoDB: Use MongoDB Compass or Atlas monitoring
# ChromaDB: Check service-specific monitoring tools
```

### Performance Monitoring

**MongoDB Monitoring:**
- Atlas: Built-in monitoring dashboard
- Self-hosted: MongoDB Compass, mongostat, mongotop

**ChromaDB Monitoring:**
- API response times
- Collection sizes
- Query performance

### Backup Strategies

**MongoDB Backup:**
```bash
# Atlas: Automated backups available
# Self-hosted: Use mongodump
mongodump --host your-mongodb-host --db rpger --out /backup/path
```

**ChromaDB Backup:**
- Export collections using ChromaDB client
- Backup persistent data directory
- Use provider backup solutions

## Troubleshooting

### Common Connection Issues

1. **MongoDB Connection Failed**
   ```bash
   # Test connection manually
   mongosh "mongodb+srv://user:pass@cluster.mongodb.net/rpger"
   
   # Check network connectivity
   telnet your-mongodb-host 27017
   
   # Verify credentials
   # Check MongoDB Atlas network access settings
   ```

2. **ChromaDB Connection Failed**
   ```bash
   # Test API endpoint
   curl http://your-chromadb-host:8000/api/v1/heartbeat
   
   # Check network connectivity
   telnet your-chromadb-host 8000
   
   # Verify API credentials
   ```

3. **Application Configuration Issues**
   ```bash
   # Check environment variables
   docker exec extractor-app env | grep -E "(MONGODB|CHROMA)"
   
   # Check application logs
   docker logs extractor-app
   
   # Test configuration
   curl http://localhost:5000/api/health
   ```

### Network Connectivity

```bash
# Test from application container
docker exec extractor-app ping your-mongodb-host
docker exec extractor-app telnet your-chromadb-host 8000

# Check DNS resolution
docker exec extractor-app nslookup your-mongodb-host
```

### SSL/Certificate Issues

```bash
# Test SSL connection
openssl s_client -connect your-mongodb-host:27017

# Check certificate validity
curl -vI https://your-chromadb-instance.com
```

## Migration from Container Stack

### Data Migration

**Export from Container Stack:**
```bash
# Export MongoDB data
docker exec extractor-mongodb mongodump --db rpger --out /tmp/backup
docker cp extractor-mongodb:/tmp/backup ./mongodb-export

# Export ChromaDB data
# Use ChromaDB client to export collections
```

**Import to External Databases:**
```bash
# Import to external MongoDB
mongorestore --host your-external-mongodb --db rpger ./mongodb-export/rpger

# Import to external ChromaDB
# Use ChromaDB client to import collections
```

### Configuration Migration

```bash
# Update configuration
cp .env.containers .env.containers.backup
cp .env.external .env

# Update database connection settings
# Test connections
curl http://localhost:5000/api/health
```

## Cost Optimization

### MongoDB Atlas

- Choose appropriate cluster tier
- Use development clusters for testing
- Monitor usage and scale accordingly
- Consider reserved capacity for production

### ChromaDB Hosting

- Monitor collection sizes
- Optimize query patterns
- Use appropriate hosting tier
- Consider data retention policies

## Best Practices

1. **Security**
   - Use strong, unique passwords
   - Enable SSL/TLS encryption
   - Implement proper access controls
   - Regular security audits

2. **Performance**
   - Monitor database performance
   - Optimize queries and indexes
   - Use appropriate connection pooling
   - Cache frequently accessed data

3. **Reliability**
   - Implement proper error handling
   - Use connection retry logic
   - Monitor service health
   - Have backup and recovery procedures

4. **Cost Management**
   - Monitor usage and costs
   - Right-size database resources
   - Implement data lifecycle policies
   - Use cost alerts and budgets

## Next Steps

After successful setup:

1. **Performance Testing**: Test with your expected workload
2. **Monitoring Setup**: Implement comprehensive monitoring
3. **Backup Procedures**: Set up regular backup processes
4. **Security Review**: Conduct security assessment
5. **Documentation**: Document your specific configuration

For container stack setup, see [container-stack-setup.md](container-stack-setup.md).