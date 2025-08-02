#!/usr/bin/env python3
"""
Comprehensive test data generator for Gnosis-Track UI.
Creates realistic validator logs with various scenarios, levels, and patterns.
"""

from gnosis_track.logging import ValidatorLogger, ValidatorLogCapture
from datetime import datetime, timedelta
import time
import random
import json

class MockWallet:
    class MockHotkey:
        ss58_address = '5F3sa2TJAWMqDhXG6jhV4N8ko9SxwGy8TpaNS1repo5EYjQX'
    hotkey = MockHotkey()

def create_comprehensive_test_data():
    """Create comprehensive test data with multiple validators and realistic scenarios."""
    
    wallet = MockWallet()
    
    # Test scenarios for different validators
    scenarios = [
        {
            'uid': 10,
            'name': 'High Performance Validator',
            'description': 'Fast processing with occasional warnings',
            'log_patterns': ['high_performance', 'fast_processing', 'minimal_errors']
        },
        {
            'uid': 20, 
            'name': 'Error-Prone Validator',
            'description': 'Demonstrates error handling and recovery',
            'log_patterns': ['frequent_errors', 'recovery_attempts', 'retries']
        },
        {
            'uid': 30,
            'name': 'Data Processing Validator', 
            'description': 'Heavy data processing with metrics',
            'log_patterns': ['data_processing', 'batch_operations', 'metrics_heavy']
        },
        {
            'uid': 40,
            'name': 'Network Operations Validator',
            'description': 'Network communications and peer interactions',
            'log_patterns': ['network_ops', 'peer_communication', 'consensus']
        },
        {
            'uid': 50,
            'name': 'Long Running Validator',
            'description': 'Extended operation simulation',
            'log_patterns': ['long_running', 'gradual_changes', 'periodic_maintenance']
        }
    ]
    
    print("🚀 Creating comprehensive test data for Gnosis-Track UI")
    print("=" * 60)
    
    for scenario in scenarios:
        print(f"\n📊 Creating {scenario['name']} (UID: {scenario['uid']})")
        print(f"    {scenario['description']}")
        
        create_validator_scenario(wallet, scenario)
    
    print(f"\n🎉 All test data created successfully!")
    print(f"📍 Check the UI at http://localhost:8081")
    print(f"🔍 Validators available: {[s['uid'] for s in scenarios]}")

def create_validator_scenario(wallet, scenario):
    """Create detailed logs for a specific validator scenario."""
    
    uid = scenario['uid']
    patterns = scenario['log_patterns']
    
    logger = ValidatorLogger(
        validator_uid=uid,
        wallet=wallet,
        bucket_name='validator-logs',
        auto_start_local=True
    )
    
    try:
        # Initialize with detailed config
        config = {
            'validator_name': scenario['name'],
            'description': scenario['description'],
            'patterns': patterns,
            'test_start_time': datetime.now().isoformat(),
            'expected_duration_minutes': 5,
            'log_levels': ['DEBUG', 'INFO', 'WARNING', 'ERROR', 'SUCCESS'],
            'features_tested': [
                'real_time_streaming',
                'log_filtering',
                'error_handling', 
                'metrics_collection',
                'ui_responsiveness'
            ]
        }
        
        logger.init_run(config=config, version_tag=f"comprehensive_test_v1.0")
        
        # Create different log patterns based on validator type
        if 'high_performance' in patterns:
            create_high_performance_logs(logger, uid)
        elif 'frequent_errors' in patterns:
            create_error_scenario_logs(logger, uid)
        elif 'data_processing' in patterns:
            create_data_processing_logs(logger, uid)
        elif 'network_ops' in patterns:
            create_network_operations_logs(logger, uid)
        elif 'long_running' in patterns:
            create_long_running_logs(logger, uid)
        
        # Add final summary
        logger.log({
            'event_type': 'test_completed',
            'validator_uid': uid,
            'scenario': scenario['name'],
            'total_duration_seconds': 60,  # Approximate
            'logs_generated': 'varies_by_scenario',
            'test_successful': True
        })
        
        logger.log_stdout(f"✅ {scenario['name']} test scenario completed successfully", level="SUCCESS")
        
    finally:
        logger.finish()
        logger.cleanup()
        print(f"    ✅ {scenario['name']} completed")

def create_high_performance_logs(logger, uid):
    """Create logs for high-performance validator scenario."""
    
    logger.log_stdout(f"🚀 Starting high-performance validator {uid}", level="INFO")
    
    # Simulate fast processing cycles
    for cycle in range(20):
        start_time = time.time()
        
        # Fast processing simulation
        logger.log({
            'cycle': cycle,
            'processing_speed': random.uniform(950, 1200),  # ops/second
            'memory_usage_mb': random.uniform(150, 300),
            'cpu_usage_percent': random.uniform(60, 85),
            'network_latency_ms': random.uniform(5, 15),
            'event_type': 'performance_metrics'
        }, step=cycle)
        
        # Occasional warnings (high performance can have edge cases)
        if random.random() < 0.15:  # 15% chance
            logger.log_stdout(f"⚠️  High load detected in cycle {cycle}, optimizing...", level="WARNING")
            logger.log({
                'cycle': cycle,
                'warning_type': 'high_load',
                'auto_optimization': True,
                'performance_impact': 'minimal'
            })
        
        # Success messages
        processing_time = (time.time() - start_time) * 1000
        logger.log_stdout(f"✅ Cycle {cycle} completed in {processing_time:.2f}ms", level="INFO")
        
        time.sleep(0.1)  # Brief pause

def create_error_scenario_logs(logger, uid):
    """Create logs demonstrating error handling and recovery."""
    
    logger.log_stdout(f"🔧 Starting error-prone validator {uid} (testing error handling)", level="INFO")
    
    error_types = [
        {'type': 'network_timeout', 'severity': 'medium', 'recoverable': True},
        {'type': 'memory_pressure', 'severity': 'high', 'recoverable': True},
        {'type': 'invalid_data', 'severity': 'low', 'recoverable': True},
        {'type': 'peer_disconnect', 'severity': 'medium', 'recoverable': True},
        {'type': 'consensus_failure', 'severity': 'high', 'recoverable': False}
    ]
    
    for attempt in range(15):
        # Normal operation
        logger.log({
            'attempt': attempt,
            'status': 'processing',
            'items_processed': random.randint(50, 200),
            'event_type': 'normal_operation'
        }, step=attempt)
        
        # Introduce errors periodically
        if random.random() < 0.4:  # 40% chance of error
            error = random.choice(error_types)
            
            logger.log_stdout(f"❌ Error occurred: {error['type']}", level="ERROR")
            logger.log({
                'attempt': attempt,
                'error_type': error['type'],
                'severity': error['severity'],
                'recoverable': error['recoverable'],
                'timestamp': datetime.now().isoformat(),
                'event_type': 'error_occurred'
            })
            
            # Recovery attempt
            if error['recoverable']:
                time.sleep(0.2)  # Recovery delay
                logger.log_stdout(f"🔄 Attempting recovery from {error['type']}", level="WARNING")
                
                if random.random() < 0.8:  # 80% recovery success rate
                    logger.log_stdout(f"✅ Successfully recovered from {error['type']}", level="SUCCESS")
                    logger.log({
                        'attempt': attempt,
                        'recovery_successful': True,
                        'recovery_time_ms': random.randint(100, 500),
                        'event_type': 'recovery_success'
                    })
                else:
                    logger.log_stdout(f"⚠️  Recovery failed, retrying {error['type']}", level="WARNING")
            
        time.sleep(0.15)

def create_data_processing_logs(logger, uid):
    """Create logs for data-heavy processing scenario."""
    
    logger.log_stdout(f"📊 Starting data processing validator {uid}", level="INFO")
    
    batch_sizes = [100, 250, 500, 1000, 1500]
    
    for batch_num in range(12):
        batch_size = random.choice(batch_sizes)
        
        logger.log_stdout(f"📥 Processing batch {batch_num} ({batch_size} items)", level="INFO")
        
        # Processing metrics
        start_time = time.time()
        
        # Simulate processing time based on batch size
        processing_time = batch_size * random.uniform(0.001, 0.003)
        time.sleep(min(processing_time, 0.3))  # Cap sleep time
        
        actual_time = time.time() - start_time
        
        logger.log({
            'batch_number': batch_num,
            'batch_size': batch_size,
            'processing_time_seconds': actual_time,
            'throughput_items_per_second': batch_size / actual_time,
            'memory_usage_mb': random.uniform(200, 800),
            'data_validation_errors': random.randint(0, 5),
            'successful_items': batch_size - random.randint(0, 3),
            'event_type': 'batch_processing'
        }, step=batch_num)
        
        # Log processing stages
        stages = ['validation', 'transformation', 'analysis', 'storage']
        for stage in stages:
            logger.log_stdout(f"    🔄 {stage.capitalize()} stage completed", level="DEBUG")
        
        logger.log_stdout(f"✅ Batch {batch_num} completed: {batch_size} items in {actual_time:.3f}s", level="SUCCESS")

def create_network_operations_logs(logger, uid):
    """Create logs for network operations and peer communication."""
    
    logger.log_stdout(f"🌐 Starting network operations validator {uid}", level="INFO")
    
    peers = [f"peer_{i}" for i in range(5, 12)]
    
    for round_num in range(18):
        logger.log_stdout(f"🔄 Consensus round {round_num} starting", level="INFO")
        
        # Peer communication
        active_peers = random.sample(peers, random.randint(3, 6))
        
        for peer in active_peers:
            response_time = random.uniform(10, 100)
            success = random.random() < 0.9  # 90% success rate
            
            if success:
                logger.log_stdout(f"    ✅ {peer}: {response_time:.1f}ms", level="DEBUG")
            else:
                logger.log_stdout(f"    ❌ {peer}: timeout", level="WARNING")
        
        # Consensus results
        consensus_reached = len([p for p in active_peers if random.random() < 0.85]) >= 3
        
        logger.log({
            'round': round_num,
            'active_peers': len(active_peers),
            'successful_responses': len([p for p in active_peers if random.random() < 0.9]),
            'average_response_time_ms': random.uniform(25, 75),
            'consensus_reached': consensus_reached,
            'block_height': 1000000 + round_num,
            'event_type': 'consensus_round'
        }, step=round_num)
        
        if consensus_reached:
            logger.log_stdout(f"✅ Consensus reached for round {round_num}", level="SUCCESS")
        else:
            logger.log_stdout(f"⚠️  Consensus failed for round {round_num}, retrying", level="WARNING")
        
        time.sleep(0.1)

def create_long_running_logs(logger, uid):
    """Create logs for extended operation simulation."""
    
    logger.log_stdout(f"⏰ Starting long-running validator {uid} (extended test)", level="INFO")
    
    start_time = time.time()
    uptime_hours = 0
    
    for iteration in range(25):
        current_time = time.time()
        uptime_seconds = current_time - start_time
        uptime_hours = uptime_seconds / 3600
        
        # System health metrics
        logger.log({
            'iteration': iteration,
            'uptime_hours': uptime_hours,
            'uptime_seconds': uptime_seconds,
            'memory_usage_mb': 200 + (iteration * 5) + random.uniform(-20, 20),  # Gradual increase
            'cpu_usage_percent': 45 + random.uniform(-15, 25),
            'disk_usage_gb': 50 + (iteration * 0.5),
            'network_connections': random.randint(8, 15),
            'processed_transactions': iteration * random.randint(100, 300),
            'event_type': 'system_health'
        }, step=iteration)
        
        # Periodic maintenance
        if iteration % 5 == 0 and iteration > 0:
            logger.log_stdout(f"🔧 Performing periodic maintenance (iteration {iteration})", level="INFO")
            logger.log({
                'iteration': iteration,
                'maintenance_type': 'periodic_cleanup',
                'memory_freed_mb': random.randint(10, 50),
                'cache_cleared': True,
                'event_type': 'maintenance'
            })
        
        # Status updates
        if iteration % 3 == 0:
            status_messages = [
                f"Processing continues smoothly (iteration {iteration})",
                f"System stable, {iteration * 50} transactions processed",
                f"Validator health: excellent (iteration {iteration})",
                f"Network sync: {random.uniform(99.5, 99.9):.1f}% (iteration {iteration})"
            ]
            logger.log_stdout(random.choice(status_messages), level="INFO")
        
        time.sleep(0.08)
    
    logger.log_stdout(f"⏰ Long-running test completed after {uptime_hours:.2f} hours", level="SUCCESS")

if __name__ == "__main__":
    """Run comprehensive test data generation."""
    
    print("🎯 Gnosis-Track Comprehensive Test Data Generator")
    print("=" * 60)
    print("This will create realistic validator logs for UI testing:")
    print("  • 5 different validator scenarios")
    print("  • Various log levels and patterns") 
    print("  • Error handling demonstrations")
    print("  • Performance metrics")
    print("  • Network operations")
    print("  • Long-running operations")
    print()
    
    try:
        create_comprehensive_test_data()
        
        print(f"\n🎉 Test data generation completed!")
        print(f"\nNext steps:")
        print(f"1. Open http://localhost:8081 in your browser")
        print(f"2. Select validators 10, 20, 30, 40, or 50")
        print(f"3. Test different features:")
        print(f"   - Real-time log streaming")
        print(f"   - Log level filtering")
        print(f"   - Search functionality")
        print(f"   - Export capabilities")
        print(f"4. Monitor UI performance with various log volumes")
        
    except KeyboardInterrupt:
        print(f"\n⏹️  Test data generation interrupted by user")
    except Exception as e:
        print(f"\n❌ Error during test data generation: {e}")
        import traceback
        traceback.print_exc()