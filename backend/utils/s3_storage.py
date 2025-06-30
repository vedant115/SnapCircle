import os
import uuid
import mimetypes
from typing import Optional, Tuple, Dict, Any
from fastapi import UploadFile, HTTPException, status
from botocore.exceptions import ClientError
from PIL import Image
import io

from .aws_config import aws_config

class S3StorageManager:
    """Manages file uploads, downloads, and operations with AWS S3."""
    
    def __init__(self):
        self.config = aws_config
    
    def generate_s3_key(self, subdirectory: str, filename: str) -> str:
        """Generate S3 object key with subdirectory structure."""
        # Ensure subdirectory doesn't start with /
        subdirectory = subdirectory.lstrip('/')
        return f"{subdirectory}/{filename}"
    
    def generate_unique_filename(self, original_filename: str) -> str:
        """Generate a unique filename while preserving the extension."""
        if not original_filename:
            return f"{uuid.uuid4()}.jpg"
        
        file_extension = os.path.splitext(original_filename)[1].lower()
        if not file_extension:
            file_extension = ".jpg"
        
        return f"{uuid.uuid4()}{file_extension}"
    
    async def upload_file(
        self,
        file: UploadFile,
        subdirectory: str,
        max_width: Optional[int] = None,
        max_height: Optional[int] = None
    ) -> Tuple[str, Dict[str, Any]]:
        """
        Upload file to S3 and return the S3 URL and metadata.
        
        Args:
            file: The uploaded file
            subdirectory: Subdirectory within bucket (e.g., 'profiles', 'events/123')
            max_width: Maximum width for image resizing (optional)
            max_height: Maximum height for image resizing (optional)
        
        Returns:
            Tuple of (s3_url, metadata_dict)
        """
        if not self.config.use_s3_storage:
            raise ValueError("S3 storage is disabled")
        
        try:
            # Generate unique filename
            unique_filename = self.generate_unique_filename(file.filename)
            s3_key = self.generate_s3_key(subdirectory, unique_filename)
            
            # Read file content
            file_content = await file.read()
            file_size = len(file_content)
            
            # Process image if resizing is needed
            if max_width or max_height:
                file_content, file_size = self._process_image(
                    file_content, max_width, max_height
                )
            
            # Determine content type
            content_type = file.content_type or mimetypes.guess_type(file.filename)[0] or 'application/octet-stream'
            
            # Upload to S3
            self.config.s3_client.put_object(
                Bucket=self.config.bucket_name,
                Key=s3_key,
                Body=file_content,
                ContentType=content_type,
                Metadata={
                    'original_filename': file.filename or '',
                    'uploaded_by': 'snapcircle_app'
                }
            )
            
            # Generate S3 URL
            s3_url = f"{self.config.bucket_url}/{s3_key}"
            
            metadata = {
                "original_filename": file.filename,
                "file_size": file_size,
                "mime_type": content_type,
                "s3_key": s3_key
            }
            
            return s3_url, metadata
            
        except ClientError as e:
            raise HTTPException(
                status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
                detail=f"Failed to upload file to S3: {e}"
            )
        except Exception as e:
            raise HTTPException(
                status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
                detail=f"Error processing file upload: {e}"
            )
    
    def _process_image(
        self,
        file_content: bytes,
        max_width: Optional[int],
        max_height: Optional[int]
    ) -> Tuple[bytes, int]:
        """Process and resize image if needed."""
        try:
            # Open image from bytes
            with Image.open(io.BytesIO(file_content)) as img:
                # Get EXIF data to preserve orientation
                exif_data = None
                if hasattr(img, '_getexif') and img._getexif():
                    exif_data = img.info.get('exif')
                
                # Convert to RGB if necessary (for JPEG compatibility)
                if img.mode in ("RGBA", "P"):
                    img = img.convert("RGB")
                
                # Resize if needed while preserving aspect ratio
                if max_width or max_height:
                    img.thumbnail(
                        (max_width or img.width, max_height or img.height),
                        Image.Resampling.LANCZOS
                    )
                
                # Save processed image to bytes
                output = io.BytesIO()
                save_kwargs = {'format': 'JPEG', 'optimize': True, 'quality': 85}
                if exif_data:
                    save_kwargs['exif'] = exif_data
                
                img.save(output, **save_kwargs)
                processed_content = output.getvalue()
                
                return processed_content, len(processed_content)
                
        except Exception as e:
            # If image processing fails, return original content
            print(f"Warning: Image processing failed: {e}")
            return file_content, len(file_content)
    
    def delete_file(self, s3_url: str) -> bool:
        """
        Delete file from S3 using its URL.
        
        Args:
            s3_url: The S3 URL of the file to delete
            
        Returns:
            True if successful, False otherwise
        """
        if not self.config.use_s3_storage:
            return False
        
        try:
            # Extract S3 key from URL
            s3_key = self._extract_s3_key_from_url(s3_url)
            if not s3_key:
                return False
            
            # Delete from S3
            self.config.s3_client.delete_object(
                Bucket=self.config.bucket_name,
                Key=s3_key
            )
            return True
            
        except ClientError as e:
            print(f"Error deleting file from S3: {e}")
            return False
    
    def _extract_s3_key_from_url(self, s3_url: str) -> Optional[str]:
        """Extract S3 key from S3 URL."""
        try:
            # Remove bucket URL prefix to get the key
            if s3_url.startswith(self.config.bucket_url):
                return s3_url[len(self.config.bucket_url):].lstrip('/')
            return None
        except Exception:
            return None
    
    def get_file_url(self, s3_key: str) -> str:
        """Generate public URL for S3 object."""
        return f"{self.config.bucket_url}/{s3_key}"
    
    def generate_presigned_url(self, s3_key: str, expiration: int = 3600) -> Optional[str]:
        """
        Generate a presigned URL for private S3 objects.
        
        Args:
            s3_key: S3 object key
            expiration: URL expiration time in seconds (default: 1 hour)
            
        Returns:
            Presigned URL or None if error
        """
        if not self.config.use_s3_storage:
            return None
        
        try:
            response = self.config.s3_client.generate_presigned_url(
                'get_object',
                Params={'Bucket': self.config.bucket_name, 'Key': s3_key},
                ExpiresIn=expiration
            )
            return response
        except ClientError as e:
            print(f"Error generating presigned URL: {e}")
            return None

# Global instance
s3_storage = S3StorageManager()
