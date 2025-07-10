import os
import uuid
import shutil
from typing import Optional, List
from fastapi import UploadFile, HTTPException, status
from PIL import Image
import mimetypes

from .aws_config import aws_config
from .s3_storage import s3_storage

# Configuration
UPLOAD_DIR = os.getenv("UPLOAD_DIR", "../uploads")
MAX_FILE_SIZE = int(os.getenv("MAX_FILE_SIZE", "10485760"))  # 10MB
ALLOWED_EXTENSIONS = {".jpg", ".jpeg", ".png", ".gif", ".bmp", ".webp"}
ALLOWED_MIME_TYPES = {
    "image/jpeg", "image/jpg", "image/png", "image/gif", 
    "image/bmp", "image/webp"
}

def ensure_upload_directories(subdirectory=None):
    """Ensure upload directories exist."""
    directories = [
        os.path.join(UPLOAD_DIR, "profiles"),
        os.path.join(UPLOAD_DIR, "events")
    ]

    # Add specific subdirectory if provided
    if subdirectory:
        directories.append(os.path.join(UPLOAD_DIR, subdirectory))

    for directory in directories:
        print(f"📁 Creating directory: {directory}")
        os.makedirs(directory, exist_ok=True)

def validate_image_file(file: UploadFile) -> None:
    """Validate uploaded image file."""
    print(f"🔍 Validating file: {file.filename}")
    print(f"   Content type: {file.content_type}")

    # Check file extension first
    if file.filename:
        file_extension = os.path.splitext(file.filename)[1].lower()
        print(f"   File extension: {file_extension}")

        if file_extension not in ALLOWED_EXTENSIONS:
            print(f"❌ Invalid extension: {file_extension}")
            raise HTTPException(
                status_code=status.HTTP_400_BAD_REQUEST,
                detail=f"File type not allowed. Allowed types: {', '.join(ALLOWED_EXTENSIONS)}"
            )
        print(f"✅ Extension valid: {file_extension}")
    else:
        print("❌ No filename provided")
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail="No filename provided"
        )

    # Check MIME type (be more permissive)
    if file.content_type:
        print(f"   Checking MIME type: {file.content_type}")
        if not file.content_type.startswith('image/'):
            print(f"❌ Invalid MIME type: {file.content_type}")
            raise HTTPException(
                status_code=status.HTTP_400_BAD_REQUEST,
                detail=f"Invalid file type. Must be an image file."
            )
        print(f"✅ MIME type valid: {file.content_type}")

    print("✅ File validation passed")

def generate_unique_filename(original_filename: str) -> str:
    """Generate a unique filename while preserving the extension."""
    if not original_filename:
        return f"{uuid.uuid4()}.jpg"
    
    file_extension = os.path.splitext(original_filename)[1].lower()
    if not file_extension:
        file_extension = ".jpg"
    
    return f"{uuid.uuid4()}{file_extension}"

async def save_uploaded_file(
    file: UploadFile,
    subdirectory: str,
    max_width: Optional[int] = None,
    max_height: Optional[int] = None
) -> tuple[str, dict]:
    """
    Save uploaded file and return the file path/URL and metadata.

    Args:
        file: The uploaded file
        subdirectory: Subdirectory within uploads (e.g., 'profiles', 'events')
        max_width: Maximum width for image resizing (optional)
        max_height: Maximum height for image resizing (optional)

    Returns:
        Tuple of (file_path_or_url, metadata_dict)
        - If S3 is enabled: returns (s3_url, metadata)
        - If local storage: returns (relative_path, metadata)
    """
    validate_image_file(file)

    # Check if S3 storage is enabled
    if aws_config.use_s3_storage:
        # Use S3 storage
        return await s3_storage.upload_file(file, subdirectory, max_width, max_height)

    # Use local storage (existing logic)
    ensure_upload_directories(subdirectory)
    
    # Generate unique filename
    unique_filename = generate_unique_filename(file.filename)
    
    # Create full path
    subdirectory_path = os.path.join(UPLOAD_DIR, subdirectory)
    file_path = os.path.join(subdirectory_path, unique_filename)
    
    # Save file temporarily
    temp_path = f"{file_path}.tmp"
    
    try:
        # Save uploaded file
        with open(temp_path, "wb") as buffer:
            shutil.copyfileobj(file.file, buffer)
        
        # Process image if resizing is needed
        if max_width or max_height:
            with Image.open(temp_path) as img:
                # Get EXIF data to preserve orientation
                exif_data = None
                if hasattr(img, '_getexif') and img._getexif():
                    exif_data = img.info.get('exif')
                
                # Convert to RGB if necessary (for JPEG compatibility)
                if img.mode in ("RGBA", "P"):
                    img = img.convert("RGB")
                
                # Resize if needed while preserving aspect ratio
                if max_width or max_height:
                    img.thumbnail((max_width or img.width, max_height or img.height), Image.Resampling.LANCZOS)
                
                # Save processed image with original EXIF data
                save_kwargs = {'optimize': True, 'quality': 85}
                if exif_data:
                    save_kwargs['exif'] = exif_data
                
                img.save(file_path, **save_kwargs)
        else:
            # Just move the file
            shutil.move(temp_path, file_path)
        
        # Get file metadata and validate size
        file_size = os.path.getsize(file_path)

        # Check file size after processing
        if file_size > MAX_FILE_SIZE:
            # Clean up the file
            if os.path.exists(file_path):
                os.remove(file_path)
            raise HTTPException(
                status_code=status.HTTP_413_REQUEST_ENTITY_TOO_LARGE,
                detail=f"File size ({file_size} bytes) exceeds maximum allowed size of {MAX_FILE_SIZE} bytes"
            )

        mime_type = mimetypes.guess_type(file_path)[0] or file.content_type
        
        metadata = {
            "original_filename": file.filename,
            "file_size": file_size,
            "mime_type": mime_type
        }
        
        # Return relative path for database storage
        relative_path = os.path.relpath(file_path, UPLOAD_DIR)
        return relative_path, metadata
        
    except Exception as e:
        # Clean up temporary file if it exists
        if os.path.exists(temp_path):
            os.remove(temp_path)
        
        # Clean up main file if it exists
        if os.path.exists(file_path):
            os.remove(file_path)
        
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=f"Failed to save file: {str(e)}"
        )

def delete_file(file_path_or_url: str) -> bool:
    """Delete a file from storage (S3 or local)."""
    try:
        # Check if S3 storage is enabled and this looks like an S3 URL
        if aws_config.use_s3_storage and file_path_or_url.startswith('http'):
            # This is an S3 URL
            return s3_storage.delete_file(file_path_or_url)
        else:
            # This is a local file path
            full_path = os.path.join(UPLOAD_DIR, file_path_or_url)
            if os.path.exists(full_path):
                os.remove(full_path)
                return True
            return False
    except Exception:
        return False

def get_file_url(file_path_or_url: str, base_url: str = None) -> str:
    """Generate a URL for accessing an uploaded file."""
    if not file_path_or_url:
        return ""

    # If this is already a full URL (S3), return as-is
    if file_path_or_url.startswith('http'):
        return file_path_or_url

    # Get base URL from environment if not provided
    if base_url is None:
        # Try to get from environment, fallback to localhost for development
        base_url = os.getenv("BACKEND_URL", "http://localhost:8000")

    # For local files, generate URL
    normalized_path = file_path_or_url.replace("\\", "/")
    return f"{base_url}/uploads/{normalized_path}"


