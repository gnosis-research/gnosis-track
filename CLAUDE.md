# CLAUDE.md

This file provides guidance to Claude Code (claude.ai/code) when working with code in this repository.

## Development Commands

**Installation & Setup:**
```bash
# Install in development mode
pip install -e .

# Install with optional dependencies
pip install -e ".[dev]"      # Development tools
pip install -e ".[ui]"       # Web UI dependencies
pip install -e ".[monitoring]" # Monitoring tools

# Install SeaweedFS locally
gnosis-track install --cluster-size 3
```

**Testing:**
```bash
# Run all tests
pytest

# Run with coverage
pytest --cov=gnosis_track

# Run integration tests (requires SeaweedFS)
pytest tests/integration/ --slow

# Run performance benchmarks
pytest tests/performance/ --benchmark

# Run specific test types
pytest -m unit          # Unit tests only
pytest -m integration   # Integration tests only
pytest -m slow          # Slow tests only
```

**Code Quality:**
```bash
# Format code
black gnosis_track/

# Sort imports
isort gnosis_track/

# Lint code
flake8 gnosis_track/

# Type checking
mypy gnosis_track/

# Run all quality checks
black gnosis_track/ && isort gnosis_track/ && flake8 gnosis_track/ && mypy gnosis_track/
```

**CLI Commands:**
```bash
# Main CLI entry point
gnosis-track --help

# Health check
gnosis-track health

# Start web UI
gnosis-track ui --port 8080

# Bucket management
gnosis-track bucket create test-bucket
gnosis-track bucket list
gnosis-track bucket stats test-bucket

# Log management
gnosis-track logs stream --validator-uid 0
gnosis-track logs export --format json
```

## Architecture Overview

**High-Level Structure:**
- **Core Layer**: SeaweedFS client, bucket management, configuration
- **Logging Layer**: Enhanced validator logging with encryption and compression
- **CLI Layer**: Command-line interface for management operations
- **UI Layer**: Web interface for log viewing and monitoring
- **Deployment Layer**: Docker and Kubernetes deployment tools

**Key Components:**

1. **SeaweedClient** (`gnosis_track/core/seaweed_client.py`):
   - S3-compatible wrapper around boto3 for SeaweedFS
   - Handles connection pooling, retries, and error handling
   - Provides health checks and performance optimizations

2. **BucketManager** (`gnosis_track/core/bucket_manager.py`):
   - High-level bucket operations with security and lifecycle management
   - Bucket configuration stored as JSON objects in `.gnosis-track/config/`
   - Supports replication, encryption, and automated cleanup

3. **ValidatorLogger** (`gnosis_track/logging/validator_logger.py`):
   - Drop-in replacement for existing validator logging systems
   - Automatic local SeaweedFS setup if remote connection fails
   - Structured logging with metrics, stdout/stderr capture, and real-time streaming
   - Supports both sync upload and buffered batch operations

4. **ConfigManager** (`gnosis_track/core/config_manager.py`):
   - YAML/JSON configuration with environment variable support
   - Hierarchical config loading (file -> env vars -> defaults)
   - Validation using Pydantic models

**Data Flow:**
```
Validator Code → ValidatorLogger → SeaweedClient → SeaweedFS Cluster
                      ↓
               BucketManager (config/lifecycle)
                      ↓
               Web UI / CLI (monitoring/management)
```

**Storage Organization:**
```
bucket-name/
├── validator_{uid}/
│   ├── {run_id}/
│   │   ├── config.json      # Run configuration
│   │   ├── logs_{timestamp}.json   # Log entries
│   │   ├── metrics_{timestamp}.json # Metrics data
│   │   └── summary.json     # Run summary
│   └── .gnosis-track/
│       └── config/
│           └── {bucket}.json # Bucket configuration
```

## Development Patterns

**Error Handling:**
- All operations should use try/catch with specific logging
- Client errors vs server errors should be distinguished
- Health checks should be non-blocking where possible

**Logging:**
- Use structured logging with `logger.info()`, `logger.error()`, etc.
- Include context (bucket names, object keys, run IDs) in log messages
- Avoid recursive logging in the ValidatorLogger itself

**Configuration:**
- All configuration should support environment variable overrides
- Use Pydantic models for validation and type safety  
- Provide sensible defaults for development environments

**Testing:**
- Unit tests for core logic without external dependencies
- Integration tests that require actual SeaweedFS instances
- Use pytest markers to categorize test types
- Mock external dependencies in unit tests

## SeaweedFS Integration Notes

**Local Development:**
- ValidatorLogger automatically downloads and starts local SeaweedFS if needed
- Local instance runs on ports 9333 (master), 8080 (volume), 8888 (filer), 8333 (S3)
- Storage directory: `~/validator_seaweedfs_storage/`

**Production Deployment:**
- Supports external SeaweedFS clusters via S3 endpoint configuration
- Handles SSL/TLS and authentication through boto3 S3 client
- Path-style addressing preferred for SeaweedFS compatibility

**Performance Considerations:**
- Uses connection pooling and adaptive retries
- Batches log uploads to reduce API calls
- Supports compression and encryption at the client level
- O(1) file access performance vs traditional tree-structured storage