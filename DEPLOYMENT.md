# Deployment Guide

## Overview

This guide provides step-by-step instructions for deploying the Freshdesk Spam Filter in various environments, from development to production.

## Prerequisites

### System Requirements

- **Operating System**: Linux, macOS, or Windows
- **Python**: 3.8 or higher
- **Memory**: Minimum 2GB RAM (4GB+ recommended for larger models)
- **Storage**: 5GB+ free space for OLLAMA models
- **Network**: Internet access for Freshdesk API and OLLAMA model downloads

### Required Services

1. **Freshdesk Account** with API access
2. **OLLAMA** installed and configured
3. **Python Environment** with pip

## Quick Deployment

### 1. System Preparation

```bash
# Update system packages (Ubuntu/Debian)
sudo apt update && sudo apt upgrade -y

# Install Python and pip (if not already installed)
sudo apt install python3 python3-pip python3-venv git -y

# Install OLLAMA
curl -fsSL https://ollama.ai/install.sh | sh
```

### 2. Application Setup

```bash
# Clone the repository
git clone <repository-url>
cd freshdesk-spam-filter

# Create virtual environment
python3 -m venv venv
source venv/bin/activate

# Install dependencies
pip install -r requirements.txt

# Configure application
cp .env.example .env
nano .env  # Edit with your settings
```

### 3. OLLAMA Setup

```bash
# Start OLLAMA service
ollama serve &

# Pull the AI model
ollama pull llama3.2

# Verify model is available
ollama list
```

### 4. Validation and Testing

```bash
# Test configuration
python test_setup.py

# Run a single test cycle
python main.py --once

# Start continuous monitoring
python main.py
```

## Environment-Specific Deployments

### Development Environment

**Purpose**: Local development and testing

```bash
# Development setup
git clone <repository-url>
cd freshdesk-spam-filter

# Create development environment
python3 -m venv dev-env
source dev-env/bin/activate

# Install with development dependencies
pip install -r requirements.txt
pip install pytest black mypy flake8

# Configure for development
cp .env.example .env.dev
ln -sf .env.dev .env

# Edit configuration for development
nano .env
```

**Development Configuration:**
```env
FRESHDESK_DOMAIN=test-company.freshdesk.com
FRESHDESK_API_KEY=test_api_key
OLLAMA_MODEL=llama3.2
SPAM_THRESHOLD=0.6
CHECK_INTERVAL_MINUTES=1
LOG_LEVEL=DEBUG
```

### Staging Environment

**Purpose**: Pre-production testing with production-like settings

```bash
# Staging deployment
git clone <repository-url>
cd freshdesk-spam-filter

# Create staging environment
python3 -m venv staging-env
source staging-env/bin/activate

# Install production dependencies
pip install -r requirements.txt

# Configure for staging
cp .env.example .env.staging
ln -sf .env.staging .env

# Edit configuration
nano .env
```

**Staging Configuration:**
```env
FRESHDESK_DOMAIN=staging-company.freshdesk.com
FRESHDESK_API_KEY=staging_api_key
OLLAMA_MODEL=llama3.2
SPAM_THRESHOLD=0.7
CHECK_INTERVAL_MINUTES=3
LOG_LEVEL=INFO
```

### Production Environment

**Purpose**: Live production deployment

```bash
# Production deployment
git clone <repository-url>
cd freshdesk-spam-filter

# Create production environment
python3 -m venv prod-env
source prod-env/bin/activate

# Install production dependencies
pip install -r requirements.txt

# Configure for production
cp .env.example .env.prod
ln -sf .env.prod .env

# Secure configuration file
chmod 600 .env
```

**Production Configuration:**
```env
FRESHDESK_DOMAIN=company.freshdesk.com
FRESHDESK_API_KEY=production_api_key
OLLAMA_MODEL=llama3.2
SPAM_THRESHOLD=0.7
CHECK_INTERVAL_MINUTES=5
LOG_LEVEL=INFO
```

## Service Management

### Systemd Service (Linux)

Create a systemd service for automatic startup and management:

```bash
# Create service file
sudo nano /etc/systemd/system/freshdesk-spam-filter.service
```

**Service Configuration:**
```ini
[Unit]
Description=Freshdesk Spam Filter
After=network.target

[Service]
Type=simple
User=spam-filter
Group=spam-filter
WorkingDirectory=/opt/freshdesk-spam-filter
Environment=PATH=/opt/freshdesk-spam-filter/venv/bin
ExecStart=/opt/freshdesk-spam-filter/venv/bin/python main.py
Restart=always
RestartSec=10

[Install]
WantedBy=multi-user.target
```

**Service Management:**
```bash
# Reload systemd
sudo systemctl daemon-reload

# Enable service
sudo systemctl enable freshdesk-spam-filter

# Start service
sudo systemctl start freshdesk-spam-filter

# Check status
sudo systemctl status freshdesk-spam-filter

# View logs
sudo journalctl -u freshdesk-spam-filter -f
```

### Docker Deployment

**Dockerfile:**
```dockerfile
FROM python:3.9-slim

# Install system dependencies
RUN apt-get update && apt-get install -y \
    curl \
    && rm -rf /var/lib/apt/lists/*

# Install OLLAMA
RUN curl -fsSL https://ollama.ai/install.sh | sh

# Set working directory
WORKDIR /app

# Copy requirements and install Python dependencies
COPY requirements.txt .
RUN pip install --no-cache-dir -r requirements.txt

# Copy application code
COPY . .

# Create non-root user
RUN useradd -m -u 1000 spam-filter
USER spam-filter

# Expose OLLAMA port
EXPOSE 11434

# Start script
CMD ["python", "main.py"]
```

**Docker Compose:**
```yaml
version: '3.8'

services:
  spam-filter:
    build: .
    environment:
      - FRESHDESK_DOMAIN=${FRESHDESK_DOMAIN}
      - FRESHDESK_API_KEY=${FRESHDESK_API_KEY}
      - OLLAMA_HOST=http://ollama:11434
    depends_on:
      - ollama
    restart: unless-stopped

  ollama:
    image: ollama/ollama
    ports:
      - "11434:11434"
    volumes:
      - ollama_data:/root/.ollama
    restart: unless-stopped

volumes:
  ollama_data:
```

**Docker Deployment:**
```bash
# Build and start
docker-compose up -d

# Pull AI model
docker-compose exec ollama ollama pull llama3.2

# View logs
docker-compose logs -f spam-filter
```

## Cloud Deployments

### AWS EC2

**Instance Setup:**
```bash
# Launch EC2 instance (t3.medium or larger recommended)
# Connect via SSH

# Update system
sudo yum update -y

# Install Python and Git
sudo yum install python3 python3-pip git -y

# Install OLLAMA
curl -fsSL https://ollama.ai/install.sh | sh

# Deploy application
git clone <repository-url>
cd freshdesk-spam-filter
python3 -m venv venv
source venv/bin/activate
pip install -r requirements.txt

# Configure and start
cp .env.example .env
nano .env
python main.py
```

### Google Cloud Platform

**Compute Engine Setup:**
```bash
# Create VM instance
gcloud compute instances create spam-filter-vm \
    --image-family=ubuntu-2004-lts \
    --image-project=ubuntu-os-cloud \
    --machine-type=e2-standard-2 \
    --zone=us-central1-a

# SSH into instance
gcloud compute ssh spam-filter-vm

# Follow standard deployment steps
```

### Azure Virtual Machine

**VM Setup:**
```bash
# Create resource group
az group create --name spam-filter-rg --location eastus

# Create VM
az vm create \
    --resource-group spam-filter-rg \
    --name spam-filter-vm \
    --image UbuntuLTS \
    --size Standard_B2s \
    --admin-username azureuser \
    --generate-ssh-keys

# SSH into VM
az vm show --resource-group spam-filter-rg --name spam-filter-vm --show-details --query publicIps -o tsv
ssh azureuser@<public-ip>

# Follow standard deployment steps
```

## Monitoring and Maintenance

### Log Management

**Log Rotation:**
```bash
# Create logrotate configuration
sudo nano /etc/logrotate.d/freshdesk-spam-filter
```

```
/opt/freshdesk-spam-filter/spam_filter.log {
    daily
    rotate 30
    compress
    delaycompress
    missingok
    notifempty
    create 644 spam-filter spam-filter
    postrotate
        systemctl reload freshdesk-spam-filter
    endscript
}
```

### Health Monitoring

**Health Check Script:**
```bash
#!/bin/bash
# health-check.sh

# Check if service is running
if ! systemctl is-active --quiet freshdesk-spam-filter; then
    echo "Service is not running"
    exit 1
fi

# Check if OLLAMA is responding
if ! curl -s http://localhost:11434/api/tags > /dev/null; then
    echo "OLLAMA is not responding"
    exit 1
fi

# Check log for recent activity
if ! tail -n 100 /opt/freshdesk-spam-filter/spam_filter.log | grep -q "$(date '+%Y-%m-%d')"; then
    echo "No recent log activity"
    exit 1
fi

echo "All checks passed"
exit 0
```

### Backup and Recovery

**Configuration Backup:**
```bash
# Backup configuration
cp .env .env.backup.$(date +%Y%m%d)

# Backup logs
tar -czf logs-backup-$(date +%Y%m%d).tar.gz *.log
```

**Recovery Procedure:**
```bash
# Restore configuration
cp .env.backup.YYYYMMDD .env

# Restart service
sudo systemctl restart freshdesk-spam-filter

# Verify operation
python test_setup.py
```

## Security Considerations

### Network Security

- **Firewall**: Only allow necessary ports (22 for SSH, 11434 for OLLAMA if remote)
- **VPN**: Consider VPN access for remote management
- **SSL/TLS**: Use HTTPS for all external communications

### Application Security

- **User Permissions**: Run service as non-root user
- **File Permissions**: Secure configuration files (chmod 600)
- **API Keys**: Rotate regularly and monitor usage
- **Updates**: Keep system and dependencies updated

### Monitoring Security

- **Log Monitoring**: Monitor for suspicious activity
- **Access Logs**: Track who accesses the system
- **API Monitoring**: Monitor Freshdesk API usage

## Troubleshooting Deployment

### Common Issues

1. **OLLAMA Connection Failed**:
   ```bash
   # Check OLLAMA service
   systemctl status ollama
   
   # Restart OLLAMA
   sudo systemctl restart ollama
   ```

2. **Freshdesk API Errors**:
   ```bash
   # Test API connectivity
   curl -u "API_KEY:X" https://domain.freshdesk.com/api/v2/tickets
   ```

3. **Permission Errors**:
   ```bash
   # Fix file permissions
   sudo chown -R spam-filter:spam-filter /opt/freshdesk-spam-filter
   chmod 600 .env
   ```

4. **Memory Issues**:
   ```bash
   # Check memory usage
   free -h
   
   # Use smaller model
   ollama pull phi3
   ```

### Performance Optimization

- **Model Selection**: Choose appropriate model for your hardware
- **Batch Size**: Adjust MAX_TICKETS_PER_BATCH based on performance
- **Check Interval**: Balance responsiveness vs. resource usage
- **Log Level**: Use INFO or WARNING in production

## Scaling Considerations

### Horizontal Scaling

- Deploy multiple instances for different Freshdesk domains
- Use load balancer for high availability
- Implement shared configuration management

### Vertical Scaling

- Increase instance size for better performance
- Use larger OLLAMA models for better accuracy
- Optimize batch processing parameters

### High Availability

- Deploy across multiple availability zones
- Implement health checks and auto-recovery
- Use managed services where possible
