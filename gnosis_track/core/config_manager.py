"""
Configuration management for gnosis-track.

Handles loading, validation, and management of configuration settings
from various sources (files, environment variables, defaults).
"""

import os
import yaml
import json
from pathlib import Path
from typing import Any, Dict, Optional, Union
from pydantic import BaseModel, Field, validator
from dotenv import load_dotenv


class SeaweedFSConfig(BaseModel):
    """SeaweedFS connection configuration."""
    s3_endpoint: str = Field(default="localhost:8333", description="SeaweedFS S3 endpoint")
    access_key: str = Field(default="admin", description="S3 access key")
    secret_key: str = Field(default="admin_secret_key", description="S3 secret key")
    use_ssl: bool = Field(default=False, description="Use SSL/TLS for connections")
    verify_ssl: bool = Field(default=True, description="Verify SSL certificates")
    auto_start_local: bool = Field(default=True, description="Auto-start local instance if connection fails")
    timeout: int = Field(default=30, description="Connection timeout in seconds")
    max_retries: int = Field(default=3, description="Maximum retry attempts")


class SecurityConfig(BaseModel):
    """Security configuration."""
    encryption_enabled: bool = Field(default=True, description="Enable data encryption")
    encryption_algorithm: str = Field(default="AES256-GCM", description="Encryption algorithm")
    jwt_secret: Optional[str] = Field(default=None, description="JWT signing secret")
    jwt_expiry: str = Field(default="24h", description="JWT token expiry")
    tls_enabled: bool = Field(default=False, description="Enable TLS for web UI")
    tls_cert_file: Optional[str] = Field(default=None, description="TLS certificate file path")
    tls_key_file: Optional[str] = Field(default=None, description="TLS private key file path")


class LoggingConfig(BaseModel):
    """Logging configuration."""
    bucket_name: str = Field(default="validator-logs", description="Default logging bucket")
    project_name: str = Field(default="data-universe-validators", description="Project name")
    compression_enabled: bool = Field(default=True, description="Enable log compression")
    structured_logging: bool = Field(default=True, description="Use structured logging format")
    log_level: str = Field(default="INFO", description="Default log level")
    retention_days: int = Field(default=90, description="Log retention period in days")
    export_formats: list = Field(default=["json", "csv"], description="Supported export formats")
    
    @validator('log_level')
    def validate_log_level(cls, v):
        valid_levels = ['DEBUG', 'INFO', 'WARNING', 'ERROR', 'CRITICAL']
        if v.upper() not in valid_levels:
            raise ValueError(f"Log level must be one of: {valid_levels}")
        return v.upper()


class UIConfig(BaseModel):
    """UI server configuration."""
    host: str = Field(default="localhost", description="UI server host")
    port: int = Field(default=8080, description="UI server port")
    debug: bool = Field(default=False, description="Enable debug mode")
    auth_required: bool = Field(default=False, description="Require authentication")
    auto_refresh_interval: int = Field(default=2000, description="Auto-refresh interval in milliseconds")


class MonitoringConfig(BaseModel):
    """Monitoring and metrics configuration."""
    enabled: bool = Field(default=True, description="Enable monitoring")
    metrics_endpoint: str = Field(default="/metrics", description="Prometheus metrics endpoint")
    health_endpoint: str = Field(default="/health", description="Health check endpoint")
    collection_interval: int = Field(default=60, description="Metrics collection interval in seconds")


class CloudBackupConfig(BaseModel):
    """Cloud backup configuration."""
    enabled: bool = Field(default=False, description="Enable cloud backup")
    provider: str = Field(default="aws", description="Cloud provider (aws, gcs, azure)")
    bucket: Optional[str] = Field(default=None, description="Backup bucket name")
    schedule: str = Field(default="0 2 * * *", description="Backup schedule (cron format)")
    retention_days: int = Field(default=365, description="Backup retention period")


class GnosisTrackConfig(BaseModel):
    """Main configuration model for gnosis-track."""
    seaweedfs: SeaweedFSConfig = Field(default_factory=SeaweedFSConfig)
    security: SecurityConfig = Field(default_factory=SecurityConfig)
    logging: LoggingConfig = Field(default_factory=LoggingConfig)
    ui: UIConfig = Field(default_factory=UIConfig)
    monitoring: MonitoringConfig = Field(default_factory=MonitoringConfig)
    cloud_backup: CloudBackupConfig = Field(default_factory=CloudBackupConfig)


class ConfigManager:
    """
    Configuration manager for gnosis-track.
    
    Loads configuration from multiple sources in order of precedence:
    1. Environment variables
    2. Configuration files (YAML/JSON)
    3. Default values
    """
    
    def __init__(
        self,
        config_file: Optional[Union[str, Path]] = None,
        env_prefix: str = "GNOSIS_TRACK",
        load_dotenv_file: bool = True,
    ):
        """
        Initialize configuration manager.
        
        Args:
            config_file: Path to configuration file (YAML or JSON)
            env_prefix: Prefix for environment variables
            load_dotenv_file: Whether to load .env file
        """
        self.config_file = Path(config_file) if config_file else None
        self.env_prefix = env_prefix
        
        # Load .env file if it exists
        if load_dotenv_file:
            load_dotenv()
        
        # Load configuration
        self.config = self._load_config()
    
    def _load_config(self) -> GnosisTrackConfig:
        """Load configuration from all sources."""
        # Start with default config
        config_dict = {}
        
        # Load from file if specified
        if self.config_file and self.config_file.exists():
            config_dict = self._load_config_file(self.config_file)
        
        # Override with environment variables
        env_config = self._load_env_config()
        config_dict = self._deep_merge(config_dict, env_config)
        
        # Create and validate config model
        return GnosisTrackConfig(**config_dict)
    
    def _load_config_file(self, config_file: Path) -> Dict[str, Any]:
        """Load configuration from file (YAML or JSON)."""
        try:
            with open(config_file, 'r') as f:
                if config_file.suffix.lower() in ['.yaml', '.yml']:
                    return yaml.safe_load(f) or {}
                elif config_file.suffix.lower() == '.json':
                    return json.load(f) or {}
                else:
                    raise ValueError(f"Unsupported config file format: {config_file.suffix}")
        except Exception as e:
            raise ValueError(f"Failed to load config file {config_file}: {e}")
    
    def _load_env_config(self) -> Dict[str, Any]:
        """Load configuration from environment variables."""
        config = {}
        prefix = f"{self.env_prefix}_"
        
        for key, value in os.environ.items():
            if key.startswith(prefix):
                # Remove prefix and convert to nested dict
                config_key = key[len(prefix):].lower()
                self._set_nested_value(config, config_key, value)
        
        return config
    
    def _set_nested_value(self, config: Dict[str, Any], key: str, value: str) -> None:
        """Set nested configuration value from environment variable."""
        # Convert key format: SEAWEEDFS_S3_ENDPOINT -> seaweedfs.s3_endpoint
        parts = key.split('_')
        
        current = config
        for part in parts[:-1]:
            if part not in current:
                current[part] = {}
            current = current[part]
        
        # Convert string values to appropriate types
        final_key = parts[-1]
        current[final_key] = self._convert_env_value(value)
    
    def _convert_env_value(self, value: str) -> Any:
        """Convert environment variable string to appropriate type."""
        # Boolean values
        if value.lower() in ('true', 'yes', '1', 'on'):
            return True
        elif value.lower() in ('false', 'no', '0', 'off'):
            return False
        
        # Numeric values
        try:
            if '.' in value:
                return float(value)
            else:
                return int(value)
        except ValueError:
            pass
        
        # JSON arrays/objects
        if value.startswith(('[', '{')):
            try:
                return json.loads(value)
            except json.JSONDecodeError:
                pass
        
        # Return as string
        return value
    
    def _deep_merge(self, base: Dict[str, Any], override: Dict[str, Any]) -> Dict[str, Any]:
        """Deep merge two dictionaries."""
        result = base.copy()
        
        for key, value in override.items():
            if key in result and isinstance(result[key], dict) and isinstance(value, dict):
                result[key] = self._deep_merge(result[key], value)
            else:
                result[key] = value
        
        return result
    
    def get_config(self) -> GnosisTrackConfig:
        """Get the current configuration."""
        return self.config
    
    def get_seaweedfs_config(self) -> SeaweedFSConfig:
        """Get SeaweedFS configuration."""
        return self.config.seaweedfs
    
    def get_security_config(self) -> SecurityConfig:
        """Get security configuration."""
        return self.config.security
    
    def get_logging_config(self) -> LoggingConfig:
        """Get logging configuration."""
        return self.config.logging
    
    def get_ui_config(self) -> UIConfig:
        """Get UI configuration."""
        return self.config.ui
    
    def get_monitoring_config(self) -> MonitoringConfig:
        """Get monitoring configuration."""
        return self.config.monitoring
    
    def get_cloud_backup_config(self) -> CloudBackupConfig:
        """Get cloud backup configuration."""
        return self.config.cloud_backup
    
    def save_config(self, output_file: Union[str, Path], format: str = "yaml") -> None:
        """
        Save current configuration to file.
        
        Args:
            output_file: Output file path
            format: Output format ('yaml' or 'json')
        """
        output_path = Path(output_file)
        config_dict = self.config.dict()
        
        with open(output_path, 'w') as f:
            if format.lower() == 'yaml':
                yaml.dump(config_dict, f, default_flow_style=False, indent=2)
            elif format.lower() == 'json':
                json.dump(config_dict, f, indent=2)
            else:
                raise ValueError(f"Unsupported format: {format}")
    
    def validate_config(self) -> bool:
        """Validate the current configuration."""
        try:
            # Re-parse to trigger validation
            GnosisTrackConfig(**self.config.dict())
            return True
        except Exception as e:
            print(f"Configuration validation failed: {e}")
            return False
    
    def get_env_example(self) -> str:
        """Generate example .env file content."""
        examples = [
            "# Gnosis-Track Configuration",
            "# SeaweedFS Configuration",
            "GNOSIS_TRACK_SEAWEEDFS_S3_ENDPOINT=localhost:8333",
            "GNOSIS_TRACK_SEAWEEDFS_ACCESS_KEY=admin",
            "GNOSIS_TRACK_SEAWEEDFS_SECRET_KEY=admin_secret_key",
            "GNOSIS_TRACK_SEAWEEDFS_USE_SSL=false",
            "",
            "# Security Configuration",
            "GNOSIS_TRACK_SECURITY_ENCRYPTION_ENABLED=true",
            "GNOSIS_TRACK_SECURITY_JWT_SECRET=your-jwt-secret-here",
            "",
            "# Logging Configuration",
            "GNOSIS_TRACK_LOGGING_BUCKET_NAME=validator-logs",
            "GNOSIS_TRACK_LOGGING_LOG_LEVEL=INFO",
            "GNOSIS_TRACK_LOGGING_RETENTION_DAYS=90",
            "",
            "# UI Configuration",
            "GNOSIS_TRACK_UI_HOST=0.0.0.0",
            "GNOSIS_TRACK_UI_PORT=8080",
            "GNOSIS_TRACK_UI_AUTH_REQUIRED=false",
            "",
            "# Monitoring Configuration",
            "GNOSIS_TRACK_MONITORING_ENABLED=true",
            "",
            "# Cloud Backup Configuration",
            "GNOSIS_TRACK_CLOUD_BACKUP_ENABLED=false",
            "GNOSIS_TRACK_CLOUD_BACKUP_PROVIDER=aws",
            "GNOSIS_TRACK_CLOUD_BACKUP_BUCKET=gnosis-track-backup",
        ]
        
        return "\n".join(examples)