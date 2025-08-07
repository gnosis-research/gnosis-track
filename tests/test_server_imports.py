#!/usr/bin/env python3

# Test what the UI server is actually importing
import sys
print("Python path:")
for p in sys.path:
    print(f"  {p}")

print("\nImporting LogStreamer...")
from gnosis_track.logging.log_streamer import LogStreamer
print(f"LogStreamer location: {LogStreamer.__module__}")
print(f"LogStreamer file: {LogStreamer.__module__.__file__ if hasattr(LogStreamer.__module__, '__file__') else 'Unknown'}")

# Check the actual method code
import inspect
print("\nget_runs method code:")
print(inspect.getsource(LogStreamer.get_runs))