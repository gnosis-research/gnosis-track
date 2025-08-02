"""
Gnosis Track - Secure distributed object storage and logging with SeaweedFS

A modern replacement for MinIO-based logging systems, providing:
- SeaweedFS integration for better performance and scalability
- Enhanced security with encryption and authentication
- Improved UI for log management and visualization
- Easy installation and deployment
"""

__version__ = "0.1.0"
__author__ = "Data Universe Team"
__email__ = "team@data-universe.ai"

from gnosis_track.core.seaweed_client import SeaweedClient
from gnosis_track.core.bucket_manager import BucketManager
from gnosis_track.logging.validator_logger import ValidatorLogger

__all__ = [
    "SeaweedClient", 
    "BucketManager", 
    "ValidatorLogger",
]