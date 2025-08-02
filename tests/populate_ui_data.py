#!/usr/bin/env python3
"""
Quick script to populate the validator-logs bucket with data for the UI demo.
This creates validators 1, 2, 3 with sample log data.
"""

from gnosis_track.logging import ValidatorLogger
from datetime import datetime
import time

class MockWallet:
    class MockHotkey:
        ss58_address = '5F3sa2TJAWMqDhXG6jhV4N8ko9SxwGy8TpaNS1repo5EYjQX'
    hotkey = MockHotkey()

wallet = MockWallet()

# Create data specifically in validator-logs bucket
for uid in [1, 2, 3]:
    print(f'Creating validator {uid} in validator-logs...')
    logger = ValidatorLogger(
        validator_uid=uid,
        wallet=wallet,
        bucket_name='validator-logs',  # Explicitly use this bucket
        auto_start_local=True
    )
    
    logger.init_run(config={'test': f'ui_demo_validator_{uid}'})
    
    for i in range(3):
        logger.log({
            'step': i, 
            'message': f'UI Demo - Validator {uid} step {i}',
            'level': 'INFO',
            'timestamp': datetime.now().isoformat()
        })
        logger.log_stdout(f'[Validator {uid}] Processing step {i} - this should appear in UI')
        time.sleep(0.1)
    
    logger.finish()
    logger.cleanup()
    print(f'✅ Validator {uid} added to validator-logs bucket')

print('Done! Check the UI now.')