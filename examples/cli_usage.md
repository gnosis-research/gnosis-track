# CLI Usage Examples

This document provides comprehensive examples of using the `gnosis-track` CLI tool.

## Installation and Setup

```bash
# Install gnosis-track
pip install -e .

# Check installation
gnosis-track --version

# Generate example configuration
gnosis-track env-example > .env

# Check system health
gnosis-track health
```

## Basic Commands

### Health Check
```bash
# Basic health check
gnosis-track health

# Verbose health check
gnosis-track -v health

# Health check with custom config
gnosis-track -c config/production.yaml health
```

### Configuration Management
```bash
# Show current configuration
gnosis-track config

# Export configuration to file
gnosis-track config-export --output my-config.yaml

# Use custom configuration file
gnosis-track -c /path/to/config.yaml health
```

## Installation Commands

### SeaweedFS Installation
```bash
# Install SeaweedFS automatically
gnosis-track install seaweedfs

# Install specific version
gnosis-track install seaweedfs --version 3.50

# Install to custom directory
gnosis-track install seaweedfs --install-dir /opt/seaweedfs

# Start SeaweedFS cluster
gnosis-track install start

# Check cluster status
gnosis-track install status

# Stop cluster
gnosis-track install stop
```

## Bucket Management

### Basic Bucket Operations
```bash
# List all buckets
gnosis-track bucket list

# Create a new bucket
gnosis-track bucket create validator-logs-dev

# Get bucket information
gnosis-track bucket info validator-logs

# Delete a bucket (careful!)
gnosis-track bucket delete old-logs --force
```

### Bucket Health and Maintenance
```bash
# Check bucket health
gnosis-track bucket health validator-logs

# Clean up old objects
gnosis-track bucket cleanup validator-logs --older-than 30d

# Verify bucket integrity
gnosis-track bucket verify validator-logs
```

## Log Management

### Streaming Logs
```bash
# Stream logs for a validator
gnosis-track logs stream --validator-uid 123

# Stream specific run
gnosis-track logs stream --validator-uid 123 --run-id run_20250126_103015

# Follow logs (tail -f style)
gnosis-track logs stream --validator-uid 123 --follow

# Filter by log level
gnosis-track logs stream --validator-uid 123 --level ERROR

# Limit number of logs
gnosis-track logs stream --validator-uid 123 --limit 50
```

### Exporting Logs
```bash
# Export logs to JSON
gnosis-track logs export --validator-uid 123 --format json --output logs.json

# Export to CSV
gnosis-track logs export --validator-uid 123 --format csv --output logs.csv

# Export to plain text
gnosis-track logs export --validator-uid 123 --format txt --output logs.txt

# Export specific run
gnosis-track logs export --validator-uid 123 --run-id run_20250126_103015

# Export with filters
gnosis-track logs export --validator-uid 123 --level ERROR --limit 1000
```

### Log Analysis
```bash
# Get log statistics
gnosis-track logs stats --validator-uid 123

# Search logs
gnosis-track logs search "error" --validator-uid 123

# Search across all validators
gnosis-track logs search "memory" --all-validators

# Search with regex
gnosis-track logs search "error|warning" --regex --validator-uid 123
```

## Web UI

### Starting the Web Interface
```bash
# Start UI with default settings
gnosis-track ui

# Start on specific host/port
gnosis-track ui --host 0.0.0.0 --port 8080

# Start with authentication enabled
gnosis-track ui --auth

# Start in debug mode
gnosis-track ui --debug

# Start with custom config
gnosis-track -c production.yaml ui --host 0.0.0.0 --port 443
```

## System Monitoring

### Metrics and Performance
```bash
# Show system metrics
gnosis-track metrics

# Show detailed metrics
gnosis-track -v metrics

# Export metrics to file
gnosis-track metrics --output metrics.json

# Monitor metrics continuously
watch -n 5 gnosis-track metrics
```

## Advanced Usage

### Production Deployment
```bash
# Production health check with alerting
gnosis-track -c production.yaml health || curl -X POST "$SLACK_WEBHOOK" \
  -d '{"text":"⚠️ Gnosis-Track health check failed"}'

# Automated log cleanup
gnosis-track bucket cleanup validator-logs --older-than 365d --dry-run
gnosis-track bucket cleanup validator-logs --older-than 365d

# Backup verification
gnosis-track bucket verify validator-logs --repair
```

### Batch Operations
```bash
# Export logs for multiple validators
for uid in 100 101 102; do
  gnosis-track logs export --validator-uid $uid --format json \
    --output "logs_validator_${uid}.json"
done

# Health check all components
gnosis-track health && \
gnosis-track bucket health validator-logs && \
gnosis-track metrics > /dev/null && \
echo "✅ All systems healthy"
```

### Integration with Scripts
```bash
#!/bin/bash
# monitoring_script.sh

CONFIG_FILE="/etc/gnosis-track/production.yaml"
LOG_FILE="/var/log/gnosis-track/monitor.log"

# Function to log with timestamp
log() {
    echo "$(date '+%Y-%m-%d %H:%M:%S') $1" >> "$LOG_FILE"
}

# Check health
if gnosis-track -c "$CONFIG_FILE" health > /dev/null 2>&1; then
    log "✅ Health check passed"
else
    log "❌ Health check failed"
    # Send alert
    curl -X POST "$SLACK_WEBHOOK" -d '{"text":"🚨 Gnosis-Track health check failed"}'
fi

# Check disk usage
METRICS=$(gnosis-track -c "$CONFIG_FILE" metrics --format json)
DISK_USAGE=$(echo "$METRICS" | jq -r '.storage.disk_usage_percent')

if (( $(echo "$DISK_USAGE > 80" | bc -l) )); then
    log "⚠️ High disk usage: ${DISK_USAGE}%"
fi
```

### Environment Variables
```bash
# Set common environment variables
export SEAWEED_S3_ENDPOINT="seaweed-cluster.internal:8333"
export SEAWEED_ACCESS_KEY="your-access-key"
export SEAWEED_SECRET_KEY="your-secret-key"
export JWT_SECRET="your-jwt-secret"

# Use environment variables with CLI
gnosis-track health

# Override with command line
gnosis-track -c custom.yaml health
```

## Troubleshooting Commands

### Debugging Connection Issues
```bash
# Verbose health check
gnosis-track -v health

# Test specific endpoint
gnosis-track bucket list --endpoint localhost:8333

# Check configuration
gnosis-track config

# Verify environment
gnosis-track env-example
```

### Performance Testing
```bash
# Test upload performance
time gnosis-track bucket create test-performance
time gnosis-track logs export --validator-uid 123 --format json --output /dev/null

# Monitor during operations
gnosis-track metrics & 
gnosis-track logs stream --validator-uid 123 --follow
```

## Configuration Examples

### Development Setup
```bash
# Quick development setup
gnosis-track install seaweedfs
gnosis-track install start
gnosis-track bucket create dev-logs
gnosis-track ui --debug
```

### Production Setup
```bash
# Production deployment
gnosis-track -c production.yaml health
gnosis-track -c production.yaml bucket create validator-logs
gnosis-track -c production.yaml ui --host 0.0.0.0 --port 443 --auth
```

### Docker Integration
```bash
# Use with Docker
docker run -v $(pwd)/config:/config \
  -p 8080:8080 \
  gnosis-track:latest \
  gnosis-track -c /config/production.yaml ui --host 0.0.0.0
```

## Help and Documentation

```bash
# Get help for any command
gnosis-track --help
gnosis-track logs --help
gnosis-track logs stream --help

# Show version
gnosis-track --version

# Verbose output for debugging
gnosis-track -v <command>
```

## Common Workflows

### Daily Operations
```bash
# Morning health check
gnosis-track health

# Check overnight logs
gnosis-track logs stats --validator-uid 123

# Clean up old logs
gnosis-track bucket cleanup validator-logs --older-than 7d --dry-run
```

### Incident Response
```bash
# Quick error check
gnosis-track logs stream --validator-uid 123 --level ERROR --limit 100

# Export error logs for analysis
gnosis-track logs export --validator-uid 123 --level ERROR \
  --output "incident_$(date +%Y%m%d_%H%M%S).json"

# Check system health
gnosis-track health && gnosis-track metrics
```