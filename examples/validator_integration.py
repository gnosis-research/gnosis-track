#!/usr/bin/env python3
"""
Validator Integration Examples for Gnosis-Track.

This example shows how to integrate Gnosis-Track with existing validator code:
- Replace existing logging systems
- Add comprehensive monitoring
- Implement health checks
- Handle errors gracefully
"""

import time
import json
import random
import threading
from datetime import datetime, timedelta
from typing import Dict, Any, List, Optional

from gnosis_track.logging import ValidatorLogger, ValidatorLogCapture
from gnosis_track.core import BucketManager


class MockBittensorWallet:
    """Mock wallet for example purposes."""
    class MockHotkey:
        ss58_address = "5F3sa2TJAWMqDhXG6jhV4N8ko9SxwGy8TpaNS1repo5EYjQX"
    
    class MockColdkey:
        ss58_address = "5CiPPseXPECbkjWCa6MnjNokrgYjMqmKndv2rSnekmSK2DjL"
    
    hotkey = MockHotkey()
    coldkey = MockColdkey()


class MockMetagraph:
    """Mock metagraph for example purposes."""
    def __init__(self):
        self.neurons = [f"neuron_{i}" for i in range(10)]
        self.block = random.randint(1000000, 2000000)


class EnhancedValidator:
    """
    Example validator class showing comprehensive Gnosis-Track integration.
    
    This demonstrates how to add enterprise-grade logging to an existing validator
    with minimal code changes and maximum reliability.
    """
    
    def __init__(self, uid: int, wallet: MockBittensorWallet, config: Dict[str, Any]):
        self.uid = uid
        self.wallet = wallet
        self.config = config
        self.metagraph = MockMetagraph()
        self.step = 0
        self.should_exit = False
        self.is_running = False
        
        # Performance tracking
        self.start_time = datetime.now()
        self.last_health_check = datetime.now()
        self.performance_metrics = {
            "requests_processed": 0,
            "errors_encountered": 0,
            "average_response_time": 0.0,
            "memory_usage_mb": 0,
            "cpu_usage_percent": 0
        }
        
        # Initialize logging with fallback
        self.logger = None
        self.log_capture = None
        self.bucket_manager = None
        
        self._setup_logging()
    
    def _setup_logging(self):
        """Setup enhanced logging with automatic fallback."""
        
        max_retries = 3
        retry_delay = 2
        
        for attempt in range(max_retries):
            try:
                print(f"🔄 Setting up logging (attempt {attempt + 1}/{max_retries})")
                
                # Initialize logger
                self.logger = ValidatorLogger(
                    validator_uid=self.uid,
                    wallet=self.wallet,
                    seaweed_s3_endpoint=self.config.get('seaweed_endpoint', 'localhost:8333'),
                    access_key=self.config.get('access_key', 'admin'),
                    secret_key=self.config.get('secret_key', 'admin_secret_key'),
                    bucket_name=f"validator-{self.uid}-logs",
                    project_name="enhanced-validator-demo",
                    encryption=True,
                    compression=True,
                    auto_start_local=True
                )
                
                # Initialize bucket manager for advanced operations
                if self.logger.seaweed_client:
                    self.bucket_manager = BucketManager(
                        self.logger.seaweed_client,
                        default_encryption=True
                    )
                
                # Setup log capture
                self.log_capture = ValidatorLogCapture(
                    self.logger,
                    capture_stdout=True,
                    capture_stderr=True
                )
                
                print("✅ Logging setup successful")
                break
                
            except Exception as e:
                print(f"❌ Logging setup attempt {attempt + 1} failed: {e}")
                
                if attempt < max_retries - 1:
                    print(f"⏳ Retrying in {retry_delay} seconds...")
                    time.sleep(retry_delay)
                else:
                    print("🔧 Using fallback logging")
                    self._setup_fallback_logging()
    
    def _setup_fallback_logging(self):
        """Setup basic file-based logging as fallback."""
        import logging
        
        # Create local file logger
        log_file = f"validator_{self.uid}_{datetime.now().strftime('%Y%m%d')}.log"
        
        logging.basicConfig(
            filename=log_file,
            level=logging.INFO,
            format='%(asctime)s | %(levelname)s | %(message)s',
            filemode='a'
        )
        
        self.fallback_logger = logging.getLogger(f"validator_{self.uid}")
        print(f"📝 Fallback logging to: {log_file}")
    
    def start_logging_session(self):
        """Start a new logging session with comprehensive configuration."""
        
        if not self.logger:
            print("⚠️ Logger not available, using fallback")
            return
        
        try:
            # Ensure bucket exists with proper configuration
            if self.bucket_manager:
                self.bucket_manager.ensure_bucket(
                    bucket_name=f"validator-{self.uid}-logs",
                    encryption=True,
                    lifecycle_days=90,  # Archive after 90 days
                    tags={
                        "validator_uid": str(self.uid),
                        "project": "enhanced-validator-demo",
                        "environment": "production",
                        "hotkey": self.wallet.hotkey.ss58_address[:20]
                    },
                    description=f"Logging bucket for enhanced validator {self.uid}"
                )
            
            # Start logging session with rich configuration
            self.logger.init_run(
                config={
                    # Validator info
                    "validator_uid": self.uid,
                    "hotkey": self.wallet.hotkey.ss58_address,
                    "coldkey": self.wallet.coldkey.ss58_address,
                    
                    # Network info
                    "network": self.config.get('network', 'finney'),
                    "netuid": self.config.get('netuid', 1),
                    "block_height": self.metagraph.block,
                    "connected_peers": len(self.metagraph.neurons),
                    
                    # System info
                    "start_time": self.start_time.isoformat(),
                    "python_version": "3.9.0",
                    "system_memory_gb": 16,
                    "available_gpus": 1,
                    
                    # Configuration
                    "features": {
                        "encryption": True,
                        "compression": True,
                        "real_time_monitoring": True,
                        "health_checks": True,
                        "performance_tracking": True
                    },
                    
                    # Custom validator config
                    **self.config
                },
                version_tag="v2.1.0",
                scraper_providers=["reddit", "twitter", "youtube"]
            )
            
            # Start log capture
            if self.log_capture:
                self.log_capture.__enter__()
            
            # Log session start
            self._log_event("validator_session_started", {
                "validator_uid": self.uid,
                "session_id": f"session_{int(time.time())}",
                "configuration": self.config
            })
            
            print(f"🚀 Enhanced logging session started for validator {self.uid}")
            
        except Exception as e:
            print(f"❌ Failed to start logging session: {e}")
            self._fallback_log("ERROR", f"Logging session start failed: {e}")
    
    def run_validation_loop(self):
        """Main validation loop with comprehensive logging."""
        
        self.is_running = True
        print(f"🔄 Starting validation loop for validator {self.uid}")
        
        try:
            while not self.should_exit and self.step < 10:  # Limited for demo
                step_start_time = time.time()
                
                # Simulate validation work
                self._simulate_validation_step()
                
                # Track performance
                step_duration = time.time() - step_start_time
                self._update_performance_metrics(step_duration)
                
                # Log metrics every step
                self._log_step_metrics(step_duration)
                
                # Health check every 5 steps
                if self.step % 5 == 0:
                    self._perform_health_check()
                
                # Simulate processing time
                time.sleep(random.uniform(0.5, 2.0))
                self.step += 1
            
            self._log_event("validation_loop_completed", {
                "total_steps": self.step,
                "duration_seconds": (datetime.now() - self.start_time).total_seconds(),
                "performance": self.performance_metrics
            })
            
        except KeyboardInterrupt:
            self._log_event("validation_interrupted", {"step": self.step})
            print("⏹️ Validation interrupted by user")
            
        except Exception as e:
            self._log_event("validation_error", {
                "error": str(e),
                "error_type": type(e).__name__,
                "step": self.step
            }, level="ERROR")
            print(f"❌ Validation error: {e}")
            
        finally:
            self.is_running = False
            print("🔧 Validation loop stopped")
    
    def _simulate_validation_step(self):
        """Simulate a validation step with various scenarios."""
        
        # Simulate different types of operations
        operations = [
            {"name": "forward_pass", "duration": 0.1, "success_rate": 0.95},
            {"name": "response_validation", "duration": 0.05, "success_rate": 0.98},
            {"name": "score_calculation", "duration": 0.02, "success_rate": 0.99},
            {"name": "weight_update", "duration": 0.03, "success_rate": 0.97}
        ]
        
        step_results = {
            "step": self.step,
            "timestamp": datetime.now().isoformat(),
            "operations": []
        }
        
        for op in operations:
            op_start = time.time()
            
            # Simulate operation
            time.sleep(op['duration'] * random.uniform(0.8, 1.2))
            
            # Simulate success/failure
            success = random.random() < op['success_rate']
            
            operation_result = {
                "name": op['name'],
                "duration_ms": (time.time() - op_start) * 1000,
                "success": success,
                "timestamp": datetime.now().isoformat()
            }
            
            if not success:
                operation_result["error"] = f"Simulated {op['name']} failure"
                self.performance_metrics["errors_encountered"] += 1
                
                self._log_event("operation_failed", operation_result, level="WARNING")
            
            step_results["operations"].append(operation_result)
            self.performance_metrics["requests_processed"] += 1
        
        # Log step completion
        print(f"📊 Step {self.step}: {len([op for op in step_results['operations'] if op['success']])}/{len(operations)} operations successful")
        
        return step_results
    
    def _update_performance_metrics(self, step_duration: float):
        """Update performance tracking metrics."""
        
        # Update response time (rolling average)
        current_avg = self.performance_metrics["average_response_time"]
        total_requests = self.performance_metrics["requests_processed"]
        
        if total_requests > 0:
            self.performance_metrics["average_response_time"] = (
                (current_avg * (total_requests - 1) + step_duration) / total_requests
            )
        
        # Simulate system metrics
        self.performance_metrics.update({
            "memory_usage_mb": random.uniform(800, 1200),
            "cpu_usage_percent": random.uniform(20, 80),
            "gpu_utilization_percent": random.uniform(60, 95),
            "network_latency_ms": random.uniform(10, 50)
        })
    
    def _log_step_metrics(self, step_duration: float):
        """Log comprehensive metrics for the current step."""
        
        if not self.logger:
            return
        
        try:
            # Core metrics
            metrics = {
                "step_metrics": {
                    "step": self.step,
                    "duration_seconds": step_duration,
                    "timestamp": datetime.now().isoformat(),
                    "validator_uid": self.uid
                },
                
                "performance": self.performance_metrics.copy(),
                
                "network_state": {
                    "block_height": self.metagraph.block + self.step,  # Simulate progression
                    "connected_peers": len(self.metagraph.neurons),
                    "sync_status": "synced"
                },
                
                "system_resources": {
                    "memory_usage_mb": self.performance_metrics["memory_usage_mb"],
                    "cpu_usage_percent": self.performance_metrics["cpu_usage_percent"],
                    "gpu_utilization_percent": self.performance_metrics.get("gpu_utilization_percent", 0),
                    "disk_usage_percent": random.uniform(30, 60),
                    "network_io_mbps": random.uniform(1, 10)
                }
            }
            
            # Log to structured storage
            self.logger.log(metrics, step=self.step)
            
            # Log human-readable summary
            self.logger.log_stdout(
                f"Step {self.step}: {step_duration:.3f}s, "
                f"CPU: {self.performance_metrics['cpu_usage_percent']:.1f}%, "
                f"Mem: {self.performance_metrics['memory_usage_mb']:.0f}MB, "
                f"Errors: {self.performance_metrics['errors_encountered']}"
            )
            
        except Exception as e:
            print(f"⚠️ Failed to log metrics: {e}")
            self._fallback_log("WARNING", f"Metrics logging failed: {e}")
    
    def _perform_health_check(self):
        """Perform comprehensive health checks."""
        
        health_data = {
            "timestamp": datetime.now().isoformat(),
            "validator_uid": self.uid,
            "checks": {}
        }
        
        # Check SeaweedFS storage health
        if self.logger and self.logger.seaweed_client:
            try:
                storage_health = self.logger.seaweed_client.health_check()
                health_data["checks"]["storage"] = storage_health
                
                if storage_health["status"] != "healthy":
                    self._log_event("storage_health_warning", storage_health, level="WARNING")
                    
            except Exception as e:
                health_data["checks"]["storage"] = {"status": "error", "error": str(e)}
        
        # Check bucket health
        if self.bucket_manager:
            try:
                bucket_health = self.bucket_manager.get_bucket_health(f"validator-{self.uid}-logs")
                health_data["checks"]["bucket"] = bucket_health
                
                if bucket_health["status"] != "healthy":
                    self._log_event("bucket_health_warning", bucket_health, level="WARNING")
                    
            except Exception as e:
                health_data["checks"]["bucket"] = {"status": "error", "error": str(e)}
        
        # Check system resources
        memory_usage = self.performance_metrics["memory_usage_mb"]
        cpu_usage = self.performance_metrics["cpu_usage_percent"]
        
        health_data["checks"]["system"] = {
            "memory_usage_mb": memory_usage,
            "cpu_usage_percent": cpu_usage,
            "status": "healthy"
        }
        
        # Alert on high resource usage
        if memory_usage > 1000:  # > 1GB
            health_data["checks"]["system"]["status"] = "warning"
            self._log_event("high_memory_usage", {"usage_mb": memory_usage}, level="WARNING")
        
        if cpu_usage > 70:  # > 70% CPU
            health_data["checks"]["system"]["status"] = "warning"
            self._log_event("high_cpu_usage", {"usage_percent": cpu_usage}, level="WARNING")
        
        # Check error rate
        error_rate = (
            self.performance_metrics["errors_encountered"] / 
            max(self.performance_metrics["requests_processed"], 1)
        )
        
        health_data["checks"]["error_rate"] = {
            "rate": error_rate,
            "status": "healthy" if error_rate < 0.1 else "warning"
        }
        
        if error_rate >= 0.1:  # > 10% error rate
            self._log_event("high_error_rate", {"error_rate": error_rate}, level="WARNING")
        
        # Log overall health status
        overall_status = "healthy"
        for check in health_data["checks"].values():
            if check.get("status") == "error":
                overall_status = "error"
                break
            elif check.get("status") == "warning":
                overall_status = "warning"
        
        health_data["overall_status"] = overall_status
        
        # Log health check results
        self._log_event("health_check", health_data)
        
        status_icon = {"healthy": "✅", "warning": "⚠️", "error": "❌"}[overall_status]
        print(f"{status_icon} Health check: {overall_status}")
        
        self.last_health_check = datetime.now()
    
    def _log_event(self, event_type: str, event_data: Dict[str, Any], level: str = "INFO"):
        """Log structured events with consistent format."""
        
        event = {
            "event_type": event_type,
            "event_data": event_data,
            "validator_uid": self.uid,
            "timestamp": datetime.now().isoformat(),
            "step": self.step,
            "session_id": f"session_{int(self.start_time.timestamp())}"
        }
        
        if self.logger:
            try:
                # Log structured data
                self.logger.log({"event": event})
                
                # Log human-readable version
                self.logger.log_stdout(
                    f"EVENT[{event_type}]: {json.dumps(event_data, default=str)}",
                    level=level
                )
            except Exception as e:
                self._fallback_log("ERROR", f"Event logging failed: {e}")
        else:
            self._fallback_log(level, f"EVENT[{event_type}]: {event_data}")
    
    def _fallback_log(self, level: str, message: str):
        """Fallback logging when main logger is unavailable."""
        
        if hasattr(self, 'fallback_logger'):
            getattr(self.fallback_logger, level.lower())(message)
        else:
            print(f"{datetime.now().isoformat()} | {level} | {message}")
    
    def stop(self):
        """Stop the validator and clean up logging."""
        
        print("🛑 Stopping validator...")
        self.should_exit = True
        
        # Log shutdown event
        self._log_event("validator_stopping", {
            "total_runtime_seconds": (datetime.now() - self.start_time).total_seconds(),
            "total_steps": self.step,
            "final_performance": self.performance_metrics
        })
        
        # Clean up logging
        try:
            if self.log_capture:
                self.log_capture.__exit__(None, None, None)
                
            if self.logger:
                self.logger.finish()
                self.logger.cleanup()
                
            print("✅ Validator stopped and logging cleaned up")
            
        except Exception as e:
            print(f"⚠️ Warning during cleanup: {e}")


def run_validator_demo():
    """Run a complete validator demo with enhanced logging."""
    
    print("🎯 Enhanced Validator Demo")
    print("=" * 60)
    
    # Configuration
    config = {
        "netuid": 1,
        "network": "finney",
        "seaweed_endpoint": "localhost:8333",
        "access_key": "admin",
        "secret_key": "admin_secret_key",
        "learning_rate": 0.001,
        "batch_size": 32,
        "model_name": "enhanced_validator_v2"
    }
    
    # Create mock wallet
    wallet = MockBittensorWallet()
    
    # Initialize validator
    validator = EnhancedValidator(
        uid=42,
        wallet=wallet,
        config=config
    )
    
    try:
        # Start logging session
        validator.start_logging_session()
        
        # Run validation loop
        validator.run_validation_loop()
        
        # Show final statistics
        print(f"\n📊 Final Statistics:")
        print(f"   Steps completed: {validator.step}")
        print(f"   Requests processed: {validator.performance_metrics['requests_processed']}")
        print(f"   Errors encountered: {validator.performance_metrics['errors_encountered']}")
        print(f"   Average response time: {validator.performance_metrics['average_response_time']:.3f}s")
        print(f"   Total runtime: {(datetime.now() - validator.start_time).total_seconds():.1f}s")
        
    except KeyboardInterrupt:
        print("\n⏹️ Demo interrupted by user")
        
    finally:
        validator.stop()


if __name__ == "__main__":
    """Run the validator integration demo."""
    
    print("🚀 Gnosis-Track Validator Integration Examples")
    print("=" * 70)
    print()
    
    run_validator_demo()
    
    print("\n🎉 Validator demo completed!")
    print("\nWhat happened:")
    print("- ✅ Enhanced validator with comprehensive logging")
    print("- ✅ Automatic health monitoring and alerts")
    print("- ✅ Structured event logging with rich metadata")
    print("- ✅ Performance tracking and resource monitoring")
    print("- ✅ Error handling with graceful fallbacks")
    print("- ✅ Secure encrypted storage with SeaweedFS")
    print("\nNext steps:")
    print("- View logs: gnosis-track logs stream --validator-uid 42")
    print("- Check health: gnosis-track health")
    print("- Start UI: gnosis-track ui --port 8080")