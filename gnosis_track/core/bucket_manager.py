"""
Secure bucket management for SeaweedFS.

Provides high-level bucket operations with security, lifecycle management,
replication, and monitoring capabilities.
"""

import json
import logging
import time
from datetime import datetime, timedelta
from typing import Any, Dict, List, Optional, Set

from gnosis_track.core.seaweed_client import SeaweedClient


logger = logging.getLogger(__name__)


class BucketManager:
    """
    Advanced bucket management for SeaweedFS.
    
    Features:
    - Automatic bucket creation and configuration
    - Lifecycle management (archival, deletion)
    - Replication management
    - Security policies
    - Monitoring and health checks
    """
    
    def __init__(
        self,
        seaweed_client: SeaweedClient,
        default_replication: str = "001",
        default_encryption: bool = True,
        monitoring_enabled: bool = True,
    ):
        """
        Initialize bucket manager.
        
        Args:
            seaweed_client: SeaweedFS client instance
            default_replication: Default replication setting (e.g., "001", "110")
            default_encryption: Enable encryption by default
            monitoring_enabled: Enable monitoring and metrics collection
        """
        self.client = seaweed_client
        self.default_replication = default_replication
        self.default_encryption = default_encryption
        self.monitoring_enabled = monitoring_enabled
        
        # Cache for bucket configurations
        self._bucket_configs: Dict[str, Dict[str, Any]] = {}
        self._last_config_refresh = 0
        self._config_cache_ttl = 300  # 5 minutes
        
        # Bucket naming conventions
        self.naming_rules = {
            "min_length": 3,
            "max_length": 63,
            "allowed_chars": "abcdefghijklmnopqrstuvwxyz0123456789-",
            "no_consecutive_dots": True,
            "no_start_end_dash": True,
        }
    
    def ensure_bucket(
        self,
        bucket_name: str,
        replication: Optional[str] = None,
        encryption: Optional[bool] = None,
        lifecycle_days: Optional[int] = None,
        tags: Optional[Dict[str, str]] = None,
        description: Optional[str] = None,
    ) -> bool:
        """
        Ensure a bucket exists with the specified configuration.
        
        Args:
            bucket_name: Name of the bucket
            replication: Replication setting (overrides default)
            encryption: Enable encryption (overrides default)
            lifecycle_days: Days after which objects are archived/deleted
            tags: Bucket tags for organization
            description: Human-readable description
            
        Returns:
            True if bucket was created or already exists
        """
        # Validate bucket name
        self._validate_bucket_name(bucket_name)
        
        # Use defaults if not specified
        replication = replication or self.default_replication
        encryption = encryption if encryption is not None else self.default_encryption
        
        try:
            # Check if bucket already exists
            if self.client.bucket_exists(bucket_name):
                logger.debug(f"Bucket {bucket_name} already exists")
                # Update configuration if needed
                self._update_bucket_config(
                    bucket_name, replication, encryption, lifecycle_days, tags, description
                )
                return True
            
            # Create the bucket
            self.client.create_bucket(bucket_name)
            
            # Configure the bucket
            self._configure_bucket(
                bucket_name, replication, encryption, lifecycle_days, tags, description
            )
            
            logger.info(f"✅ Created and configured bucket: {bucket_name}")
            return True
            
        except Exception as e:
            logger.error(f"Failed to ensure bucket {bucket_name}: {e}")
            raise
    
    def delete_bucket(
        self,
        bucket_name: str,
        force: bool = False,
        backup_objects: bool = True,
    ) -> bool:
        """
        Delete a bucket and optionally backup its contents.
        
        Args:
            bucket_name: Name of the bucket to delete
            force: Force deletion even if bucket contains objects
            backup_objects: Backup objects before deletion
            
        Returns:
            True if bucket was deleted successfully
        """
        try:
            if not self.client.bucket_exists(bucket_name):
                logger.warning(f"Bucket {bucket_name} does not exist")
                return True
            
            # List objects in bucket
            objects = self.client.list_objects(bucket_name)
            
            if objects and not force:
                raise ValueError(f"Bucket {bucket_name} contains {len(objects)} objects. Use force=True to delete.")
            
            # Backup objects if requested
            if backup_objects and objects:
                backup_bucket = f"{bucket_name}-backup-{int(time.time())}"
                self._backup_bucket_objects(bucket_name, backup_bucket, objects)
            
            # Delete all objects
            for obj in objects:
                self.client.delete_object(bucket_name, obj['Key'])
            
            # Delete bucket configuration
            self._delete_bucket_config(bucket_name)
            
            logger.info(f"🗑️ Deleted bucket: {bucket_name}")
            return True
            
        except Exception as e:
            logger.error(f"Failed to delete bucket {bucket_name}: {e}")
            raise
    
    def list_buckets(self, include_stats: bool = False) -> List[Dict[str, Any]]:
        """
        List all buckets with optional statistics.
        
        Args:
            include_stats: Include object count and size statistics
            
        Returns:
            List of bucket information dictionaries
        """
        try:
            buckets = self.client.list_buckets()
            
            result = []
            for bucket in buckets:
                bucket_info = {
                    "name": bucket["Name"],
                    "creation_date": bucket["CreationDate"],
                }
                
                # Add configuration if available
                config = self.get_bucket_config(bucket["Name"])
                if config:
                    bucket_info.update(config)
                
                # Add statistics if requested
                if include_stats:
                    stats = self._get_bucket_stats(bucket["Name"])
                    bucket_info.update(stats)
                
                result.append(bucket_info)
            
            return result
            
        except Exception as e:
            logger.error(f"Failed to list buckets: {e}")
            raise
    
    def get_bucket_config(self, bucket_name: str) -> Optional[Dict[str, Any]]:
        """Get configuration for a specific bucket."""
        try:
            # Check cache first
            if (bucket_name in self._bucket_configs and 
                time.time() - self._last_config_refresh < self._config_cache_ttl):
                return self._bucket_configs[bucket_name]
            
            # Try to get config from bucket metadata
            config_key = f".gnosis-track/config/{bucket_name}.json"
            
            if self.client.object_exists(bucket_name, config_key):
                config_data = self.client.get_object(bucket_name, config_key)
                config = json.loads(config_data.decode('utf-8'))
                
                # Cache the config
                self._bucket_configs[bucket_name] = config
                self._last_config_refresh = time.time()
                
                return config
            
            return None
            
        except Exception as e:
            logger.debug(f"Could not get config for bucket {bucket_name}: {e}")
            return None
    
    def set_bucket_lifecycle(
        self,
        bucket_name: str,
        archive_days: Optional[int] = None,
        delete_days: Optional[int] = None,
        transition_storage_class: str = "GLACIER",
    ) -> bool:
        """
        Set lifecycle policy for a bucket.
        
        Args:
            bucket_name: Name of the bucket
            archive_days: Days after which objects are archived
            delete_days: Days after which objects are deleted
            transition_storage_class: Storage class for archival
            
        Returns:
            True if lifecycle policy was set successfully
        """
        try:
            lifecycle_config = {
                "archive_days": archive_days,
                "delete_days": delete_days,
                "transition_storage_class": transition_storage_class,
                "last_updated": datetime.now().isoformat(),
            }
            
            # Update bucket configuration
            config = self.get_bucket_config(bucket_name) or {}
            config["lifecycle"] = lifecycle_config
            
            self._save_bucket_config(bucket_name, config)
            
            logger.info(f"Set lifecycle policy for bucket {bucket_name}")
            return True
            
        except Exception as e:
            logger.error(f"Failed to set lifecycle for bucket {bucket_name}: {e}")
            raise
    
    def cleanup_old_objects(
        self,
        bucket_name: str,
        days: int,
        dry_run: bool = True,
        prefix: str = "",
    ) -> Dict[str, Any]:
        """
        Clean up objects older than specified days.
        
        Args:
            bucket_name: Name of the bucket
            days: Delete objects older than this many days
            dry_run: Only simulate deletion, don't actually delete
            prefix: Only consider objects with this prefix
            
        Returns:
            Dictionary with cleanup statistics
        """
        try:
            cutoff_date = datetime.now() - timedelta(days=days)
            objects = self.client.list_objects(bucket_name, prefix=prefix)
            
            old_objects = []
            total_size = 0
            
            for obj in objects:
                if obj['LastModified'].replace(tzinfo=None) < cutoff_date:
                    old_objects.append(obj)
                    total_size += obj.get('Size', 0)
            
            if not dry_run:
                for obj in old_objects:
                    self.client.delete_object(bucket_name, obj['Key'])
                logger.info(f"Deleted {len(old_objects)} old objects from {bucket_name}")
            else:
                logger.info(f"Would delete {len(old_objects)} old objects from {bucket_name} (dry run)")
            
            return {
                "bucket": bucket_name,
                "cutoff_date": cutoff_date.isoformat(),
                "objects_found": len(old_objects),
                "total_size_bytes": total_size,
                "deleted": not dry_run,
                "dry_run": dry_run,
            }
            
        except Exception as e:
            logger.error(f"Failed to cleanup old objects in {bucket_name}: {e}")
            raise
    
    def get_bucket_health(self, bucket_name: str) -> Dict[str, Any]:
        """
        Get health status for a bucket.
        
        Args:
            bucket_name: Name of the bucket
            
        Returns:
            Dictionary with health information
        """
        try:
            start_time = time.time()
            
            # Basic connectivity test
            exists = self.client.bucket_exists(bucket_name)
            if not exists:
                return {
                    "status": "not_found",
                    "bucket": bucket_name,
                    "timestamp": datetime.now().isoformat(),
                }
            
            # Get bucket statistics
            stats = self._get_bucket_stats(bucket_name)
            
            # Test read/write performance
            test_key = f".gnosis-track/health-test-{int(time.time())}"
            test_data = json.dumps({"timestamp": datetime.now().isoformat()})
            
            # Write test
            write_start = time.time()
            self.client.put_object(bucket_name, test_key, test_data)
            write_time = time.time() - write_start
            
            # Read test
            read_start = time.time()
            self.client.get_object(bucket_name, test_key)
            read_time = time.time() - read_start
            
            # Cleanup test object
            self.client.delete_object(bucket_name, test_key)
            
            total_time = time.time() - start_time
            
            # Determine health status
            status = "healthy"
            if write_time > 5.0 or read_time > 5.0:
                status = "slow"
            elif total_time > 10.0:
                status = "degraded"
            
            return {
                "status": status,
                "bucket": bucket_name,
                "response_time_ms": int(total_time * 1000),
                "write_time_ms": int(write_time * 1000),
                "read_time_ms": int(read_time * 1000),
                "object_count": stats.get("object_count", 0),
                "total_size_bytes": stats.get("total_size_bytes", 0),
                "timestamp": datetime.now().isoformat(),
            }
            
        except Exception as e:
            return {
                "status": "error",
                "bucket": bucket_name,
                "error": str(e),
                "timestamp": datetime.now().isoformat(),
            }
    
    def _validate_bucket_name(self, bucket_name: str) -> None:
        """Validate bucket name against naming conventions."""
        rules = self.naming_rules
        
        if len(bucket_name) < rules["min_length"]:
            raise ValueError(f"Bucket name must be at least {rules['min_length']} characters")
        
        if len(bucket_name) > rules["max_length"]:
            raise ValueError(f"Bucket name must be at most {rules['max_length']} characters")
        
        for char in bucket_name:
            if char not in rules["allowed_chars"]:
                raise ValueError(f"Invalid character '{char}' in bucket name")
        
        if bucket_name.startswith('-') or bucket_name.endswith('-'):
            raise ValueError("Bucket name cannot start or end with a dash")
        
        if '..' in bucket_name:
            raise ValueError("Bucket name cannot contain consecutive dots")
    
    def _configure_bucket(
        self,
        bucket_name: str,
        replication: str,
        encryption: bool,
        lifecycle_days: Optional[int],
        tags: Optional[Dict[str, str]],
        description: Optional[str],
    ) -> None:
        """Configure a newly created bucket."""
        config = {
            "name": bucket_name,
            "replication": replication,
            "encryption": encryption,
            "created_at": datetime.now().isoformat(),
            "created_by": "gnosis-track",
            "version": "0.1.0",
        }
        
        if lifecycle_days:
            config["lifecycle"] = {
                "archive_days": lifecycle_days,
                "last_updated": datetime.now().isoformat(),
            }
        
        if tags:
            config["tags"] = tags
        
        if description:
            config["description"] = description
        
        self._save_bucket_config(bucket_name, config)
    
    def _update_bucket_config(
        self,
        bucket_name: str,
        replication: str,
        encryption: bool,
        lifecycle_days: Optional[int],
        tags: Optional[Dict[str, str]],
        description: Optional[str],
    ) -> None:
        """Update configuration for an existing bucket."""
        config = self.get_bucket_config(bucket_name) or {}
        
        config.update({
            "replication": replication,
            "encryption": encryption,
            "last_updated": datetime.now().isoformat(),
        })
        
        if lifecycle_days:
            config["lifecycle"] = {
                "archive_days": lifecycle_days,
                "last_updated": datetime.now().isoformat(),
            }
        
        if tags:
            config["tags"] = tags
        
        if description:
            config["description"] = description
        
        self._save_bucket_config(bucket_name, config)
    
    def _save_bucket_config(self, bucket_name: str, config: Dict[str, Any]) -> None:
        """Save bucket configuration to object storage."""
        config_key = f".gnosis-track/config/{bucket_name}.json"
        config_data = json.dumps(config, indent=2)
        
        self.client.put_object(
            bucket_name,
            config_key,
            config_data,
            content_type="application/json",
            metadata={"managed-by": "gnosis-track"}
        )
        
        # Update cache
        self._bucket_configs[bucket_name] = config
        self._last_config_refresh = time.time()
    
    def _delete_bucket_config(self, bucket_name: str) -> None:
        """Delete bucket configuration."""
        config_key = f".gnosis-track/config/{bucket_name}.json"
        
        if self.client.object_exists(bucket_name, config_key):
            self.client.delete_object(bucket_name, config_key)
        
        # Remove from cache
        if bucket_name in self._bucket_configs:
            del self._bucket_configs[bucket_name]
    
    def _get_bucket_stats(self, bucket_name: str) -> Dict[str, Any]:
        """Get statistics for a bucket."""
        try:
            objects = self.client.list_objects(bucket_name)
            
            total_size = sum(obj.get('Size', 0) for obj in objects)
            object_count = len(objects)
            
            # Calculate object type distribution
            type_counts = {}
            for obj in objects:
                key = obj['Key']
                if '.' in key:
                    ext = key.split('.')[-1].lower()
                    type_counts[ext] = type_counts.get(ext, 0) + 1
                else:
                    type_counts['no_extension'] = type_counts.get('no_extension', 0) + 1
            
            return {
                "object_count": object_count,
                "total_size_bytes": total_size,
                "total_size_mb": round(total_size / (1024 * 1024), 2),
                "type_distribution": type_counts,
                "last_calculated": datetime.now().isoformat(),
            }
            
        except Exception as e:
            logger.error(f"Failed to get stats for bucket {bucket_name}: {e}")
            return {
                "object_count": 0,
                "total_size_bytes": 0,
                "error": str(e),
            }
    
    def _backup_bucket_objects(
        self,
        source_bucket: str,
        backup_bucket: str,
        objects: List[Dict[str, Any]]
    ) -> None:
        """Backup objects from one bucket to another."""
        try:
            # Create backup bucket
            self.ensure_bucket(
                backup_bucket,
                tags={"purpose": "backup", "source": source_bucket}
            )
            
            # Copy all objects
            for obj in objects:
                self.client.copy_object(
                    source_bucket,
                    obj['Key'],
                    backup_bucket,
                    obj['Key']
                )
            
            logger.info(f"Backed up {len(objects)} objects to {backup_bucket}")
            
        except Exception as e:
            logger.error(f"Failed to backup objects: {e}")
            raise