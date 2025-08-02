#!/usr/bin/env python3
"""
Single comprehensive validator test for Gnosis-Track UI.
Creates extensive, realistic logs for thorough UI testing.
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

def create_comprehensive_single_validator():
    """Create comprehensive test data for a single validator with all scenarios."""
    
    wallet = MockWallet()
    uid = 100  # Single test validator
    
    print("🚀 Creating comprehensive single validator test data")
    print("=" * 50)
    print(f"📍 Validator UID: {uid}")
    print(f"⏱️  Expected duration: ~2-3 minutes")
    print(f"📊 Will include all test scenarios in one validator")
    print()
    
    logger = ValidatorLogger(
        validator_uid=uid,
        wallet=wallet,
        bucket_name='validator-logs',
        auto_start_local=True
    )
    
    try:
        # Initialize with comprehensive config
        config = {
            'validator_name': 'Comprehensive Test Validator',
            'description': 'Single validator testing all UI features and scenarios',
            'test_scenarios': [
                'startup_sequence',
                'normal_operations', 
                'performance_metrics',
                'error_handling',
                'data_processing',
                'network_operations',
                'maintenance_cycles',
                'shutdown_sequence'
            ],
            'test_start_time': datetime.now().isoformat(),
            'expected_logs': '200+',
            'log_levels_tested': ['DEBUG', 'INFO', 'WARNING', 'ERROR', 'SUCCESS'],
            'features_tested': [
                'real_time_streaming',
                'log_filtering',
                'search_functionality',
                'error_highlighting', 
                'metrics_display',
                'export_capabilities',
                'ui_performance'
            ]
        }
        
        logger.init_run(config=config, version_tag="comprehensive_single_v1.0")
        
        print("1️⃣  Running startup sequence...")
        run_startup_sequence(logger, uid)
        
        print("2️⃣  Running normal operations...")
        run_normal_operations(logger, uid)
        
        print("3️⃣  Running performance testing...")
        run_performance_testing(logger, uid)
        
        print("4️⃣  Running error scenarios...")
        run_error_scenarios(logger, uid)
        
        print("5️⃣  Running data processing...")
        run_data_processing(logger, uid)
        
        print("6️⃣  Running network operations...")
        run_network_operations(logger, uid)
        
        print("7️⃣  Running maintenance cycles...")
        run_maintenance_cycles(logger, uid)
        
        print("8️⃣  Running shutdown sequence...")
        run_shutdown_sequence(logger, uid)
        
        # Final summary
        logger.log({
            'event_type': 'comprehensive_test_completed',
            'validator_uid': uid,
            'test_duration_minutes': 'varies',
            'scenarios_completed': 8,
            'total_logs_generated': '200+',
            'test_successful': True,
            'timestamp': datetime.now().isoformat()
        })
        
        logger.log_stdout("🎉 Comprehensive test completed successfully!", level="SUCCESS")
        
    finally:
        logger.finish()
        logger.cleanup()
        print("\n✅ Single validator comprehensive test completed!")
        print(f"🌐 Check the UI at http://localhost:8081")
        print(f"🔍 Select Validator {uid} to see all the logs")

def run_startup_sequence(logger, uid):
    """Simulate validator startup sequence."""
    
    logger.log_stdout(f"🚀 Validator {uid} starting up...", level="INFO")
    
    startup_steps = [
        "Loading configuration",
        "Initializing cryptographic modules", 
        "Connecting to network peers",
        "Synchronizing blockchain state",
        "Loading validator keys",
        "Starting consensus engine",
        "Initializing API endpoints",
        "Validator ready for operations"
    ]
    
    for i, step in enumerate(startup_steps):
        logger.log_stdout(f"    {step}...", level="DEBUG")
        
        # Simulate some steps taking longer
        delay = random.uniform(0.1, 0.3) if i < 6 else random.uniform(0.05, 0.15)
        time.sleep(delay)
        
        logger.log({
            'startup_step': i + 1,
            'step_name': step,
            'duration_ms': delay * 1000,
            'status': 'completed',
            'event_type': 'startup_step'
        }, step=i)
        
        if i == len(startup_steps) - 1:
            logger.log_stdout("✅ Validator startup completed successfully!", level="SUCCESS")

def run_normal_operations(logger, uid):
    """Simulate normal validator operations."""
    
    logger.log_stdout(f"⚙️  Running normal operations for validator {uid}", level="INFO")
    
    for cycle in range(15):
        # Normal processing cycle
        logger.log({
            'cycle': cycle,
            'blocks_processed': random.randint(5, 15),
            'transactions_validated': random.randint(50, 200),
            'gas_used': random.randint(100000, 500000),
            'processing_time_ms': random.uniform(50, 150),
            'memory_usage_mb': random.uniform(180, 250),
            'event_type': 'normal_cycle'
        }, step=cycle)
        
        # Status messages
        if cycle % 3 == 0:
            logger.log_stdout(f"📊 Cycle {cycle}: {random.randint(100, 200)} transactions processed", level="INFO")
        
        # Occasional debug info
        if random.random() < 0.3:
            logger.log_stdout(f"    Debug: Memory usage at {random.randint(180, 250)}MB", level="DEBUG")
        
        time.sleep(0.1)

def run_performance_testing(logger, uid):
    """Test performance scenarios."""
    
    logger.log_stdout(f"🏃‍♂️ Running performance tests for validator {uid}", level="INFO")
    
    test_types = ['throughput', 'latency', 'memory_efficiency', 'cpu_optimization']
    
    for i, test_type in enumerate(test_types):
        logger.log_stdout(f"    Testing {test_type}...", level="DEBUG")
        
        # Generate performance metrics
        if test_type == 'throughput':
            tps = random.uniform(800, 1200)
            logger.log({
                'test_type': test_type,
                'transactions_per_second': tps,
                'duration_seconds': 10,
                'peak_tps': tps * 1.15,
                'average_tps': tps * 0.95,
                'event_type': 'performance_test'
            }, step=i)
            logger.log_stdout(f"    ✅ Throughput: {tps:.1f} TPS", level="SUCCESS")
            
        elif test_type == 'latency':
            latency = random.uniform(15, 35)
            logger.log({
                'test_type': test_type,
                'average_latency_ms': latency,
                'p95_latency_ms': latency * 1.8,
                'p99_latency_ms': latency * 2.5,
                'event_type': 'performance_test'
            }, step=i)
            logger.log_stdout(f"    ✅ Latency: {latency:.1f}ms average", level="SUCCESS")
            
        elif test_type == 'memory_efficiency':
            memory_mb = random.uniform(200, 300)
            logger.log({
                'test_type': test_type,
                'memory_usage_mb': memory_mb,
                'memory_efficiency_score': random.uniform(85, 95),
                'gc_frequency': random.randint(5, 15),
                'event_type': 'performance_test'
            }, step=i)
            logger.log_stdout(f"    ✅ Memory usage: {memory_mb:.1f}MB", level="SUCCESS")
            
        time.sleep(0.2)

def run_error_scenarios(logger, uid):
    """Test various error scenarios and recovery."""
    
    logger.log_stdout(f"🚨 Testing error handling for validator {uid}", level="WARNING")
    
    error_scenarios = [
        {'type': 'network_timeout', 'severity': 'medium', 'recoverable': True},
        {'type': 'invalid_transaction', 'severity': 'low', 'recoverable': True}, 
        {'type': 'peer_disconnection', 'severity': 'medium', 'recoverable': True},
        {'type': 'memory_pressure', 'severity': 'high', 'recoverable': True},
        {'type': 'disk_space_low', 'severity': 'high', 'recoverable': False}
    ]
    
    for i, scenario in enumerate(error_scenarios):
        logger.log_stdout(f"    Simulating {scenario['type']}...", level="DEBUG")
        
        # Trigger error
        logger.log_stdout(f"❌ Error: {scenario['type']} occurred", level="ERROR")
        logger.log({
            'error_type': scenario['type'],
            'severity': scenario['severity'],
            'recoverable': scenario['recoverable'],
            'error_code': f"E{1000 + i}",
            'timestamp': datetime.now().isoformat(),
            'event_type': 'error_occurred'
        }, step=i)
        
        # Recovery attempt
        if scenario['recoverable']:
            time.sleep(0.3)  # Recovery time
            logger.log_stdout(f"🔄 Attempting recovery from {scenario['type']}", level="WARNING")
            
            recovery_success = random.random() < 0.8  # 80% success rate
            if recovery_success:
                logger.log_stdout(f"✅ Successfully recovered from {scenario['type']}", level="SUCCESS")
                logger.log({
                    'recovery_type': scenario['type'],
                    'recovery_time_ms': random.randint(200, 800),
                    'recovery_successful': True,
                    'event_type': 'recovery_success'
                })
            else:
                logger.log_stdout(f"⚠️  Recovery partially successful for {scenario['type']}", level="WARNING")
        else:
            logger.log_stdout(f"🔧 Manual intervention required for {scenario['type']}", level="ERROR")

def run_data_processing(logger, uid):
    """Simulate data processing operations."""
    
    logger.log_stdout(f"📊 Running data processing for validator {uid}", level="INFO")
    
    batch_operations = [
        {'name': 'transaction_validation', 'size': random.randint(100, 500)},
        {'name': 'block_verification', 'size': random.randint(10, 50)},
        {'name': 'state_update', 'size': random.randint(200, 800)},
        {'name': 'merkle_proof_generation', 'size': random.randint(50, 150)}
    ]
    
    for i, operation in enumerate(batch_operations):
        logger.log_stdout(f"    Processing {operation['name']} batch ({operation['size']} items)", level="INFO")
        
        start_time = time.time()
        
        # Simulate processing time
        processing_time = operation['size'] * random.uniform(0.001, 0.005)
        time.sleep(min(processing_time, 0.3))
        
        actual_time = time.time() - start_time
        
        logger.log({
            'operation_name': operation['name'],
            'batch_size': operation['size'],
            'processing_time_seconds': actual_time,
            'throughput_items_per_second': operation['size'] / actual_time,
            'memory_peak_mb': random.uniform(250, 400),
            'cpu_usage_percent': random.uniform(70, 95),
            'success_rate_percent': random.uniform(98, 100),
            'event_type': 'data_processing'
        }, step=i)
        
        logger.log_stdout(f"    ✅ {operation['name']} completed: {operation['size']} items in {actual_time:.3f}s", level="SUCCESS")

def run_network_operations(logger, uid):
    """Simulate network operations and peer communication."""
    
    logger.log_stdout(f"🌐 Running network operations for validator {uid}", level="INFO")
    
    peers = [f"peer_{i:03d}" for i in range(10, 20)]
    
    for round_num in range(8):
        logger.log_stdout(f"🔄 Network round {round_num} starting", level="INFO")
        
        # Peer selection
        active_peers = random.sample(peers, random.randint(4, 7))
        
        peer_responses = []
        for peer in active_peers:
            response_time = random.uniform(10, 80)
            success = random.random() < 0.92  # 92% success rate
            
            peer_responses.append({
                'peer_id': peer,
                'response_time_ms': response_time,
                'success': success
            })
            
            if success:
                if response_time < 30:
                    logger.log_stdout(f"    ✅ {peer}: {response_time:.1f}ms (fast)", level="DEBUG")
                else:
                    logger.log_stdout(f"    ⚠️  {peer}: {response_time:.1f}ms (slow)", level="DEBUG")
            else:
                logger.log_stdout(f"    ❌ {peer}: timeout/error", level="WARNING")
        
        # Network round results
        successful_peers = [p for p in peer_responses if p['success']]
        avg_response_time = sum(p['response_time_ms'] for p in successful_peers) / len(successful_peers) if successful_peers else 0
        
        logger.log({
            'round': round_num,
            'total_peers': len(active_peers),
            'successful_peers': len(successful_peers),
            'success_rate_percent': (len(successful_peers) / len(active_peers)) * 100,
            'average_response_time_ms': avg_response_time,
            'consensus_reached': len(successful_peers) >= 3,
            'block_height': 2000000 + round_num,
            'event_type': 'network_round'
        }, step=round_num)
        
        if len(successful_peers) >= 3:
            logger.log_stdout(f"✅ Network consensus reached (round {round_num})", level="SUCCESS")
        else:
            logger.log_stdout(f"⚠️  Network consensus failed (round {round_num})", level="WARNING")
        
        time.sleep(0.2)

def run_maintenance_cycles(logger, uid):
    """Simulate maintenance and cleanup operations."""
    
    logger.log_stdout(f"🔧 Running maintenance cycles for validator {uid}", level="INFO")
    
    maintenance_tasks = [
        'cache_cleanup',
        'log_rotation', 
        'memory_defragmentation',
        'database_optimization',
        'peer_list_refresh'
    ]
    
    for i, task in enumerate(maintenance_tasks):
        logger.log_stdout(f"    Performing {task}...", level="DEBUG")
        
        # Simulate maintenance work
        start_time = time.time()
        time.sleep(random.uniform(0.1, 0.4))
        duration = time.time() - start_time
        
        # Maintenance results
        results = {
            'cache_cleanup': {'freed_mb': random.randint(10, 50), 'entries_cleared': random.randint(100, 500)},
            'log_rotation': {'archived_files': random.randint(2, 8), 'space_freed_mb': random.randint(20, 100)},
            'memory_defragmentation': {'fragmentation_reduced_percent': random.uniform(15, 35)},
            'database_optimization': {'queries_optimized': random.randint(5, 20), 'performance_gain_percent': random.uniform(8, 25)},
            'peer_list_refresh': {'peers_updated': random.randint(3, 12), 'new_peers_discovered': random.randint(0, 3)}
        }
        
        logger.log({
            'maintenance_task': task,
            'duration_seconds': duration,
            'results': results.get(task, {}),
            'status': 'completed',
            'event_type': 'maintenance_task'
        }, step=i)
        
        logger.log_stdout(f"    ✅ {task} completed in {duration:.2f}s", level="SUCCESS")

def run_shutdown_sequence(logger, uid):
    """Simulate graceful shutdown sequence."""
    
    logger.log_stdout(f"🔄 Initiating graceful shutdown for validator {uid}", level="INFO")
    
    shutdown_steps = [
        "Stopping new transaction acceptance",
        "Completing pending operations",
        "Saving validator state",
        "Closing network connections", 
        "Flushing logs and metrics",
        "Releasing system resources",
        "Validator shutdown complete"
    ]
    
    for i, step in enumerate(shutdown_steps):
        logger.log_stdout(f"    {step}...", level="DEBUG")
        
        time.sleep(random.uniform(0.1, 0.2))
        
        logger.log({
            'shutdown_step': i + 1,
            'step_name': step,
            'status': 'completed',
            'event_type': 'shutdown_step'
        }, step=i)
        
        if i == len(shutdown_steps) - 1:
            logger.log_stdout("✅ Validator shutdown completed successfully!", level="SUCCESS")

if __name__ == "__main__":
    """Run single comprehensive validator test."""
    
    print("🎯 Gnosis-Track Single Validator Comprehensive Test")
    print("=" * 55)
    print("This will create extensive logs for one validator (UID: 100)")
    print("covering all test scenarios:")
    print("  • Startup sequence")
    print("  • Normal operations")
    print("  • Performance testing")
    print("  • Error handling")
    print("  • Data processing")
    print("  • Network operations")
    print("  • Maintenance cycles")
    print("  • Shutdown sequence")
    print()
    
    try:
        create_comprehensive_single_validator()
        
        print(f"\n🎉 Single validator test completed!")
        print(f"\nNext steps:")
        print(f"1. Open http://localhost:8081")
        print(f"2. Select Validator 100")
        print(f"3. Watch real-time logs streaming")
        print(f"4. Test filtering by log level")
        print(f"5. Try search functionality")
        print(f"6. Test export features")
        
    except KeyboardInterrupt:
        print(f"\n⏹️  Test interrupted by user")
    except Exception as e:
        print(f"\n❌ Error during test: {e}")
        import traceback
        traceback.print_exc()