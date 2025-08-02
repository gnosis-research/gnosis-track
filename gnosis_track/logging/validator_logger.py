"""
Enhanced validator logger using SeaweedFS.

Provides high-performance distributed logging with improved security,
real-time streaming, and cloud storage capabilities.
"""

import json
import datetime as dt
import io
import time
import platform
import urllib.request
import subprocess
import socket
import os
from typing import Dict, Any, Optional, List

from gnosis_track.core.seaweed_client import SeaweedClient
from gnosis_track.core.bucket_manager import BucketManager


class ValidatorLogger:
    """
    Enhanced SeaweedFS logger for validators.
    
    Provides enterprise-grade logging capabilities with:
    - High-performance distributed storage through SeaweedFS
    - Enhanced security with per-file encryption
    - Real-time log streaming and monitoring
    - Automatic cloud backup and archival
    - Structured logging with rich metadata
    """
    
    def __init__(
        self, 
        validator_uid: int,
        wallet,  # bt.wallet type
        seaweed_s3_endpoint: str = "localhost:8333",
        access_key: str = "admin",
        secret_key: str = "admin_secret_key",
        bucket_name: str = "validator-logs",
        project_name: str = "data-universe-validators",
        use_ssl: bool = False,
        auto_start_local: bool = True,
        encryption: bool = True,
        compression: bool = True,
    ):
        """
        Initialize enhanced validator logger.
        
        Args:
            validator_uid: Unique identifier for validator
            wallet: Bittensor wallet instance
            seaweed_s3_endpoint: SeaweedFS S3 endpoint
            access_key: S3 access key
            secret_key: S3 secret key
            bucket_name: Name of the logging bucket
            project_name: Project name for organization
            use_ssl: Whether to use SSL/TLS
            auto_start_local: Automatically start local SeaweedFS if needed
            encryption: Enable encryption for log data
            compression: Enable compression for log data
        """
        
        self.validator_uid = validator_uid
        self.wallet = wallet
        self.project_name = project_name
        self.bucket_name = bucket_name
        self.seaweed_s3_endpoint = seaweed_s3_endpoint
        self.access_key = access_key
        self.secret_key = secret_key
        self.use_ssl = use_ssl
        self.auto_start_local = auto_start_local
        self.encryption = encryption
        self.compression = compression
        
        # Local SeaweedFS process tracking
        self.local_seaweed_process = None
        self.local_s3_port = 8333
        self.local_master_port = 9333
        self.local_volume_port = 8080
        self.local_filer_port = 8888
        
        # Initialize SeaweedFS client
        self.seaweed_client = self._initialize_seaweed_client()
        self.bucket_manager = None
        
        if self.seaweed_client:
            self.bucket_manager = BucketManager(
                self.seaweed_client,
                default_encryption=encryption
            )
        
        # Run tracking
        self.run_start = None
        self.run_id = None
        self.current_log_buffer = []
        self.metrics_buffer = []
        self.last_upload_time = dt.datetime.now()
        
        # Configuration
        self.config_data = {}
        
        # Ensure bucket exists
        if self.bucket_manager:
            self._ensure_bucket_exists()
    
    def _initialize_seaweed_client(self) -> Optional[SeaweedClient]:
        """Initialize SeaweedFS client with fallback to local instance."""
        try:
            # First try to connect to specified endpoint
            endpoint_url = f"{'https' if self.use_ssl else 'http'}://{self.seaweed_s3_endpoint}"
            
            self._log_info(f"Attempting to connect to SeaweedFS at {endpoint_url}")
            
            client = SeaweedClient(
                endpoint_url=endpoint_url,
                access_key=self.access_key,
                secret_key=self.secret_key,
                use_ssl=self.use_ssl,
                verify_ssl=False,  # Often self-signed certs in local setups
            )
            
            # Test connection
            health = client.health_check()
            if health["status"] == "healthy":
                self._log_info(f"✅ Connected to SeaweedFS at {endpoint_url}")
                return client
            else:
                self._log_warning(f"SeaweedFS health check failed: {health}")
                
        except Exception as e:
            self._log_warning(f"Failed to connect to SeaweedFS at {self.seaweed_s3_endpoint}: {e}")
            
            if self.auto_start_local:
                self._log_info("Attempting to start local SeaweedFS instance...")
                if self._start_local_seaweedfs():
                    # Try connecting to local instance
                    try:
                        local_endpoint = f"http://localhost:{self.local_s3_port}"
                        client = SeaweedClient(
                            endpoint_url=local_endpoint,
                            access_key=self.access_key,
                            secret_key=self.secret_key,
                            use_ssl=False,
                        )
                        
                        # Wait for SeaweedFS to fully start
                        time.sleep(5)
                        health = client.health_check()
                        if health["status"] == "healthy":
                            self._log_info(f"✅ Connected to local SeaweedFS at {local_endpoint}")
                            return client
                        else:
                            self._log_error(f"Local SeaweedFS health check failed: {health}")
                            
                    except Exception as local_e:
                        self._log_error(f"Failed to connect to local SeaweedFS: {local_e}")
                        
            self._log_error("Could not establish SeaweedFS connection")
            return None
    
    def _start_local_seaweedfs(self) -> bool:
        """Start a local SeaweedFS instance."""
        try:
            # Create validator storage directory
            storage_dir = os.path.expanduser("~/validator_seaweedfs_storage")
            data_dir = os.path.join(storage_dir, "data")
            filer_dir = os.path.join(storage_dir, "filer")
            
            os.makedirs(data_dir, exist_ok=True)
            os.makedirs(filer_dir, exist_ok=True)
            
            # Download SeaweedFS binary if needed
            seaweed_binary = os.path.join(storage_dir, "weed")
            if not os.path.exists(seaweed_binary):
                self._log_info("Downloading SeaweedFS binary...")
                self._download_seaweedfs_binary(seaweed_binary)
            
            # Find available ports
            self.local_master_port = self._find_available_port(9333)
            self.local_volume_port = self._find_available_port(8080)
            self.local_filer_port = self._find_available_port(8888)
            self.local_s3_port = self._find_available_port(8333)
            
            # Start SeaweedFS master
            master_cmd = [
                seaweed_binary, "master",
                "-port", str(self.local_master_port),
                "-mdir", os.path.join(storage_dir, "master"),
                "-defaultReplication", "000",  # No replication for local setup
            ]
            
            self._log_info(f"Starting SeaweedFS master: {' '.join(master_cmd)}")
            master_process = subprocess.Popen(
                master_cmd,
                stdout=subprocess.PIPE,
                stderr=subprocess.PIPE,
                cwd=storage_dir
            )
            
            # Wait for master to start
            time.sleep(2)
            
            # Start SeaweedFS volume
            volume_cmd = [
                seaweed_binary, "volume",
                "-port", str(self.local_volume_port),
                "-dir", data_dir,
                "-mserver", f"localhost:{self.local_master_port}",
                "-max", "100",
            ]
            
            self._log_info(f"Starting SeaweedFS volume: {' '.join(volume_cmd)}")
            volume_process = subprocess.Popen(
                volume_cmd,
                stdout=subprocess.PIPE,
                stderr=subprocess.PIPE,
                cwd=storage_dir
            )
            
            # Wait for volume to start
            time.sleep(2)
            
            # Start SeaweedFS filer
            filer_cmd = [
                seaweed_binary, "filer",
                "-port", str(self.local_filer_port),
                "-master", f"localhost:{self.local_master_port}",
                "-dir", filer_dir,
            ]
            
            self._log_info(f"Starting SeaweedFS filer: {' '.join(filer_cmd)}")
            filer_process = subprocess.Popen(
                filer_cmd,
                stdout=subprocess.PIPE,
                stderr=subprocess.PIPE,
                cwd=storage_dir
            )
            
            # Wait for filer to start
            time.sleep(2)
            
            # Start SeaweedFS S3 gateway
            s3_cmd = [
                seaweed_binary, "s3",
                "-port", str(self.local_s3_port),
                "-filer", f"localhost:{self.local_filer_port}",
                "-config", os.path.join(storage_dir, "s3_config.json"),
            ]
            
            # Create S3 config
            s3_config = {
                "identities": [
                    {
                        "name": self.access_key,
                        "credentials": [
                            {
                                "accessKey": self.access_key,
                                "secretKey": self.secret_key
                            }
                        ],
                        "actions": ["Admin", "Read", "Write"]
                    }
                ]
            }
            
            with open(os.path.join(storage_dir, "s3_config.json"), 'w') as f:
                json.dump(s3_config, f, indent=2)
            
            self._log_info(f"Starting SeaweedFS S3: {' '.join(s3_cmd)}")
            s3_process = subprocess.Popen(
                s3_cmd,
                stdout=subprocess.PIPE,
                stderr=subprocess.PIPE,
                cwd=storage_dir
            )
            
            # Store process for cleanup
            self.local_seaweed_process = {
                "master": master_process,
                "volume": volume_process,
                "filer": filer_process,
                "s3": s3_process,
            }
            
            self._log_info(f"🚀 Local SeaweedFS started:")
            self._log_info(f"   Master: localhost:{self.local_master_port}")
            self._log_info(f"   Volume: localhost:{self.local_volume_port}")
            self._log_info(f"   Filer: localhost:{self.local_filer_port}")
            self._log_info(f"   S3: localhost:{self.local_s3_port}")
            
            return True
            
        except Exception as e:
            self._log_error(f"Failed to start local SeaweedFS: {e}")
            return False
    
    def _download_seaweedfs_binary(self, binary_path: str) -> None:
        """Download SeaweedFS binary for the current platform."""
        try:
            system = platform.system().lower()
            machine = platform.machine().lower()
            
            # SeaweedFS binary URLs
            base_url = "https://github.com/seaweedfs/seaweedfs/releases/latest/download"
            
            if system == "darwin":
                if "arm" in machine or "aarch64" in machine:
                    filename = "darwin_arm64.tar.gz"
                else:
                    filename = "darwin_amd64.tar.gz"
            elif system == "linux":
                if "arm" in machine or "aarch64" in machine:
                    filename = "linux_arm64.tar.gz"
                else:
                    filename = "linux_amd64.tar.gz"
            else:
                raise Exception(f"Unsupported platform: {system}-{machine}")
            
            url = f"{base_url}/{filename}"
            self._log_info(f"Downloading SeaweedFS from {url}")
            
            # Download and extract
            import tarfile
            import tempfile
            
            with tempfile.NamedTemporaryFile(suffix=".tar.gz") as tmp_file:
                urllib.request.urlretrieve(url, tmp_file.name)
                
                with tarfile.open(tmp_file.name, 'r:gz') as tar:
                    tar.extract('weed', path=os.path.dirname(binary_path))
                    extracted_path = os.path.join(os.path.dirname(binary_path), 'weed')
                    os.rename(extracted_path, binary_path)
            
            os.chmod(binary_path, 0o755)
            self._log_info("✅ SeaweedFS binary downloaded")
            
        except Exception as e:
            self._log_error(f"Failed to download SeaweedFS binary: {e}")
            raise
    
    def _find_available_port(self, start_port: int) -> int:
        """Find an available port starting from start_port."""
        for port in range(start_port, start_port + 100):
            try:
                with socket.socket(socket.AF_INET, socket.SOCK_STREAM) as s:
                    s.bind(('localhost', port))
                    return port
            except OSError:
                continue
        raise Exception(f"No available ports found starting from {start_port}")
    
    def _ensure_bucket_exists(self) -> None:
        """Ensure the logging bucket exists with proper configuration."""
        try:
            if self.bucket_manager:
                self.bucket_manager.ensure_bucket(
                    bucket_name=self.bucket_name,
                    encryption=self.encryption,
                    tags={
                        "purpose": "validator-logging",
                        "project": self.project_name,
                        "validator_uid": str(self.validator_uid),
                    },
                    description=f"Logging bucket for validator {self.validator_uid}",
                )
                self._log_info(f"Ensured bucket exists: {self.bucket_name}")
        except Exception as e:
            self._log_error(f"Error ensuring bucket exists: {e}")
    
    # Public API methods for logging operations
    
    def init_run(
        self, 
        config: Dict[str, Any] = None, 
        version_tag: str = None, 
        scraper_providers: List[str] = None
    ) -> None:
        """Initialize a new logging run."""
        now = dt.datetime.now()
        self.run_start = now
        self.run_id = now.strftime("%Y-%m-%d_%H-%M-%S")
        
        # Store configuration
        self.config_data = {
            "uid": self.validator_uid,
            "hotkey": self.wallet.hotkey.ss58_address,
            "run_name": self.run_id,
            "type": "validator",
            "version": version_tag or "unknown",
            "scrapers": scraper_providers or [],
            "started_at": now.isoformat(),
            "project": self.project_name,
            "seaweedfs_endpoint": self.seaweed_s3_endpoint,
            "encryption_enabled": self.encryption,
            "compression_enabled": self.compression,
            **(config or {})
        }
        
        # Clear buffers
        self.current_log_buffer = []
        self.metrics_buffer = []
        
        self._log_info(f"Started SeaweedFS logging run: validator-{self.validator_uid}-{self.run_id}")
        
        # Upload initial config
        self._upload_config()
    
    def log(self, data: Dict[str, Any], step: Optional[int] = None) -> None:
        """Log metrics data with timestamp and step information."""
        log_entry = {
            "timestamp": dt.datetime.now().isoformat(),
            "step": step,
            "data": data
        }
        self.metrics_buffer.append(log_entry)
        
        # Upload metrics every 10 entries or immediately if it's important data
        if len(self.metrics_buffer) >= 10:
            self._upload_metrics()
    
    def log_stdout(self, message: str, level: str = "INFO") -> None:
        """Log stdout/stderr messages."""
        # Skip our own upload messages to avoid recursion
        if "Uploaded" in message and ("log entries" in message or "metrics" in message):
            return
            
        log_entry = {
            "timestamp": dt.datetime.now().isoformat(),
            "level": level,
            "message": message,
            "run_id": self.run_id
        }
        self.current_log_buffer.append(log_entry)
        
        # Upload logs less frequently to capture complete multi-line content
        now = dt.datetime.now()
        time_since_upload = (now - self.last_upload_time).total_seconds()
        
        # Upload every 20 entries or every 15 seconds (larger batches)
        if len(self.current_log_buffer) >= 20 or time_since_upload >= 15:
            self._upload_logs()
            self.last_upload_time = now
    
    def finish(self) -> None:
        """Finish the current logging run and upload final data."""
        if not self.run_id:
            return
            
        # Upload any remaining data
        if self.current_log_buffer:
            self._upload_logs()
        if self.metrics_buffer:
            self._upload_metrics()
            
        # Upload final summary
        self._upload_summary()
        
        self._log_info(f"Finished SeaweedFS logging run: {self.run_id}")
        
        # Clear state
        self.run_id = None
        self.run_start = None
        self.current_log_buffer = []
        self.metrics_buffer = []
    
    def cleanup(self) -> None:
        """Clean up resources including local SeaweedFS processes."""
        if self.local_seaweed_process:
            try:
                self._log_info("Shutting down local SeaweedFS processes...")
                
                for name, process in self.local_seaweed_process.items():
                    try:
                        process.terminate()
                        process.wait(timeout=5)
                        self._log_info(f"✅ {name} process terminated")
                    except subprocess.TimeoutExpired:
                        self._log_warning(f"{name} process did not terminate gracefully, killing...")
                        process.kill()
                    except Exception as e:
                        self._log_error(f"Error shutting down {name} process: {e}")
                
                self.local_seaweed_process = None
                
            except Exception as e:
                self._log_error(f"Error during SeaweedFS cleanup: {e}")
        
        # Close client connection
        if self.seaweed_client:
            self.seaweed_client.close()
    
    def should_rotate_run(self) -> bool:
        """Check if run should be rotated (daily rotation)."""
        if not self.run_start:
            return False
        return (dt.datetime.now() - self.run_start) >= dt.timedelta(days=1)
    
    # Internal methods for uploading data
    
    def _upload_config(self) -> None:
        """Upload configuration data."""
        if not self.run_id or not self.seaweed_client:
            return
            
        try:
            config_data = {
                "run_info": self.config_data,
                "uploaded_at": dt.datetime.now().isoformat()
            }
            
            config_json = json.dumps(config_data, indent=2)
            object_key = f"validator_{self.validator_uid}/{self.run_id}/config.json"
            
            self.seaweed_client.put_object(
                bucket_name=self.bucket_name,
                object_key=object_key,
                data=config_json,
                content_type='application/json',
                metadata={"run_id": self.run_id, "type": "config"}
            )
            
            self._log_debug(f"Uploaded config to SeaweedFS: {object_key}")
            
        except Exception as e:
            self._log_error(f"Error uploading config to SeaweedFS: {e}")
    
    def _upload_logs(self) -> None:
        """Upload log buffer to SeaweedFS."""
        if not self.current_log_buffer or not self.run_id or not self.seaweed_client:
            return
            
        try:
            timestamp = dt.datetime.now().strftime("%Y%m%d_%H%M%S")
            log_data = {
                "logs": self.current_log_buffer.copy(),
                "uploaded_at": dt.datetime.now().isoformat(),
                "run_id": self.run_id
            }
            
            log_json = json.dumps(log_data, indent=2)
            object_key = f"validator_{self.validator_uid}/{self.run_id}/logs_{timestamp}.json"
            
            self.seaweed_client.put_object(
                bucket_name=self.bucket_name,
                object_key=object_key,
                data=log_json,
                content_type='application/json',
                metadata={"run_id": self.run_id, "type": "logs"}
            )
            
            self._log_debug(f"Uploaded {len(self.current_log_buffer)} log entries to SeaweedFS")
            self.current_log_buffer = []
            
        except Exception as e:
            self._log_error(f"Error uploading logs to SeaweedFS: {e}")
    
    def _upload_metrics(self) -> None:
        """Upload metrics buffer to SeaweedFS."""
        if not self.metrics_buffer or not self.run_id or not self.seaweed_client:
            return
            
        try:
            timestamp = dt.datetime.now().strftime("%Y%m%d_%H%M%S")
            metrics_data = {
                "metrics": self.metrics_buffer.copy(),
                "uploaded_at": dt.datetime.now().isoformat(),
                "run_id": self.run_id
            }
            
            metrics_json = json.dumps(metrics_data, indent=2)
            object_key = f"validator_{self.validator_uid}/{self.run_id}/metrics_{timestamp}.json"
            
            self.seaweed_client.put_object(
                bucket_name=self.bucket_name,
                object_key=object_key,
                data=metrics_json,
                content_type='application/json',
                metadata={"run_id": self.run_id, "type": "metrics"}
            )
            
            self._log_debug(f"Uploaded {len(self.metrics_buffer)} metrics to SeaweedFS")
            self.metrics_buffer = []
            
        except Exception as e:
            self._log_error(f"Error uploading metrics to SeaweedFS: {e}")
    
    def _upload_summary(self) -> None:
        """Upload run summary."""
        if not self.run_id or not self.seaweed_client:
            return
            
        try:
            summary_data = {
                "run_id": self.run_id,
                "validator_uid": self.validator_uid,
                "start_time": self.run_start.isoformat() if self.run_start else None,
                "end_time": dt.datetime.now().isoformat(),
                "duration_seconds": (dt.datetime.now() - self.run_start).total_seconds() if self.run_start else 0,
                "config": self.config_data,
                "final_log_count": len(self.current_log_buffer),
                "final_metrics_count": len(self.metrics_buffer),
                "storage_backend": "seaweedfs",
                "encryption_enabled": self.encryption,
            }
            
            summary_json = json.dumps(summary_data, indent=2)
            object_key = f"validator_{self.validator_uid}/{self.run_id}/summary.json"
            
            self.seaweed_client.put_object(
                bucket_name=self.bucket_name,
                object_key=object_key,
                data=summary_json,
                content_type='application/json',
                metadata={"run_id": self.run_id, "type": "summary"}
            )
            
            self._log_debug(f"Uploaded run summary to SeaweedFS")
            
        except Exception as e:
            self._log_error(f"Error uploading summary to SeaweedFS: {e}")
    
    # Logging helpers
    
    def _log_info(self, message: str) -> None:
        """Log info message."""
        try:
            import bittensor as bt
            bt.logging.info(message)
        except ImportError:
            print(f"INFO: {message}")
    
    def _log_warning(self, message: str) -> None:
        """Log warning message."""
        try:
            import bittensor as bt
            bt.logging.warning(message)
        except ImportError:
            print(f"WARNING: {message}")
    
    def _log_error(self, message: str) -> None:
        """Log error message."""
        try:
            import bittensor as bt
            bt.logging.error(message)
        except ImportError:
            print(f"ERROR: {message}")
    
    def _log_debug(self, message: str) -> None:
        """Log debug message."""
        try:
            import bittensor as bt
            bt.logging.debug(message)
        except ImportError:
            pass  # Debug messages are optional


class ValidatorLogCapture:
    """
    Enhanced log capture context manager for comprehensive logging.
    
    Captures stdout/stderr and bittensor logs, forwarding them to the SeaweedFS logger
    for centralized storage and real-time monitoring.
    """
    
    def __init__(
        self, 
        seaweed_logger: ValidatorLogger, 
        capture_stdout: bool = True, 
        capture_stderr: bool = True
    ):
        """
        Initialize log capture.
        
        Args:
            seaweed_logger: ValidatorLogger instance
            capture_stdout: Whether to capture stdout
            capture_stderr: Whether to capture stderr
        """
        self.seaweed_logger = seaweed_logger
        self.capture_stdout = capture_stdout
        self.capture_stderr = capture_stderr
        self.original_stdout = None
        self.original_stderr = None
        self.original_bt_methods = {}
        
    def __enter__(self):
        """Enter the log capture context."""
        # Capture stdout/stderr
        if self.capture_stdout:
            import sys
            self.original_stdout = sys.stdout
            sys.stdout = self._create_wrapper(self.original_stdout, "INFO")
            
        if self.capture_stderr:
            import sys
            self.original_stderr = sys.stderr
            sys.stderr = self._create_wrapper(self.original_stderr, "ERROR")
        
        # Hook into bittensor logging
        try:
            import bittensor as bt
            
            methods_to_hook = ['info', 'debug', 'trace', 'error', 'warning', 'success']
            
            for method_name in methods_to_hook:
                if hasattr(bt.logging, method_name):
                    original_method = getattr(bt.logging, method_name)
                    self.original_bt_methods[method_name] = original_method
                    
                    # Create wrapper for each method
                    def create_wrapper(orig_method, level_name, logger):
                        def wrapper(message, *args, **kwargs):
                            # Call original method
                            result = orig_method(message, *args, **kwargs)
                            
                            # Also send to SeaweedFS logger
                            try:
                                formatted_message = str(message) % args if args else str(message)
                                if not ("Uploaded" in formatted_message and ("log entries" in formatted_message or "metrics" in formatted_message)):
                                    logger.log_stdout(formatted_message, level_name.upper())
                            except Exception:
                                pass
                            
                            return result
                        return wrapper
                    
                    # Replace the method
                    setattr(bt.logging, method_name, create_wrapper(original_method, method_name, self.seaweed_logger))
                    
        except Exception as e:
            print(f"Could not hook bittensor logging: {e}")
            
        return self
        
    def __exit__(self, exc_type, exc_val, exc_tb):
        """Exit the log capture context."""
        # Restore stdout/stderr
        if self.original_stdout:
            import sys
            sys.stdout = self.original_stdout
        if self.original_stderr:
            import sys
            sys.stderr = self.original_stderr
            
        # Restore bittensor logging methods
        if self.original_bt_methods:
            try:
                import bittensor as bt
                for method_name, original_method in self.original_bt_methods.items():
                    setattr(bt.logging, method_name, original_method)
            except:
                pass
    
    def _create_wrapper(self, original_stream, level):
        """Create a wrapper that logs to both original stream and SeaweedFS."""
        class StreamWrapper:
            def __init__(self, original, logger, level):
                self.original = original
                self.logger = logger
                self.level = level
                self.buffer = ""
                
            def write(self, text):
                # Write to original stream
                self.original.write(text)
                
                # Buffer text to handle multi-line output properly
                self.buffer += text
                
                # If buffer gets too large, process it immediately
                if len(self.buffer) > 10000:
                    self._process_buffer()
                
                # Process complete lines for smaller content
                if '\n' in text:
                    self._process_buffer()
                    
            def _process_buffer(self):
                """Process buffered content."""
                if not self.buffer:
                    return
                    
                lines = self.buffer.split('\n')
                
                # Keep the last incomplete line in buffer if text doesn't end with newline
                if not self.buffer.endswith('\n'):
                    self.buffer = lines[-1]
                    lines = lines[:-1]
                else:
                    self.buffer = ""
                
                # Process complete lines
                for line in lines:
                    if line.strip():
                        line_content = line.strip()
                        # Skip certain log messages to avoid noise
                        if not any(skip in line_content for skip in [
                            'Uploaded', 'log entries', 'metrics',
                            'SeaweedFS health check', 'bucket exists'
                        ]):
                            self.logger.log_stdout(line_content, self.level)
                    
            def flush(self):
                # Process any remaining buffer content
                self._process_buffer()
                self.original.flush()
                
        return StreamWrapper(original_stream, self.seaweed_logger, level)


# Export main classes
__all__ = ["ValidatorLogger", "ValidatorLogCapture"]