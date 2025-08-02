# Validator Integration Guide

This guide shows how to integrate Gnosis-Track with your existing validator for enhanced logging and monitoring.

## 🔄 Simple Integration (Minimal Changes)

### Step 1: Install Gnosis-Track

```bash
pip install gnosis-track
```

### Step 2: Replace Validator Logger Import

In your `neurons/validator.py`, replace the existing logger import:

```python
# Remove this line:
# from utils.validator_minio_logger import ValidatorMinioLogger, ValidatorMinioLogCapture

# Add this line:
from gnosis_track.logging import ValidatorLogger, ValidatorLogCapture
```

### Step 3: Update Logger Initialization

Replace the existing logger initialization with the new one:

```python
# In your validator's __init__ method, replace:
# self.minio_logger = ValidatorMinioLogger(...)

# With:
self.logger = ValidatorLogger(
    validator_uid=self.uid,
    wallet=self.wallet,
    seaweed_s3_endpoint=getattr(self.config, 'seaweed_endpoint', 'localhost:8333'),
    access_key=getattr(self.config, 'access_key', 'admin'),
    secret_key=getattr(self.config, 'secret_key', 'admin_secret_key'),
    bucket_name=getattr(self.config, 'bucket_name', 'validator-logs'),
    encryption=True,           # Enhanced security
    compression=True,          # Reduce storage costs
    auto_start_local=True      # Automatically start SeaweedFS if needed
)

# Replace log capture initialization:
# self.minio_log_capture = ValidatorMinioLogCapture(self.minio_logger)
self.log_capture = ValidatorLogCapture(self.logger)
```

### Step 4: Update Method Calls

Replace all method calls throughout your validator:

```python
# Replace all instances of:
# self.minio_logger.method_name()

# With:
# self.logger.method_name()

# For example:
self.logger.init_run(
    config={
        "netuid": self.config.netuid,
        "chain_endpoint": self.config.subtensor.chain_endpoint,
        "block": self.block
    },
    version_tag=version_tag,
    scraper_providers=scraper_providers
)

# Log capture remains the same:
self.log_capture.__enter__()
# ... your code ...
self.log_capture.__exit__(None, None, None)
```

### Step 5: Update Configuration (Optional)

Add SeaweedFS configuration to your config:

```python
# In your config.py or configuration file:
seaweed_endpoint: str = "localhost:8333"
access_key: str = "admin"  
secret_key: str = "admin_secret_key"
bucket_name: str = "validator-logs"
```

## 🚀 Enhanced Integration (Full Features)

For advanced features, you can enhance your validator with additional capabilities:

### Advanced Logger Configuration

```python
from gnosis_track.logging import ValidatorLogger, ValidatorLogCapture
from gnosis_track.core import BucketManager, ConfigManager

class EnhancedValidator:
    def __init__(self):
        # Load configuration
        config_manager = ConfigManager()
        self.config = config_manager.get_config()
        
        # Initialize enhanced logger
        self.logger = ValidatorLogger(
            validator_uid=self.uid,
            wallet=self.wallet,
            seaweed_s3_endpoint=self.config.seaweedfs.s3_endpoint,
            access_key=self.config.seaweedfs.access_key,
            secret_key=self.config.seaweedfs.secret_key,
            bucket_name=self.config.logging.bucket_name,
            project_name=self.config.logging.project_name,
            encryption=self.config.security.encryption_enabled,
            compression=self.config.logging.compression_enabled,
        )
        
        # Initialize bucket manager for advanced operations
        self.bucket_manager = BucketManager(
            self.logger.seaweed_client,
            default_encryption=self.config.security.encryption_enabled
        )
        
        # Setup automatic log capture
        self.log_capture = ValidatorLogCapture(
            self.logger,
            capture_stdout=True,
            capture_stderr=True
        )
    
    def setup_logging(self):
        """Setup enhanced logging with automatic bucket management."""
        
        # Ensure bucket exists with proper configuration
        self.bucket_manager.ensure_bucket(
            bucket_name=self.config.logging.bucket_name,
            encryption=self.config.security.encryption_enabled,
            lifecycle_days=self.config.logging.retention_days,
            tags={
                "validator_uid": str(self.uid),
                "project": self.config.logging.project_name,
                "environment": "production"
            },
            description=f"Logging bucket for validator {self.uid}"
        )
        
        # Start logging session
        self.logger.init_run(
            config={
                "validator_uid": self.uid,
                "netuid": self.config.netuid,
                "hotkey": self.wallet.hotkey.ss58_address,
                "coldkey": self.wallet.coldkey.ss58_address,
                "chain_endpoint": self.config.subtensor.chain_endpoint,
                "network": self.config.subtensor.network,
                "version": self.get_version(),
                "features": {
                    "encryption": self.config.security.encryption_enabled,
                    "compression": self.config.logging.compression_enabled,
                    "cloud_backup": self.config.cloud_backup.enabled,
                }
            },
            version_tag=self.get_version(),
            scraper_providers=self.get_scraper_providers()
        )
        
        # Start log capture
        self.log_capture.__enter__()
        
        bt.logging.info(f"🚀 Enhanced logging initialized for validator {self.uid}")
    
    def log_metrics(self, step: int, metrics: dict):
        """Log metrics with enhanced metadata."""
        
        # Add system metrics
        enhanced_metrics = {
            **metrics,
            "system": {
                "memory_usage_mb": self.get_memory_usage(),
                "cpu_usage_percent": self.get_cpu_usage(),
                "disk_usage_percent": self.get_disk_usage(),
            },
            "network": {
                "connected_peers": len(self.metagraph.neurons),
                "sync_status": self.get_sync_status(),
            },
            "performance": {
                "processing_time_ms": self.get_processing_time(),
                "throughput_per_second": self.get_throughput(),
            }
        }
        
        self.logger.log(enhanced_metrics, step=step)
    
    def log_event(self, event_type: str, event_data: dict, level: str = "INFO"):
        """Log structured events."""
        
        event = {
            "event_type": event_type,
            "event_data": event_data,
            "validator_uid": self.uid,
            "timestamp": dt.datetime.now().isoformat(),
            "block_height": self.block,
        }
        
        self.logger.log_stdout(
            f"EVENT[{event_type}]: {json.dumps(event_data)}",
            level=level
        )
    
    def cleanup_logging(self):
        """Clean up logging resources."""
        
        # Exit log capture
        if hasattr(self, 'log_capture'):
            self.log_capture.__exit__(None, None, None)
        
        # Finish logging session
        if hasattr(self, 'logger'):
            self.logger.finish()
            self.logger.cleanup()
        
        bt.logging.info("🔧 Logging cleanup completed")
```

### Health Monitoring Integration

```python
def monitor_system_health(self):
    """Monitor and log system health metrics."""
    
    # Check SeaweedFS health
    if hasattr(self.logger, 'seaweed_client'):
        health = self.logger.seaweed_client.health_check()
        
        if health['status'] != 'healthy':
            self.log_event(
                "storage_health_warning",
                {
                    "status": health['status'],
                    "response_time_ms": health['response_time_ms'],
                    "error": health.get('error')
                },
                level="WARNING"
            )
    
    # Check bucket health
    if hasattr(self, 'bucket_manager'):
        bucket_health = self.bucket_manager.get_bucket_health(
            self.config.logging.bucket_name
        )
        
        if bucket_health['status'] != 'healthy':
            self.log_event(
                "bucket_health_warning", 
                bucket_health,
                level="WARNING"
            )
    
    # Log system metrics
    self.log_metrics(
        step=self.step,
        metrics={
            "health_check": {
                "storage_status": health.get('status', 'unknown'),
                "bucket_status": bucket_health.get('status', 'unknown'),
                "timestamp": dt.datetime.now().isoformat()
            }
        }
    )
```

## 📊 Web UI Integration

Start the web UI to monitor your validator logs in real-time:

```bash
# Start the UI server
gnosis-track ui --port 8080

# Or with authentication
gnosis-track ui --port 8080 --auth-required

# Or with custom configuration
gnosis-track ui --config production.yaml
```

Access the UI at `http://localhost:8080` to:

- View real-time log streams
- Search and filter logs
- Export logs in multiple formats
- Monitor system health
- Analyze performance metrics

## 🔧 Configuration Examples

### Basic Configuration (`config.yaml`)

```yaml
seaweedfs:
  s3_endpoint: "localhost:8333"
  access_key: "admin"
  secret_key: "admin_secret_key"
  use_ssl: false
  auto_start_local: true

security:
  encryption_enabled: true
  encryption_algorithm: "AES256-GCM"

logging:
  bucket_name: "validator-logs"
  project_name: "my-validator-project"
  compression_enabled: true
  retention_days: 90

ui:
  host: "0.0.0.0"
  port: 8080
  auth_required: false

monitoring:
  enabled: true
  collection_interval: 60
```

### Production Configuration (`production.yaml`)

```yaml
seaweedfs:
  s3_endpoint: "seaweed-cluster.internal:8333"
  access_key: "${SEAWEED_ACCESS_KEY}"
  secret_key: "${SEAWEED_SECRET_KEY}"
  use_ssl: true
  verify_ssl: true
  auto_start_local: false

security:
  encryption_enabled: true
  jwt_secret: "${JWT_SECRET}"
  tls_enabled: true
  tls_cert_file: "/etc/ssl/certs/gnosis-track.crt"
  tls_key_file: "/etc/ssl/private/gnosis-track.key"

logging:
  bucket_name: "validator-logs-prod"
  project_name: "production-validators"
  compression_enabled: true
  retention_days: 365
  export_formats: ["json", "csv", "parquet"]

ui:
  host: "0.0.0.0"
  port: 443
  auth_required: true

monitoring:
  enabled: true
  collection_interval: 30
  metrics_endpoint: "/metrics"

cloud_backup:
  enabled: true
  provider: "aws"
  bucket: "validator-logs-backup"
  schedule: "0 2 * * *"  # Daily at 2 AM
```

## 🚨 Error Handling

Add robust error handling for logging operations:

```python
def safe_log_operation(self, operation_func, *args, **kwargs):
    """Safely execute logging operations with fallback."""
    
    try:
        return operation_func(*args, **kwargs)
    except Exception as e:
        # Log to local file as fallback
        bt.logging.error(f"Logging operation failed: {e}")
        
        # Try to log error to local backup
        try:
            with open(f"validator_{self.uid}_backup.log", "a") as f:
                f.write(f"{dt.datetime.now().isoformat()} | ERROR | Logging failed: {e}\n")
        except:
            pass  # Even backup failed, continue operation
        
        return None

def resilient_logging_setup(self):
    """Setup logging with automatic retry and fallback."""
    
    max_retries = 3
    retry_delay = 5
    
    for attempt in range(max_retries):
        try:
            self.setup_logging()
            bt.logging.info("✅ Logging setup successful")
            return
        except Exception as e:
            bt.logging.warning(f"Logging setup attempt {attempt + 1} failed: {e}")
            
            if attempt < max_retries - 1:
                bt.logging.info(f"Retrying in {retry_delay} seconds...")
                time.sleep(retry_delay)
            else:
                bt.logging.error("❌ All logging setup attempts failed, using local fallback")
                self.setup_fallback_logging()

def setup_fallback_logging(self):
    """Setup basic file-based logging as fallback."""
    
    import logging
    
    # Setup local file logging
    log_file = f"validator_{self.uid}_{dt.datetime.now().strftime('%Y%m%d')}.log"
    
    logging.basicConfig(
        filename=log_file,
        level=logging.INFO,
        format='%(asctime)s | %(levelname)s | %(message)s'
    )
    
    bt.logging.info(f"📝 Fallback logging to: {log_file}")
```

This integration guide provides a complete path for upgrading your validator to use Gnosis-Track while maintaining reliability and adding powerful new features!