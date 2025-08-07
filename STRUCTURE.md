# Project Structure

This document outlines the organization and structure of the gnosis-track project.

## 📁 Directory Structure

```
gnosis-track/
├── 📄 README.md                    # Main project documentation
├── 📄 LICENSE                      # Apache 2.0 license
├── 📄 VALIDATOR_INTEGRATION.md     # Validator integration guide
├── 📄 CLAUDE.md                    # AI assistant context file
├── 📦 pyproject.toml               # Modern Python packaging configuration
├── 📦 setup.py                     # Legacy setup script (for compatibility)
├── 📦 requirements.txt             # Production dependencies
├── 📦 MANIFEST.in                  # Package manifest for sdist
│
├── 📁 gnosis_track/                # Main package
│   ├── 📄 __init__.py              # Package initialization
│   │
│   ├── 📁 core/                    # Core system components
│   │   ├── 📄 config_manager.py    # Configuration management
│   │   ├── 📄 seaweed_client.py    # SeaweedFS S3 client
│   │   ├── 📄 bucket_manager.py    # S3 bucket operations
│   │   ├── 📄 auth_manager.py      # JWT authentication
│   │   └── 📄 token_manager.py     # API token management
│   │
│   ├── 📁 logging/                 # Logging system
│   │   ├── 📄 validator_logger.py  # Main validator logger
│   │   ├── 📄 log_streamer.py      # Log streaming and retrieval
│   │   └── 📄 log_formatter.py     # Log formatting utilities
│   │
│   ├── 📁 ui/                      # Web interface
│   │   ├── 📄 server.py            # FastAPI server with auto docs
│   │   ├── 📁 static/              # Static assets (CSS, JS, images)
│   │   └── 📁 templates/           # Jinja2 HTML templates
│   │
│   ├── 📁 cli/                     # Command-line interface
│   │   ├── 📄 main.py              # Main CLI entry point
│   │   ├── 📄 install.py           # Installation commands
│   │   ├── 📄 manage.py            # Management commands
│   │   └── 📄 logs.py              # Log-related commands
│   │
│   └── 📁 deployment/              # Deployment configurations
│
├── 📁 examples/                    # Usage examples and integrations
│   ├── 📄 basic_usage.py           # Basic API usage examples
│   ├── 📄 validator_integration.py # Validator integration example
│   ├── 📄 monitoring_alerting.py   # Monitoring and alerting setup
│   ├── 📄 gnosis_track_integration.py # Advanced integration
│   ├── 📄 cli_usage.md             # CLI usage documentation
│   └── 📁 configs/                 # Example configuration files
│
├── 📁 tests/                       # Test suite
│   ├── 📄 comprehensive_test_data.py # Comprehensive test data generator
│   ├── 📄 single_validator_test.py   # Single validator test
│   ├── 📄 infinite_random_logs.py   # Infinite log generator for testing
│   ├── 📄 populate_ui_data.py       # UI test data population
│   ├── 📄 test_fresh_import.py      # Fresh import testing
│   ├── 📄 test_server_imports.py    # Server import testing
│   └── 📄 deploy.sh                 # Deployment test script
│
└── 📁 scripts/                     # Utility scripts
    ├── 📄 create_token.py          # Token creation utility
    └── 📄 debug_runs.py            # Debug run inspection
```

## 🏗️ Architecture Overview

### Core Components

1. **SeaweedFS Client** (`core/seaweed_client.py`)
   - High-performance S3-compatible client
   - Connection management and retry logic
   - Health checking and monitoring

2. **Validator Logger** (`logging/validator_logger.py`) 
   - Main logging interface for validators
   - Structured logging with metadata
   - Real-time streaming capabilities

3. **Authentication System** (`core/auth_manager.py`, `core/token_manager.py`)
   - JWT-based authentication
   - WandB-style API tokens (gt_xxxxx format)
   - Role-based access control

4. **Web Interface** (`ui/server.py`)
   - FastAPI server with automatic OpenAPI documentation
   - Real-time log viewing and filtering
   - Responsive web UI

5. **CLI Tools** (`cli/main.py`)
   - Complete command-line interface
   - Token management
   - System health checking
   - Configuration management

### Data Flow

```
Validator → ValidatorLogger → SeaweedFS → LogStreamer → Web UI
                    ↓
                API Tokens ← TokenManager ← CLI/Web Auth
```

## 🛠️ Development Patterns

### Configuration Management
- YAML-based configuration with environment variable overrides
- Separate configs for development, testing, and production
- Validation using Pydantic models

### Error Handling
- Comprehensive exception handling with retry logic
- Graceful degradation for network issues
- Structured error logging

### Security
- Token-based authentication with configurable expiration
- CORS configuration for web UI
- Input validation and sanitization

### Testing
- Comprehensive test suite with realistic data generation
- Authentication testing with bypass detection
- Performance testing with infinite log generation

## 📚 Key Files

- **Entry Points**: `gnosis_track/cli/main.py`, `gnosis_track/ui/server.py`
- **Core Logic**: `gnosis_track/logging/validator_logger.py`
- **Configuration**: `examples/configs/`
- **Documentation**: `README.md`, `VALIDATOR_INTEGRATION.md`

## 🔄 Refactoring Completed

This structure was recently refactored to:

1. ✅ Remove 47MB of redundant test log files
2. ✅ Organize scripts into appropriate directories
3. ✅ Clean up unused imports and dependencies
4. ✅ Fix CLI token management function signatures
5. ✅ Improve .gitignore to prevent build artifacts
6. ✅ Consolidate related functionality

The codebase is now clean, well-organized, and ready for production use.