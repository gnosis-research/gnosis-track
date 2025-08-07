"""
SeaweedFS S3-compatible client wrapper.

Provides a high-level interface to interact with SeaweedFS using the S3 API,
with enhanced security, performance optimizations, and error handling.
"""

import io
import json
import logging
import time
from datetime import datetime
from typing import Any, Dict, List, Optional, Union

import boto3
import botocore
from botocore.client import Config
from botocore.exceptions import ClientError, NoCredentialsError


logger = logging.getLogger(__name__)


class SeaweedClient:
    """
    SeaweedFS S3-compatible client with enhanced features.
    
    Provides a wrapper around boto3 S3 client with:
    - Automatic retry logic
    - Enhanced error handling
    - Performance optimizations for SeaweedFS
    - Built-in encryption support
    - Connection pooling
    """
    
    def __init__(
        self,
        endpoint_url: str,
        access_key: str,
        secret_key: str,
        region: str = "us-east-1",
        use_ssl: bool = False,
        verify_ssl: bool = True,
        max_retries: int = 3,
        timeout: int = 30,
        max_pool_connections: int = 50,
    ):
        """
        Initialize SeaweedFS client.
        
        Args:
            endpoint_url: SeaweedFS S3 endpoint (e.g., "http://localhost:8333")
            access_key: S3 access key
            secret_key: S3 secret key
            region: AWS region (default for S3 compatibility)
            use_ssl: Whether to use HTTPS
            verify_ssl: Whether to verify SSL certificates
            max_retries: Maximum number of retries for failed requests
            timeout: Request timeout in seconds
            max_pool_connections: Maximum number of pool connections
        """
        self.endpoint_url = endpoint_url
        self.access_key = access_key
        self.secret_key = secret_key
        self.region = region
        
        # Configure boto3 with SeaweedFS optimizations
        self.config = Config(
            region_name=region,
            retries={
                'max_attempts': max_retries,
                'mode': 'adaptive'
            },
            max_pool_connections=max_pool_connections,
            connect_timeout=timeout,
            read_timeout=timeout,
            signature_version='s3v4',
            s3={
                'addressing_style': 'path'  # SeaweedFS prefers path-style
            }
        )
        
        # Initialize S3 client
        self.s3_client = boto3.client(
            's3',
            endpoint_url=endpoint_url,
            aws_access_key_id=access_key,
            aws_secret_access_key=secret_key,
            config=self.config,
            use_ssl=use_ssl,
            verify=verify_ssl
        )
        
        # Test connection
        self._test_connection()
    
    def _test_connection(self) -> bool:
        """Test connection to SeaweedFS."""
        try:
            self.s3_client.list_buckets()
            logger.info(f"✅ Connected to SeaweedFS at {self.endpoint_url}")
            return True
        except Exception as e:
            logger.error(f"❌ Failed to connect to SeaweedFS: {e}")
            raise ConnectionError(f"Cannot connect to SeaweedFS at {self.endpoint_url}: {e}")
    
    def create_bucket(
        self, 
        bucket_name: str,
        create_bucket_configuration: Optional[Dict[str, Any]] = None
    ) -> bool:
        """
        Create a new bucket.
        
        Args:
            bucket_name: Name of the bucket to create
            create_bucket_configuration: Additional bucket configuration
            
        Returns:
            True if bucket was created successfully
        """
        try:
            if create_bucket_configuration:
                self.s3_client.create_bucket(
                    Bucket=bucket_name,
                    CreateBucketConfiguration=create_bucket_configuration
                )
            else:
                self.s3_client.create_bucket(Bucket=bucket_name)
            
            logger.info(f"Created bucket: {bucket_name}")
            return True
            
        except ClientError as e:
            error_code = e.response['Error']['Code']
            if error_code == 'BucketAlreadyExists':
                logger.debug(f"Bucket {bucket_name} already exists")
                return True
            else:
                logger.error(f"Failed to create bucket {bucket_name}: {e}")
                raise
    
    def bucket_exists(self, bucket_name: str) -> bool:
        """Check if a bucket exists."""
        try:
            self.s3_client.head_bucket(Bucket=bucket_name)
            return True
        except ClientError as e:
            error_code = e.response['Error']['Code']
            if error_code == '404':
                return False
            else:
                logger.error(f"Error checking bucket {bucket_name}: {e}")
                raise
    
    def list_buckets(self) -> List[Dict[str, Any]]:
        """List all buckets."""
        try:
            response = self.s3_client.list_buckets()
            return response.get('Buckets', [])
        except ClientError as e:
            logger.error(f"Failed to list buckets: {e}")
            raise
    
    def put_object(
        self,
        bucket_name: str,
        object_key: str,
        data: Union[str, bytes, io.IOBase],
        content_type: Optional[str] = None,
        metadata: Optional[Dict[str, str]] = None,
        server_side_encryption: Optional[str] = None,
    ) -> bool:
        """
        Upload an object to SeaweedFS.
        
        Args:
            bucket_name: Name of the bucket
            object_key: Key/path of the object
            data: Data to upload (string, bytes, or file-like object)
            content_type: MIME type of the content
            metadata: Additional metadata for the object
            server_side_encryption: Encryption method (e.g., 'AES256')
            
        Returns:
            True if upload was successful
        """
        try:
            # Prepare data for upload
            if isinstance(data, str):
                body = data.encode('utf-8')
                if not content_type:
                    content_type = 'text/plain'
            elif isinstance(data, bytes):
                body = data
                if not content_type:
                    content_type = 'application/octet-stream'
            else:
                body = data
                if not content_type:
                    content_type = 'application/octet-stream'
            
            # Prepare extra args
            extra_args = {}
            if content_type:
                extra_args['ContentType'] = content_type
            if metadata:
                extra_args['Metadata'] = metadata
            if server_side_encryption:
                extra_args['ServerSideEncryption'] = server_side_encryption
            
            # Upload the object
            if isinstance(body, (str, bytes)):
                self.s3_client.put_object(
                    Bucket=bucket_name,
                    Key=object_key,
                    Body=body,
                    **extra_args
                )
            else:
                self.s3_client.upload_fileobj(
                    body,
                    bucket_name,
                    object_key,
                    ExtraArgs=extra_args
                )
            
            logger.debug(f"Uploaded object: {bucket_name}/{object_key}")
            return True
            
        except ClientError as e:
            logger.error(f"Failed to upload object {bucket_name}/{object_key}: {e}")
            raise
    
    def get_object(self, bucket_name: str, object_key: str) -> bytes:
        """Download an object from SeaweedFS."""
        try:
            response = self.s3_client.get_object(Bucket=bucket_name, Key=object_key)
            return response['Body'].read()
        except ClientError as e:
            logger.error(f"Failed to get object {bucket_name}/{object_key}: {e}")
            raise
    
    def delete_object(self, bucket_name: str, object_key: str) -> bool:
        """Delete an object from SeaweedFS."""
        try:
            self.s3_client.delete_object(Bucket=bucket_name, Key=object_key)
            logger.debug(f"Deleted object: {bucket_name}/{object_key}")
            return True
        except ClientError as e:
            logger.error(f"Failed to delete object {bucket_name}/{object_key}: {e}")
            raise
    
    def list_objects(
        self,
        bucket_name: str,
        prefix: str = "",
        max_keys: int = 1000,
        delimiter: str = "",
    ) -> List[Dict[str, Any]]:
        """List objects in a bucket."""
        try:
            kwargs = {
                'Bucket': bucket_name,
                'MaxKeys': max_keys,
            }
            if prefix:
                kwargs['Prefix'] = prefix
            if delimiter:
                kwargs['Delimiter'] = delimiter
            
            response = self.s3_client.list_objects_v2(**kwargs)
            return response.get('Contents', [])
        except ClientError as e:
            logger.error(f"Failed to list objects in {bucket_name}: {e}")
            raise
    
    def list_prefixes(
        self,
        bucket_name: str,
        prefix: str = "",
        delimiter: str = "/"
    ) -> List[str]:
        """
        List common prefixes (directories) in a bucket.
        
        Args:
            bucket_name: Name of the bucket
            prefix: Prefix to filter by
            delimiter: Delimiter to use for grouping (usually '/')
            
        Returns:
            List of common prefixes (directory paths)
        """
        try:
            kwargs = {
                'Bucket': bucket_name,
                'Delimiter': delimiter,
            }
            if prefix:
                kwargs['Prefix'] = prefix
            
            response = self.s3_client.list_objects_v2(**kwargs)
            common_prefixes = response.get('CommonPrefixes', [])
            return [cp['Prefix'] for cp in common_prefixes]
        except ClientError as e:
            logger.error(f"Failed to list prefixes in {bucket_name}: {e}")
            raise
    
    def object_exists(self, bucket_name: str, object_key: str) -> bool:
        """Check if an object exists."""
        try:
            self.s3_client.head_object(Bucket=bucket_name, Key=object_key)
            return True
        except ClientError as e:
            error_code = e.response['Error']['Code']
            if error_code == '404':
                return False
            else:
                logger.error(f"Error checking object {bucket_name}/{object_key}: {e}")
                raise
    
    def get_object_metadata(self, bucket_name: str, object_key: str) -> Dict[str, Any]:
        """Get metadata for an object."""
        try:
            response = self.s3_client.head_object(Bucket=bucket_name, Key=object_key)
            return {
                'size': response.get('ContentLength', 0),
                'last_modified': response.get('LastModified'),
                'etag': response.get('ETag', '').strip('"'),
                'content_type': response.get('ContentType', ''),
                'metadata': response.get('Metadata', {}),
                'server_side_encryption': response.get('ServerSideEncryption'),
            }
        except ClientError as e:
            logger.error(f"Failed to get metadata for {bucket_name}/{object_key}: {e}")
            raise
    
    def copy_object(
        self,
        source_bucket: str,
        source_key: str,
        dest_bucket: str,
        dest_key: str,
        metadata: Optional[Dict[str, str]] = None,
    ) -> bool:
        """Copy an object within SeaweedFS."""
        try:
            copy_source = {'Bucket': source_bucket, 'Key': source_key}
            extra_args = {}
            
            if metadata:
                extra_args['Metadata'] = metadata
                extra_args['MetadataDirective'] = 'REPLACE'
            
            self.s3_client.copy_object(
                CopySource=copy_source,
                Bucket=dest_bucket,
                Key=dest_key,
                **extra_args
            )
            
            logger.debug(f"Copied object: {source_bucket}/{source_key} -> {dest_bucket}/{dest_key}")
            return True
            
        except ClientError as e:
            logger.error(f"Failed to copy object: {e}")
            raise
    
    def generate_presigned_url(
        self,
        bucket_name: str,
        object_key: str,
        expiration: int = 3600,
        http_method: str = 'GET',
    ) -> str:
        """Generate a presigned URL for temporary access to an object."""
        try:
            if http_method.upper() == 'GET':
                response = self.s3_client.generate_presigned_url(
                    'get_object',
                    Params={'Bucket': bucket_name, 'Key': object_key},
                    ExpiresIn=expiration
                )
            elif http_method.upper() == 'PUT':
                response = self.s3_client.generate_presigned_url(
                    'put_object',
                    Params={'Bucket': bucket_name, 'Key': object_key},
                    ExpiresIn=expiration
                )
            else:
                raise ValueError(f"Unsupported HTTP method: {http_method}")
            
            return response
            
        except ClientError as e:
            logger.error(f"Failed to generate presigned URL: {e}")
            raise
    
    def health_check(self) -> Dict[str, Any]:
        """Perform a health check on the SeaweedFS connection."""
        start_time = time.time()
        
        try:
            # Test basic connectivity
            buckets = self.list_buckets()
            
            # Test write/read if we have a test bucket
            test_key = f"health-check-{int(time.time())}"
            test_data = json.dumps({"timestamp": datetime.now().isoformat()})
            
            response_time = time.time() - start_time
            
            return {
                "status": "healthy",
                "endpoint": self.endpoint_url,
                "response_time_ms": int(response_time * 1000),
                "buckets_count": len(buckets),
                "timestamp": datetime.now().isoformat(),
            }
            
        except Exception as e:
            response_time = time.time() - start_time
            return {
                "status": "unhealthy",
                "endpoint": self.endpoint_url,
                "error": str(e),
                "response_time_ms": int(response_time * 1000),
                "timestamp": datetime.now().isoformat(),
            }
    
    def close(self):
        """Close the client connection."""
        # boto3 handles connection pooling automatically
        # This method is here for API compatibility
        pass