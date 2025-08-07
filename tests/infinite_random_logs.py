#!/usr/bin/env python3
"""
Infinite random log generator for Gnosis-Track UI testing.
Continuously generates realistic validator logs with random patterns.
"""

from gnosis_track.logging import ValidatorLogger
from datetime import datetime, timedelta
import time
import random
import json
import threading
import os

class MockWallet:
    class MockHotkey:
        ss58_address = '5F3sa2TJAWMqDhXG6jhV4N8ko9SxwGy8TpaNS1repo5EYjQX'
    hotkey = MockHotkey()

class InfiniteLogGenerator:
    def __init__(self, validator_uid=200, api_key=None, server_url=None):
        self.validator_uid = validator_uid
        self.wallet = MockWallet()
        self.logger = None
        self.running = False
        self.iteration = 0
        self.start_time = time.time()
        self.api_key = api_key
        self.server_url = server_url or "http://localhost:8081"
        
        # Random data generators
        self.log_levels = ['DEBUG', 'INFO', 'WARNING', 'ERROR', 'SUCCESS']
        self.level_weights = [0.3, 0.4, 0.15, 0.1, 0.05]  # More INFO, less ERROR
        
        self.event_types = [
            'transaction_processing',
            'block_validation', 
            'peer_communication',
            'consensus_participation',
            'data_synchronization',
            'system_monitoring',
            'performance_metrics',
            'error_handling',
            'maintenance_task',
            'network_operation'
        ]
        
        self.message_templates = {
            'transaction_processing': [
                "Processing transaction {tx_id} from {sender}",
                "Transaction {tx_id} validated successfully",
                "Invalid transaction {tx_id}: {error_reason}",
                "Transaction pool size: {pool_size}",
                "Gas estimation for {tx_id}: {gas_amount}"
            ],
            'block_validation': [
                "Validating block #{block_num} with {tx_count} transactions",
                "Block #{block_num} validation completed in {duration}ms",
                "Block #{block_num} rejected: {rejection_reason}",
                "New block #{block_num} added to chain",
                "Fork detected at block #{block_num}"
            ],
            'peer_communication': [
                "Connected to peer {peer_id} ({ip}:{port})",
                "Peer {peer_id} disconnected: {reason}",
                "Received {msg_type} from peer {peer_id}",
                "Broadcasting {msg_type} to {peer_count} peers",
                "Peer {peer_id} response time: {latency}ms"
            ],
            'consensus_participation': [
                "Participating in consensus round {round_num}",
                "Vote cast for block #{block_num}",
                "Consensus reached for round {round_num}",
                "Consensus timeout for round {round_num}",
                "Validator set updated: {validator_count} active"
            ],
            'system_monitoring': [
                "CPU usage: {cpu_percent}%",
                "Memory usage: {memory_mb}MB ({memory_percent}%)",
                "Disk usage: {disk_gb}GB available",
                "Network I/O: {bytes_in}↓ {bytes_out}↑",
                "System load average: {load_avg}"
            ],
            'performance_metrics': [
                "TPS: {tps} transactions per second",
                "Block time: {block_time}s",
                "Sync progress: {sync_percent}%",
                "Database size: {db_size_gb}GB",
                "Response time: {response_time}ms"
            ]
        }
    
    def start(self):
        """Start the infinite log generation."""
        print(f"🚀 Starting infinite log generator for Validator {self.validator_uid}")
        print(f"📍 Press Ctrl+C to stop")
        print(f"🌐 Monitor at: {self.server_url}")
        print(f"🔍 Select Validator {self.validator_uid} in the UI")
        print()
        
        # Check if authentication is required
        if self._is_auth_required():
            if not self.api_key:
                print("❌ Authentication is required but no API key provided")
                print("   Set GNOSIS_API_KEY environment variable or pass --api-key")
                print("   Generate a token with: gnosis-track token create --project test-project")
                return
            
            if not self._verify_api_key():
                print("❌ Invalid or expired API key")
                print("   Generate a new token with: gnosis-track token create --project test-project")
                return
        
        try:
            self.logger = ValidatorLogger(
                validator_uid=self.validator_uid,
                wallet=self.wallet,
                bucket_name='validator-logs',
                auto_start_local=True
            )
            
            # Initialize run
            config = {
                'test_type': 'infinite_random_generation',
                'validator_name': f'Infinite Test Validator {self.validator_uid}',
                'start_time': datetime.now().isoformat(),
                'description': 'Continuous random log generation for UI testing',
                'features': [
                    'real_time_streaming',
                    'random_log_levels',
                    'varied_message_types',
                    'performance_simulation',
                    'error_injection'
                ]
            }
            
            self.logger.init_run(config=config, version_tag="infinite_v1.0")
            
            self.running = True
            self._generate_logs()
            
        except KeyboardInterrupt:
            print(f"\n⏹️  Stopping log generation...")
            self.stop()
        except Exception as e:
            print(f"\n❌ Error: {e}")
            self.stop()
    
    def stop(self):
        """Stop the log generation."""
        self.running = False
        if self.logger:
            try:
                # Final summary
                runtime = time.time() - self.start_time
                self.logger.log({
                    'event_type': 'infinite_test_stopped',
                    'total_runtime_seconds': runtime,
                    'total_iterations': self.iteration,
                    'average_logs_per_second': self.iteration / runtime if runtime > 0 else 0,
                    'stopped_at': datetime.now().isoformat()
                })
                
                self.logger.log_stdout(f"🛑 Infinite test stopped after {runtime:.1f}s ({self.iteration} iterations)", level="INFO")
                self.logger.finish()
                self.logger.cleanup()
            except:
                pass
        
        print(f"✅ Log generation stopped")
        print(f"📊 Generated {self.iteration} log entries in {time.time() - self.start_time:.1f} seconds")
    
    def _generate_logs(self):
        """Main log generation loop."""
        
        while self.running:
            try:
                self.iteration += 1
                
                # Generate random log entry
                self._generate_random_log_entry()
                
                # Vary the delay to simulate real-world patterns
                delay = self._get_random_delay()
                time.sleep(delay)
                
                # Occasional status updates
                if self.iteration % 50 == 0:
                    runtime = time.time() - self.start_time
                    rate = self.iteration / runtime if runtime > 0 else 0
                    self.logger.log_stdout(
                        f"📊 Generated {self.iteration} logs ({rate:.1f} logs/sec, runtime: {runtime:.0f}s)",
                        level="INFO"
                    )
                
            except Exception as e:
                self.logger.log_stdout(f"❌ Error in log generation: {e}", level="ERROR")
                time.sleep(1)  # Brief pause before continuing
    
    def _generate_random_log_entry(self):
        """Generate a single random log entry."""
        
        # Choose random log level
        level = random.choices(self.log_levels, weights=self.level_weights)[0]
        
        # Choose random event type
        event_type = random.choice(self.event_types)
        
        # Generate random message
        message = self._generate_random_message(event_type)
        
        # Generate random metrics
        metrics = self._generate_random_metrics(event_type)
        
        # Log structured data
        self.logger.log({
            'iteration': self.iteration,
            'event_type': event_type,
            'level': level,
            'message': message,
            'metrics': metrics,
            'timestamp': datetime.now().isoformat(),
            'runtime_seconds': time.time() - self.start_time
        }, step=self.iteration)
        
        # Log human-readable message
        self.logger.log_stdout(message, level=level)
    
    def _generate_random_message(self, event_type):
        """Generate a random message for the given event type."""
        
        if event_type not in self.message_templates:
            return f"Random {event_type} event #{self.iteration}"
        
        template = random.choice(self.message_templates[event_type])
        
        # Fill in template variables with random data
        variables = {
            'tx_id': f"0x{random.randint(10000000, 99999999):08x}",
            'sender': f"0x{random.randint(1000000000000000, 9999999999999999):016x}",
            'block_num': random.randint(2000000, 2100000),
            'tx_count': random.randint(10, 200),
            'duration': random.randint(50, 500),
            'peer_id': f"peer_{random.randint(100, 999)}",
            'ip': f"{random.randint(1, 255)}.{random.randint(1, 255)}.{random.randint(1, 255)}.{random.randint(1, 255)}",
            'port': random.randint(30000, 65535),
            'latency': random.randint(10, 200),
            'round_num': random.randint(1000, 2000),
            'validator_count': random.randint(50, 150),
            'cpu_percent': random.randint(30, 95),
            'memory_mb': random.randint(200, 800),
            'memory_percent': random.randint(40, 85),
            'disk_gb': random.randint(50, 500),
            'bytes_in': f"{random.randint(1, 999)}KB",
            'bytes_out': f"{random.randint(1, 999)}KB",
            'load_avg': f"{random.uniform(0.5, 3.0):.2f}",
            'tps': random.randint(100, 1500),
            'block_time': random.uniform(2.0, 8.0),
            'sync_percent': random.uniform(95.0, 100.0),
            'db_size_gb': random.uniform(10.0, 100.0),
            'response_time': random.randint(10, 150),
            'pool_size': random.randint(10, 1000),
            'gas_amount': random.randint(21000, 500000),
            'error_reason': random.choice(['invalid signature', 'insufficient funds', 'nonce too low', 'gas limit exceeded']),
            'rejection_reason': random.choice(['invalid hash', 'timestamp out of range', 'invalid transactions']),
            'reason': random.choice(['timeout', 'network error', 'protocol mismatch']),
            'msg_type': random.choice(['block', 'transaction', 'consensus', 'handshake', 'ping']),
            'peer_count': random.randint(5, 20)
        }
        
        try:
            return template.format(**variables)
        except KeyError:
            # If template has unknown variables, return simple message
            return f"{event_type.replace('_', ' ').title()} #{self.iteration}"
    
    def _generate_random_metrics(self, event_type):
        """Generate random metrics for the event type."""
        
        base_metrics = {
            'cpu_usage_percent': random.uniform(30, 90),
            'memory_usage_mb': random.uniform(200, 600),
            'network_latency_ms': random.uniform(10, 100),
            'disk_io_mb_per_sec': random.uniform(1, 50)
        }
        
        # Add event-specific metrics
        if event_type == 'transaction_processing':
            base_metrics.update({
                'gas_used': random.randint(21000, 300000),
                'gas_price_gwei': random.uniform(10, 100),
                'processing_time_ms': random.uniform(10, 200)
            })
        elif event_type == 'block_validation':
            base_metrics.update({
                'block_size_kb': random.uniform(50, 500),
                'validation_time_ms': random.uniform(100, 1000),
                'transaction_count': random.randint(10, 200)
            })
        elif event_type == 'peer_communication':
            base_metrics.update({
                'active_connections': random.randint(5, 25),
                'data_sent_kb': random.uniform(1, 100),
                'data_received_kb': random.uniform(1, 100)
            })
        
        return base_metrics
    
    def _is_auth_required(self) -> bool:
        """Check if the server has authentication enabled."""
        try:
            import urllib.request
            import urllib.error
            
            # Try accessing the health endpoint without auth
            req = urllib.request.Request(f"{self.server_url}/health")
            response = urllib.request.urlopen(req, timeout=5)
            
            # If health endpoint is accessible, check if auth is required
            # by trying to access a protected endpoint
            req = urllib.request.Request(f"{self.server_url}/api/validators")
            try:
                urllib.request.urlopen(req, timeout=5)
                return False  # No auth required
            except urllib.error.HTTPError as e:
                if e.code == 401:
                    return True  # Auth required
                return False  # Other error, assume no auth
                
        except Exception:
            # If we can't connect, assume no auth required for local testing
            return False
    
    def _verify_api_key(self) -> bool:
        """Verify the API key with the server."""
        try:
            import urllib.request
            import urllib.error
            import json
            
            # Test the API key by getting S3 credentials
            data = json.dumps({"api_key": self.api_key}).encode('utf-8')
            req = urllib.request.Request(
                f"{self.server_url}/api/auth/s3-credentials",
                data=data,
                headers={'Content-Type': 'application/json'}
            )
            
            response = urllib.request.urlopen(req, timeout=5)
            return response.status == 200
            
        except Exception:
            return False
    
    def _get_random_delay(self):
        """Get random delay between log entries to simulate realistic patterns."""
        
        # Different delay patterns based on iteration
        if self.iteration % 100 < 10:
            # Burst mode - rapid logs
            return random.uniform(0.05, 0.2)
        elif self.iteration % 100 < 80:
            # Normal mode - moderate pace
            return random.uniform(0.2, 1.0)
        else:
            # Quiet mode - slower pace
            return random.uniform(1.0, 3.0)

def main():
    """Main entry point."""
    import argparse
    
    parser = argparse.ArgumentParser(description='Gnosis-Track Infinite Random Log Generator')
    parser.add_argument('--validator-uid', type=int, default=200, help='Validator UID (default: 200)')
    parser.add_argument('--api-key', help='API key for authentication (or set GNOSIS_API_KEY env var)')
    parser.add_argument('--server-url', default='http://localhost:8081', help='Server URL (default: http://localhost:8081)')
    
    args = parser.parse_args()
    
    print("🎯 Gnosis-Track Infinite Random Log Generator")
    print("=" * 45)
    print("This will continuously generate random validator logs")
    print("for real-time UI testing and performance validation.")
    print()
    
    # Get API key from argument or environment
    api_key = args.api_key or os.environ.get('GNOSIS_API_KEY')
    
    # If running interactively and no command line args provided
    if not any(vars(args).values()) and not api_key:
        try:
            validator_uid = int(input("Enter Validator UID (default: 200): ") or "200")
        except ValueError:
            validator_uid = 200
        
        # Check if user wants to provide API key
        if input("Enter API key (press Enter to skip): ").strip():
            api_key = input("API key: ").strip()
    else:
        validator_uid = args.validator_uid
    
    print(f"🔄 Will generate logs for Validator {validator_uid}")
    print(f"🌐 Server: {args.server_url}")
    if api_key:
        print(f"🔑 API Key: {api_key[:12]}...")
    else:
        print("🔓 No API key provided - will check if auth is required")
    print()
    
    generator = InfiniteLogGenerator(
        validator_uid=validator_uid,
        api_key=api_key,
        server_url=args.server_url
    )
    generator.start()

if __name__ == "__main__":
    main()