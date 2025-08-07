#!/usr/bin/env python3

# Test fresh import without any caching
import sys
import importlib

# Force reload of modules to ensure we get the latest code
if 'gnosis_track.core.seaweed_client' in sys.modules:
    importlib.reload(sys.modules['gnosis_track.core.seaweed_client'])
if 'gnosis_track.logging.log_streamer' in sys.modules:
    importlib.reload(sys.modules['gnosis_track.logging.log_streamer'])

import yaml
from gnosis_track.core.seaweed_client import SeaweedClient
from gnosis_track.logging.log_streamer import LogStreamer

# Load config
with open('temp_config.yaml', 'r') as f:
    config = yaml.safe_load(f)

# Create client
client = SeaweedClient(
    endpoint_url=f"http://{config['seaweedfs']['s3_endpoint']}",
    access_key=config['seaweedfs']['access_key'],
    secret_key=config['seaweedfs']['secret_key'],
    use_ssl=config['seaweedfs']['use_ssl'],
    verify_ssl=config['seaweedfs']['verify_ssl']
)

# Create log streamer
streamer = LogStreamer(client, config['logging']['bucket_name'])

# Test get_runs
runs = streamer.get_runs(200)
print(f"Fresh import test - runs: {runs}")

# Also test the new list_prefixes method
prefixes = client.list_prefixes(config['logging']['bucket_name'], prefix="validator_200/")
print(f"Fresh import test - prefixes: {prefixes}")