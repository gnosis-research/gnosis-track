#!/usr/bin/env python3
"""
Basic usage examples for Gnosis-Track logging.

This example shows the fundamental logging operations:
- Initialize logger
- Start logging session  
- Log metrics and events
- Capture stdout/stderr
- Finish session
"""

import time
import random
from datetime import datetime
from gnosis_track.logging import ValidatorLogger, ValidatorLogCapture


def example_basic_logging():
    """Basic logging example with metrics and events."""
    
    print("🚀 Basic Logging Example")
    print("=" * 50)
    
    # Create a mock wallet object (replace with actual wallet in real usage)
    class MockWallet:
        class MockHotkey:
            ss58_address = "5F3sa2TJAWMqDhXG6jhV4N8ko9SxwGy8TpaNS1repo5EYjQX"
        hotkey = MockHotkey()
    
    wallet = MockWallet()
    
    # Initialize logger
    logger = ValidatorLogger(
        validator_uid=0,
        wallet=wallet,
        seaweed_s3_endpoint="localhost:8333",
        access_key="admin",
        secret_key="admin_secret_key", 
        bucket_name="example-logs",
        encryption=True,
        compression=True,
        auto_start_local=True  # Will start SeaweedFS if not running
    )
    
    try:
        # Start logging session
        logger.init_run(
            config={
                "experiment": "basic_example",
                "model": "transformer_v1",
                "dataset": "custom_data",
                "parameters": {
                    "learning_rate": 0.001,
                    "batch_size": 32,
                    "epochs": 100
                }
            },
            version_tag="v1.0.0"
        )
        
        print("✅ Logging session started")
        
        # Simulate training loop with metrics
        for epoch in range(5):
            # Simulate some work
            time.sleep(1)
            
            # Generate mock metrics
            loss = random.uniform(0.5, 1.0) * (0.9 ** epoch)  # Decreasing loss
            accuracy = random.uniform(0.7, 0.95) + (epoch * 0.02)  # Increasing accuracy
            learning_rate = 0.001 * (0.95 ** epoch)  # Decreasing LR
            
            # Log metrics
            logger.log({
                "epoch": epoch,
                "loss": loss,
                "accuracy": accuracy,
                "learning_rate": learning_rate,
                "timestamp": datetime.now().isoformat(),
                "batch_processed": (epoch + 1) * 100
            }, step=epoch)
            
            # Log text events
            logger.log_stdout(f"Epoch {epoch + 1}/5 completed - Loss: {loss:.4f}, Accuracy: {accuracy:.4f}")
            
            print(f"📊 Epoch {epoch + 1}: Loss={loss:.4f}, Acc={accuracy:.4f}")
        
        # Log final results
        logger.log({
            "final_results": {
                "best_accuracy": max([0.7 + i * 0.02 for i in range(5)]),
                "final_loss": loss,
                "total_epochs": 5,
                "training_time_seconds": 5,
                "model_size_mb": 125.7
            }
        })
        
        logger.log_stdout("Training completed successfully!", level="SUCCESS")
        print("✅ Training completed")
        
    finally:
        # Always finish the session
        logger.finish()
        logger.cleanup()
        print("🔧 Logger cleaned up")


def example_log_capture():
    """Example using log capture to automatically capture all output."""
    
    print("\n🎯 Log Capture Example")
    print("=" * 50)
    
    class MockWallet:
        class MockHotkey:
            ss58_address = "5F3sa2TJAWMqDhXG6jhV4N8ko9SxwGy8TpaNS1repo5EYjQX"
        hotkey = MockHotkey()
    
    wallet = MockWallet()
    
    # Initialize logger
    logger = ValidatorLogger(
        validator_uid=1,
        wallet=wallet,
        bucket_name="capture-example-logs",
        auto_start_local=True
    )
    
    try:
        # Start logging session
        logger.init_run(
            config={"experiment": "log_capture_demo"},
            version_tag="v1.0.0"
        )
        
        # Use log capture context manager
        with ValidatorLogCapture(logger, capture_stdout=True, capture_stderr=True):
            print("🎪 This output will be automatically captured and stored!")
            print("📝 All print statements are logged to SeaweedFS")
            
            # Simulate some processing
            for i in range(3):
                print(f"Processing item {i + 1}...")
                time.sleep(0.5)
                
                # This will also be captured
                if i == 1:
                    print("⚠️ Warning: This is a test warning", file=__import__('sys').stderr)
            
            print("✅ Processing completed!")
            
            # Manual logging still works inside capture
            logger.log({
                "items_processed": 3,
                "status": "completed",
                "capture_demo": True
            })
        
        print("📤 Log capture finished - all output was stored")
        
    finally:
        logger.finish()
        logger.cleanup()


def example_structured_logging():
    """Example of structured logging with rich metadata."""
    
    print("\n📋 Structured Logging Example") 
    print("=" * 50)
    
    class MockWallet:
        class MockHotkey:
            ss58_address = "5F3sa2TJAWMqDhXG6jhV4N8ko9SxwGy8TpaNS1repo5EYjQX"
        hotkey = MockHotkey()
    
    wallet = MockWallet()
    
    logger = ValidatorLogger(
        validator_uid=2,
        wallet=wallet,
        bucket_name="structured-logs",
        auto_start_local=True
    )
    
    try:
        logger.init_run(
            config={
                "experiment_type": "structured_logging_demo",
                "environment": "development",
                "features": ["encryption", "compression", "real_time_monitoring"]
            }
        )
        
        # Log different types of structured events
        events = [
            {
                "event_type": "system_startup",
                "data": {
                    "memory_available_gb": 16.5,
                    "cpu_cores": 8,
                    "gpu_available": True,
                    "disk_space_gb": 500.2
                }
            },
            {
                "event_type": "model_loaded", 
                "data": {
                    "model_name": "transformer_large",
                    "parameters": 175_000_000,
                    "load_time_seconds": 12.3,
                    "memory_usage_gb": 4.7
                }
            },
            {
                "event_type": "data_processed",
                "data": {
                    "batch_size": 64,
                    "sequence_length": 512,
                    "processing_time_ms": 234,
                    "throughput_samples_per_sec": 273.5
                }
            },
            {
                "event_type": "performance_metrics",
                "data": {
                    "gpu_utilization_percent": 87.5,
                    "memory_utilization_percent": 62.3,
                    "temperature_celsius": 67,
                    "power_draw_watts": 250
                }
            }
        ]
        
        # Log each event with metadata
        for i, event in enumerate(events):
            logger.log({
                **event,
                "sequence_number": i,
                "timestamp": datetime.now().isoformat(),
                "validator_uid": 2,
                "session_id": "demo_session_001"
            }, step=i)
            
            # Also log as text for human reading
            logger.log_stdout(
                f"EVENT[{event['event_type']}]: {event['data']}"
            )
            
            print(f"📊 Logged event: {event['event_type']}")
            time.sleep(0.2)
        
        # Log summary statistics
        logger.log({
            "summary": {
                "total_events": len(events),
                "event_types": list(set(e['event_type'] for e in events)),
                "demo_completed": True,
                "total_duration_seconds": len(events) * 0.2
            }
        })
        
        print("✅ Structured logging demo completed")
        
    finally:
        logger.finish()
        logger.cleanup()


def example_error_handling():
    """Example showing error handling and recovery."""
    
    print("\n🚨 Error Handling Example")
    print("=" * 50)
    
    class MockWallet:
        class MockHotkey:
            ss58_address = "5F3sa2TJAWMqDhXG6jhV4N8ko9SxwGy8TpaNS1repo5EYjQX"
        hotkey = MockHotkey()
    
    wallet = MockWallet()
    
    # Initialize with fallback handling
    logger = None
    
    try:
        logger = ValidatorLogger(
            validator_uid=3,
            wallet=wallet,
            bucket_name="error-demo-logs",
            auto_start_local=True
        )
        
        logger.init_run(config={"demo": "error_handling"})
        print("✅ Logger initialized successfully")
        
        # Simulate operations that might fail
        operations = [
            {"name": "normal_operation", "should_fail": False},
            {"name": "risky_operation", "should_fail": True},
            {"name": "recovery_operation", "should_fail": False}
        ]
        
        for op in operations:
            try:
                print(f"🔄 Executing {op['name']}...")
                
                # Log operation start
                logger.log({
                    "operation": op['name'],
                    "status": "started",
                    "timestamp": datetime.now().isoformat()
                })
                
                # Simulate work
                time.sleep(0.5)
                
                # Simulate failure
                if op['should_fail']:
                    raise Exception(f"Simulated failure in {op['name']}")
                
                # Log success
                logger.log({
                    "operation": op['name'],
                    "status": "completed",
                    "duration_seconds": 0.5
                })
                
                logger.log_stdout(f"✅ {op['name']} completed successfully")
                print(f"✅ {op['name']} succeeded")
                
            except Exception as e:
                # Log error with full context
                logger.log({
                    "operation": op['name'],
                    "status": "failed",
                    "error": str(e),
                    "error_type": type(e).__name__,
                    "recovery_attempted": True
                })
                
                logger.log_stdout(f"❌ {op['name']} failed: {e}", level="ERROR")
                print(f"❌ {op['name']} failed: {e}")
                
                # Continue with next operation (graceful degradation)
                continue
        
        # Log final status
        logger.log({
            "demo_completed": True,
            "total_operations": len(operations),
            "failed_operations": sum(1 for op in operations if op['should_fail'])
        })
        
    except Exception as e:
        print(f"❌ Critical error: {e}")
        # In real usage, you might want to fallback to file logging here
        
    finally:
        if logger:
            try:
                logger.finish()
                logger.cleanup()
                print("🔧 Logger cleaned up")
            except:
                print("⚠️ Warning: Logger cleanup failed")


if __name__ == "__main__":
    """Run all basic examples."""
    
    print("🎯 Gnosis-Track Basic Usage Examples")
    print("=" * 60)
    print()
    
    # Run examples
    example_basic_logging()
    example_log_capture()
    example_structured_logging()
    example_error_handling()
    
    print("\n🎉 All examples completed!")
    print("\nNext steps:")
    print("- Check the web UI at http://localhost:8080 (if running)")
    print("- View logs with: gnosis-track logs stream --validator-uid 0")
    print("- Export logs with: gnosis-track logs export --validator-uid 0 --format json")
    print("- Check system health: gnosis-track health")