#!/usr/bin/env python3
"""
Gnosis-Track: Open Source Centralized Logging for Bittensor Subnets
Drop-in replacement for WandB with automatic log streaming + manual logging

🌟 Business Model:
- Self-hosted: Free (deploy your own SeaweedFS + UI)  
- Managed Service: Paid (we handle infrastructure, scaling, backups)

Usage in validator code:
    import gnosis_track
    
    # Initialize once (similar to wandb.init)
    gnosis_track.init(
        config=config,
        wallet=wallet, 
        project="my-subnet-validators",
        uid=uid,
        # For managed service
        # api_key="gt_xxxxx",  # Get from gnosis-track.com
        # endpoint="https://api.gnosis-track.com"
    )
    
    # All bt.logging calls are automatically captured!
    bt.logging.info("This goes to Gnosis-Track automatically")
    
    # Optional manual logging (like wandb.log)
    gnosis_track.log({"step": step, "scores": scores})
"""

import os
import sys
import time
import threading
import logging
import io
from typing import Dict, Any, Optional, Union
from datetime import datetime
from contextlib import redirect_stdout, redirect_stderr
import bittensor as bt

from gnosis_track.logging import ValidatorLogger


class LogCapture:
    """Captures all logging output and streams to Gnosis-Track."""
    
    def __init__(self, gnosis_logger):
        self.gnosis_logger = gnosis_logger
        self.original_handlers = []
        self.is_capturing = False
        
    def start_capture(self):
        """Start capturing all Python logging."""
        if self.is_capturing:
            return
            
        # Get the root logger
        root_logger = logging.getLogger()
        
        # Store original handlers
        self.original_handlers = root_logger.handlers.copy()
        
        # Create our custom handler
        gnosis_handler = GnosisLogHandler(self.gnosis_logger)
        gnosis_handler.setLevel(logging.DEBUG)
        
        # Add our handler
        root_logger.addHandler(gnosis_handler)
        
        # Capture bittensor logging specifically
        bt_logger = logging.getLogger('bittensor')
        if gnosis_handler not in bt_logger.handlers:
            bt_logger.addHandler(gnosis_handler)
        
        self.is_capturing = True
        
    def stop_capture(self):
        """Stop capturing logging."""
        if not self.is_capturing:
            return
            
        root_logger = logging.getLogger()
        
        # Remove our handlers
        for handler in root_logger.handlers.copy():
            if isinstance(handler, GnosisLogHandler):
                root_logger.removeHandler(handler)
        
        self.is_capturing = False


class GnosisLogHandler(logging.Handler):
    """Custom logging handler that sends logs to Gnosis-Track."""
    
    def __init__(self, gnosis_logger):
        super().__init__()
        self.gnosis_logger = gnosis_logger
        
    def emit(self, record):
        try:
            # Format the log message
            message = self.format(record)
            
            # Map Python log levels to our levels
            level_mapping = {
                'DEBUG': 'DEBUG',
                'INFO': 'INFO', 
                'WARNING': 'WARNING',
                'ERROR': 'ERROR',
                'CRITICAL': 'ERROR'
            }
            
            level = level_mapping.get(record.levelname, 'INFO')
            
            # Send to Gnosis-Track
            if self.gnosis_logger and hasattr(self.gnosis_logger, 'log_stdout'):
                self.gnosis_logger.log_stdout(message, level=level)
                
        except Exception:
            # Don't let logging errors break the main application
            pass


class GnosisTrack:
    """
    Main Gnosis-Track client for Bittensor subnets.
    
    🚀 Features:
    - Automatic log streaming (like WandB)
    - Manual metric logging
    - Self-hosted or managed service
    - Drop-in WandB replacement
    """
    
    def __init__(self):
        self.logger = None
        self.log_capture = None
        self.config = None
        self.wallet = None
        self.uid = None
        self.project = None
        self.run_id = None
        self.is_initialized = False
        self._log_queue = []
        self._background_thread = None
        self._should_stop = False
        self.managed_service = False
        
    def init(
        self,
        config: Any,
        wallet: bt.wallet,
        project: str = "subnet-validators",
        uid: Optional[int] = None,
        name: Optional[str] = None,
        tags: Optional[list] = None,
        notes: Optional[str] = None,
        # Managed service options
        api_key: Optional[str] = None,
        endpoint: Optional[str] = None,
        **kwargs
    ):
        """
        Initialize Gnosis-Track logging.
        
        Args:
            config: Bittensor config object
            wallet: Bittensor wallet  
            project: Project name for organizing logs
            uid: Validator UID
            name: Custom run name
            tags: List of tags for this run
            notes: Description/notes for this run
            api_key: API key for managed service (gt_xxxxx)
            endpoint: Managed service endpoint
        """
        try:
            self.config = config
            self.wallet = wallet
            self.uid = uid
            self.project = project
            
            # Check if Gnosis-Track is disabled
            if getattr(config, 'gnosis_track_off', False):
                bt.logging.warning("🔕 Gnosis-Track logging is disabled in config")
                return self
            
            # Generate run name
            timestamp = datetime.now().strftime("%Y-%m-%d_%H-%M-%S")
            self.run_id = name or f"validator-{uid}-{timestamp}"
            
            # Determine if using managed service
            self.managed_service = bool(api_key and endpoint)
            
            if self.managed_service:
                bt.logging.info(f"🌟 Using Gnosis-Track Managed Service: {endpoint}")
                # TODO: Implement managed service client
                self._init_managed_service(api_key, endpoint, config, wallet, uid)
            else:
                bt.logging.info("🏠 Using Self-Hosted Gnosis-Track")
                self._init_self_hosted(config, wallet, uid)
            
            # Prepare run configuration
            run_config = {
                "validator_uid": uid,
                "hotkey": wallet.hotkey.ss58_address,
                "coldkey": wallet.coldkey.ss58_address,
                "netuid": getattr(config, 'netuid', None),
                "project": project,
                "run_name": self.run_id,
                "chain_endpoint": getattr(config.subtensor, 'chain_endpoint', None) if hasattr(config, 'subtensor') else 'unknown',
                "tags": tags or [],
                "notes": notes or f"Validator {uid} on subnet {getattr(config, 'netuid', 'unknown')}",
                "start_time": datetime.now().isoformat(),
                "gnosis_track_version": "1.0.0",
                "service_type": "managed" if self.managed_service else "self_hosted",
                **kwargs
            }
            
            # Start the logging run
            if self.logger:
                self.logger.init_run(config=run_config, version_tag="gnosis_track_v1.0")
                
                # Start automatic log capture
                self.log_capture = LogCapture(self.logger)
                self.log_capture.start_capture()
                
                # Start background processing thread
                self._background_thread = threading.Thread(target=self._background_processor, daemon=True)
                self._background_thread.start()
                
                self.is_initialized = True
                bt.logging.success(f"✅ Gnosis-Track initialized: {self.run_id}")
                bt.logging.info(f"📊 Project: {project}")
                bt.logging.info(f"🆔 UID: {uid}")
                bt.logging.info(f"🔗 Service: {'Managed' if self.managed_service else 'Self-Hosted'}")
            
        except Exception as e:
            bt.logging.error(f"❌ Failed to initialize Gnosis-Track: {e}")
            bt.logging.warning("⚠️  Continuing without Gnosis-Track logging")
            
        return self
    
    def _init_self_hosted(self, config, wallet, uid):
        """Initialize for self-hosted deployment."""
        # Get configuration from bittensor config or environment
        gnosis_endpoint = (
            getattr(config, 'gnosis_track_endpoint', None) or 
            os.getenv('GNOSIS_TRACK_ENDPOINT', 'localhost:8333')
        )
        gnosis_bucket = (
            getattr(config, 'gnosis_track_bucket', None) or
            os.getenv('GNOSIS_TRACK_BUCKET', f'subnet-{getattr(config, "netuid", "unknown")}-logs')
        )
        gnosis_access_key = (
            getattr(config, 'gnosis_track_access_key', None) or
            os.getenv('GNOSIS_TRACK_ACCESS_KEY', 'admin')
        )
        gnosis_secret_key = (
            getattr(config, 'gnosis_track_secret_key', None) or
            os.getenv('GNOSIS_TRACK_SECRET_KEY', 'admin_secret_key')
        )
        
        # Initialize the ValidatorLogger for self-hosted SeaweedFS
        self.logger = ValidatorLogger(
            validator_uid=uid,
            wallet=wallet,
            seaweed_s3_endpoint=gnosis_endpoint,
            access_key=gnosis_access_key,
            secret_key=gnosis_secret_key,
            bucket_name=gnosis_bucket,
            encryption=True,
            compression=True,
            auto_start_local=getattr(config, 'gnosis_track_auto_start', False)  # Default false for production
        )
    
    def _init_managed_service(self, api_key, endpoint, config, wallet, uid):
        """Initialize for managed service (future implementation)."""
        # TODO: Implement managed service client
        # This would make HTTP requests to gnosis-track.com API
        bt.logging.warning("🚧 Managed service not yet implemented, falling back to self-hosted")
        self._init_self_hosted(config, wallet, uid)
    
    def log(self, metrics: Dict[str, Any], step: Optional[int] = None):
        """
        Log metrics manually (WandB-compatible API).
        
        Args:
            metrics: Dictionary of metrics to log
            step: Optional step number
        """
        if not self.is_initialized or not self.logger:
            return
        
        try:
            # Add metadata
            log_entry = {
                **metrics,
                "timestamp": datetime.now().isoformat(),
                "validator_uid": self.uid,
                "run_id": self.run_id,
                "log_type": "manual_metrics"
            }
            
            # Queue for background processing
            self._log_queue.append({
                "type": "metrics",
                "data": log_entry,
                "step": step,
                "timestamp": time.time()
            })
            
        except Exception as e:
            bt.logging.error(f"❌ Error queuing Gnosis-Track metrics: {e}")
    
    def log_stdout(self, message: str, level: str = "INFO"):
        """
        Log a text message with level.
        
        Args:
            message: Text message to log
            level: Log level (DEBUG, INFO, WARNING, ERROR, SUCCESS)
        """
        if not self.is_initialized or not self.logger:
            return
        
        try:
            self.logger.log_stdout(message, level=level)
        except Exception as e:
            bt.logging.error(f"❌ Error logging message to Gnosis-Track: {e}")
    
    def finish(self):
        """Finish the logging run (WandB-compatible API)."""
        if not self.is_initialized:
            return
        
        try:
            bt.logging.info("🔄 Finishing Gnosis-Track logging...")
            
            # Stop log capture
            if self.log_capture:
                self.log_capture.stop_capture()
            
            # Stop background thread
            self._should_stop = True
            if self._background_thread and self._background_thread.is_alive():
                self._background_thread.join(timeout=10)
            
            # Process remaining logs
            self._process_log_queue()
            
            # Finish the run
            if self.logger:
                self.logger.finish()
                self.logger.cleanup()
            
            bt.logging.success("✅ Gnosis-Track logging finished")
            
        except Exception as e:
            bt.logging.error(f"❌ Error finishing Gnosis-Track: {e}")
        
        finally:
            self.is_initialized = False
            self.logger = None
    
    def _background_processor(self):
        """Background thread to process log queue."""
        while not self._should_stop:
            try:
                self._process_log_queue()
                time.sleep(2)  # Process every 2 seconds
            except Exception as e:
                bt.logging.error(f"❌ Error in Gnosis-Track background processor: {e}")
                time.sleep(5)  # Wait longer on error
    
    def _process_log_queue(self):
        """Process pending logs in the queue."""
        if not self._log_queue or not self.logger:
            return
        
        # Process up to 20 logs at a time
        batch_size = min(20, len(self._log_queue))
        batch = self._log_queue[:batch_size]
        self._log_queue = self._log_queue[batch_size:]
        
        for log_entry in batch:
            try:
                if log_entry["type"] == "metrics":
                    self.logger.log(
                        log_entry["data"],
                        step=log_entry["step"]
                    )
            except Exception as e:
                bt.logging.error(f"❌ Error processing Gnosis-Track log: {e}")


# Global instance (WandB-compatible module pattern)
_global_instance = GnosisTrack()

# Module-level functions (WandB-compatible API)
def init(*args, **kwargs):
    """Initialize Gnosis-Track logging."""
    return _global_instance.init(*args, **kwargs)

def log(metrics: Dict[str, Any], step: Optional[int] = None):
    """Log metrics."""
    _global_instance.log(metrics, step)

def log_stdout(message: str, level: str = "INFO"):
    """Log a text message."""
    _global_instance.log_stdout(message, level)

def finish():
    """Finish logging run."""
    _global_instance.finish()

# Context manager support
class GnosisTrackRun:
    """Context manager for Gnosis-Track runs."""
    
    def __init__(self, *args, **kwargs):
        self.args = args
        self.kwargs = kwargs
        self.instance = None
    
    def __enter__(self):
        self.instance = GnosisTrack()
        return self.instance.init(*self.args, **self.kwargs)
    
    def __exit__(self, exc_type, exc_val, exc_tb):
        if self.instance:
            self.instance.finish()

def run(*args, **kwargs):
    """Create a context manager for a Gnosis-Track run."""
    return GnosisTrackRun(*args, **kwargs)


# Utility functions for subnet owners
def setup_subnet_config(
    netuid: int,
    endpoint: str = "localhost:8333",
    bucket: Optional[str] = None,
    access_key: str = "admin", 
    secret_key: str = "admin_secret_key"
):
    """
    Helper function for subnet owners to generate config template.
    
    Args:
        netuid: Subnet netuid
        endpoint: SeaweedFS endpoint
        bucket: Bucket name (defaults to subnet-{netuid}-logs)
        access_key: S3 access key
        secret_key: S3 secret key
        
    Returns:
        Configuration dict to add to validator config
    """
    bucket = bucket or f"subnet-{netuid}-logs"
    
    config = {
        "gnosis_track_endpoint": endpoint,
        "gnosis_track_bucket": bucket,
        "gnosis_track_access_key": access_key,
        "gnosis_track_secret_key": secret_key,
        "gnosis_track_off": False,  # Set to True to disable
        "gnosis_track_auto_start": False  # Set to True for local development
    }
    
    print("🔧 Gnosis-Track Configuration for Subnet {netuid}:")
    print("Add this to your validator config:")
    print()
    for key, value in config.items():
        print(f"    {key} = {repr(value)}")
    print()
    print(f"📊 Logs will be stored in bucket: {bucket}")
    print(f"🌐 SeaweedFS endpoint: {endpoint}")
    print(f"📱 Web UI: http://{endpoint.split(':')[0]}:8081")
    
    return config

if __name__ == "__main__":
    # Example usage for subnet owners
    print("🎯 Gnosis-Track: Open Source Centralized Logging")
    print("=" * 50)
    print()
    print("🏠 Self-Hosted (Free):")
    print("  - Deploy your own SeaweedFS + UI")  
    print("  - Full control over data")
    print("  - No monthly fees")
    print()
    print("☁️  Managed Service (Paid):")
    print("  - We handle infrastructure")
    print("  - Automatic scaling & backups")
    print("  - Premium support")
    print("  - Coming soon...")
    print()
    
    # Generate example config
    setup_subnet_config(netuid=13, endpoint="your-seaweedfs-server.com:8333")