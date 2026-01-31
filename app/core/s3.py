"""
AWS S3 Service for File Storage
"""

import boto3
from botocore.exceptions import ClientError
from typing import Optional, BinaryIO
import mimetypes
from io import BytesIO

from app.core.config import settings


class S3Service:
    """AWS S3 service for private file storage"""
    
    def __init__(self):
        self._client = None
        self._resource = None
    
    @property
    def client(self):
        """Get S3 client (lazy initialization)"""
        if self._client is None:
            self._client = boto3.client(
                's3',
                aws_access_key_id=settings.AWS_ACCESS_KEY_ID,
                aws_secret_access_key=settings.AWS_SECRET_ACCESS_KEY,
                region_name=settings.AWS_REGION
            )
        return self._client
    
    @property
    def resource(self):
        """Get S3 resource (lazy initialization)"""
        if self._resource is None:
            self._resource = boto3.resource(
                's3',
                aws_access_key_id=settings.AWS_ACCESS_KEY_ID,
                aws_secret_access_key=settings.AWS_SECRET_ACCESS_KEY,
                region_name=settings.AWS_REGION
            )
        return self._resource
    
    @property
    def bucket_name(self) -> str:
        """Get bucket name from settings"""
        return settings.S3_BUCKET_NAME
    
    def upload_file(
        self,
        file_data: BinaryIO,
        s3_key: str,
        content_type: Optional[str] = None
    ) -> bool:
        """
        Upload a file to S3 private bucket
        
        Args:
            file_data: File-like object to upload
            s3_key: The key (path) in S3 bucket
            content_type: MIME type of the file
            
        Returns:
            bool: True if upload successful, False otherwise
        """
        try:
            extra_args = {}
            if content_type:
                extra_args['ContentType'] = content_type
            
            # Ensure private ACL (no public access)
            extra_args['ACL'] = 'private'
            
            self.client.upload_fileobj(
                file_data,
                self.bucket_name,
                s3_key,
                ExtraArgs=extra_args
            )
            return True
        except ClientError as e:
            print(f"S3 Upload Error: {e}")
            return False
    
    def download_file(self, s3_key: str) -> Optional[BytesIO]:
        """
        Download a file from S3 bucket
        
        Args:
            s3_key: The key (path) in S3 bucket
            
        Returns:
            BytesIO object containing file data, or None if error
        """
        try:
            file_obj = BytesIO()
            self.client.download_fileobj(
                self.bucket_name,
                s3_key,
                file_obj
            )
            file_obj.seek(0)
            return file_obj
        except ClientError as e:
            print(f"S3 Download Error: {e}")
            return None
    
    def delete_file(self, s3_key: str) -> bool:
        """
        Delete a file from S3 bucket
        
        Args:
            s3_key: The key (path) in S3 bucket
            
        Returns:
            bool: True if deletion successful, False otherwise
        """
        try:
            self.client.delete_object(
                Bucket=self.bucket_name,
                Key=s3_key
            )
            return True
        except ClientError as e:
            print(f"S3 Delete Error: {e}")
            return False
    
    def file_exists(self, s3_key: str) -> bool:
        """
        Check if a file exists in S3 bucket
        
        Args:
            s3_key: The key (path) in S3 bucket
            
        Returns:
            bool: True if file exists, False otherwise
        """
        try:
            self.client.head_object(
                Bucket=self.bucket_name,
                Key=s3_key
            )
            return True
        except ClientError:
            return False
    
    def get_file_metadata(self, s3_key: str) -> Optional[dict]:
        """
        Get metadata for a file in S3 bucket
        
        Args:
            s3_key: The key (path) in S3 bucket
            
        Returns:
            dict with metadata or None if error
        """
        try:
            response = self.client.head_object(
                Bucket=self.bucket_name,
                Key=s3_key
            )
            return {
                'content_type': response.get('ContentType'),
                'content_length': response.get('ContentLength'),
                'last_modified': response.get('LastModified'),
                'etag': response.get('ETag')
            }
        except ClientError:
            return None
    
    def get_file_stream(self, s3_key: str):
        """
        Get a streaming response for a file (for large files)
        
        Args:
            s3_key: The key (path) in S3 bucket
            
        Returns:
            Streaming body or None if error
        """
        try:
            response = self.client.get_object(
                Bucket=self.bucket_name,
                Key=s3_key
            )
            return response['Body']
        except ClientError as e:
            print(f"S3 Stream Error: {e}")
            return None


# Global S3 service instance
s3_service = S3Service()


def get_s3_service() -> S3Service:
    """Get S3 service dependency"""
    return s3_service
