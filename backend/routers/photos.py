from fastapi import APIRouter, Depends, HTTPException, status, UploadFile, File, Form
from sqlalchemy.orm import Session
from typing import List, Optional
import os

from database.connection import get_db
from models.user import User
from models.event import Event
from models.event_registration import EventRegistration
from models.photo import Photo
from models.photo_face import PhotoFace
from schemas import (
    PhotoResponse,
    MessageResponse,
    PhotoFaceResponse,
    PhotoWithFaces,
    FaceProcessingRequest,
    FaceProcessingResponse
)
from utils.auth import get_current_user
from utils.file_handler import save_uploaded_file, delete_file, get_file_url
from utils.s3_storage import s3_storage
from utils.aws_config import aws_config
from utils.face_recognition_utils import (
    generate_face_embedding,
    validate_face_image,
    FaceRecognitionError,
    detect_faces_in_image,
    find_matching_users_for_event
)

router = APIRouter()

def get_secure_photo_url(image_path: str) -> str:
    """
    Get a secure URL for a photo (presigned URL for S3, direct URL for local).

    Args:
        image_path: The image path from database (S3 URL or local path)

    Returns:
        Secure URL to access the photo
    """
    if not image_path:
        return ""

    # Check if this is an S3 URL and S3 is enabled
    if aws_config.use_s3_storage and image_path.startswith('http'):
        # Extract S3 key from the URL
        s3_key = s3_storage._extract_s3_key_from_url(image_path)
        if s3_key:
            # Generate presigned URL (valid for 1 hour)
            presigned_url = s3_storage.generate_presigned_url(s3_key, expiration=3600)
            if presigned_url:
                return presigned_url
        # Fallback to original URL if presigned generation fails
        return image_path

    # For local storage, use the existing function
    return get_file_url(image_path)

@router.post("/profile", response_model=MessageResponse)
async def upload_profile_photo(
    file: UploadFile = File(...),
    current_user: User = Depends(get_current_user),
    db: Session = Depends(get_db)
):
    """Upload or update user's profile photo (selfie) and generate face embedding."""
    try:
        # Save the uploaded file
        file_path, metadata = await save_uploaded_file(
            file,
            "profiles",
            max_width=800,  # Resize to max 800px width
            max_height=800  # Resize to max 800px height
        )

        # Get the image path/URL for face recognition (works with both S3 and local)
        image_path_for_processing = file_path

        # For S3 storage, we need to use the secure URL for face processing
        if aws_config.use_s3_storage and file_path.startswith('http'):
            # Use the S3 URL directly - our face recognition utils can handle it
            image_path_for_processing = get_secure_photo_url(file_path)
        else:
            # For local storage, construct the full path
            upload_dir = os.getenv("UPLOAD_DIR", "../uploads")
            image_path_for_processing = os.path.join(upload_dir, file_path)

        # Validate that the image contains exactly one face
        if not validate_face_image(image_path_for_processing):
            # Clean up the uploaded file
            delete_file(file_path)
            raise HTTPException(
                status_code=status.HTTP_400_BAD_REQUEST,
                detail="Profile photo must contain exactly one clearly visible face. Please upload a clear selfie."
            )

        # Generate face embedding
        try:
            face_embedding = generate_face_embedding(image_path_for_processing)
            if face_embedding is None:
                # Clean up the uploaded file
                delete_file(file_path)
                raise HTTPException(
                    status_code=status.HTTP_400_BAD_REQUEST,
                    detail="Could not detect a face in the uploaded image. Please upload a clear selfie."
                )
        except FaceRecognitionError as e:
            # Clean up the uploaded file
            delete_file(file_path)
            raise HTTPException(
                status_code=status.HTTP_400_BAD_REQUEST,
                detail=f"Face recognition failed: {str(e)}"
            )

        # Delete old profile photo if exists
        if current_user.selfie_image_path:
            delete_file(current_user.selfie_image_path)

        # Update user's profile photo path and face embedding
        current_user.selfie_image_path = file_path
        current_user.embedding = face_embedding.tolist()  # Convert numpy array to list for PostgreSQL
        db.commit()

        return {"message": "Profile photo uploaded and face registered successfully"}

    except HTTPException:
        raise
    except Exception as e:
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=f"Failed to upload profile photo: {str(e)}"
        )

@router.delete("/profile", response_model=MessageResponse)
async def delete_profile_photo(
    current_user: User = Depends(get_current_user),
    db: Session = Depends(get_db)
):
    """Delete user's profile photo."""
    if not current_user.selfie_image_path:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="No profile photo found"
        )
    
    # Delete the file
    delete_file(current_user.selfie_image_path)
    
    # Update user record
    current_user.selfie_image_path = None
    db.commit()
    
    return {"message": "Profile photo deleted successfully"}

@router.post("/events/{event_identifier}", response_model=List[PhotoResponse])
async def upload_event_photos(
    event_identifier: str,
    files: List[UploadFile] = File(...),
    current_user: User = Depends(get_current_user),
    db: Session = Depends(get_db)
):
    """Upload photos to an event (by ID or event code)."""
    print(f"🔄 Photo upload request for event {event_identifier}")
    print(f"👤 User: {current_user.email}")
    print(f"📁 Number of files: {len(files)}")

    # Try to find event by code first, then by ID
    event = None

    if event_identifier.isdigit():
        # Numeric ID
        event = db.query(Event).filter(Event.id == int(event_identifier)).first()
    else:
        # Event code
        event = db.query(Event).filter(Event.event_code == event_identifier.upper()).first()

    if not event:
        print(f"❌ Event {event_identifier} not found")
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="Event not found"
        )

    print(f"✅ Event found: {event.event_name}")
    
    # Check if user has access to upload photos (owner or registered guest)
    is_owner = event.owner_id == current_user.id
    is_registered = db.query(EventRegistration).filter(
        EventRegistration.event_id == event.id,
        EventRegistration.user_id == current_user.id
    ).first() is not None
    
    if not (is_owner or is_registered):
        raise HTTPException(
            status_code=status.HTTP_403_FORBIDDEN,
            detail="Access denied. You must be the event owner or a registered guest."
        )
    
    uploaded_photos = []
    failed_uploads = []
    
    for i, file in enumerate(files):
        try:
            print(f"📁 Processing file {i+1}/{len(files)}: {file.filename}")
            print(f"   Content type: {file.content_type}")
            print(f"   File size: {getattr(file, 'size', 'unknown')} bytes")

            # Save the uploaded file
            file_path, metadata = await save_uploaded_file(
                file,
                f"events/{event.id}",
                max_width=1920,  # Resize to max 1920px width
                max_height=1080  # Resize to max 1080px height
            )

            print(f"✅ File saved: {file_path}")

            # Create photo record
            photo = Photo(
                event_id=event.id,
                image_path=file_path,
                uploaded_by=current_user.id,
                original_filename=metadata["original_filename"],
                file_size=metadata["file_size"],
                mime_type=metadata["mime_type"]
            )
            
            db.add(photo)
            db.commit()
            db.refresh(photo)
            
            uploaded_photos.append(photo)
            
        except Exception as e:
            print(f"❌ Failed to process file {file.filename}: {str(e)}")
            import traceback
            traceback.print_exc()
            failed_uploads.append({
                "filename": file.filename,
                "error": str(e)
            })
    
    if failed_uploads and not uploaded_photos:
        # All uploads failed
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail=f"All uploads failed: {failed_uploads}"
        )
    
    return uploaded_photos

@router.get("/events/{event_identifier}", response_model=List[PhotoResponse])
async def get_event_photos(
    event_identifier: str,
    current_user: User = Depends(get_current_user),
    db: Session = Depends(get_db)
):
    """Get all photos for an event (by ID or event code)."""
    # Try to find event by code first, then by ID
    event = None

    if event_identifier.isdigit():
        # Numeric ID
        event = db.query(Event).filter(Event.id == int(event_identifier)).first()
    else:
        # Event code
        event = db.query(Event).filter(Event.event_code == event_identifier.upper()).first()

    if not event:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="Event not found"
        )
    
    # Check if user has access to view photos (owner or registered guest)
    is_owner = event.owner_id == current_user.id
    is_registered = db.query(EventRegistration).filter(
        EventRegistration.event_id == event.id,
        EventRegistration.user_id == current_user.id
    ).first() is not None

    if not (is_owner or is_registered):
        raise HTTPException(
            status_code=status.HTTP_403_FORBIDDEN,
            detail="Access denied. You must be the event owner or a registered guest."
        )

    photos = db.query(Photo).filter(Photo.event_id == event.id).all()

    # Convert photos to response format with secure URLs
    photo_responses = []
    for photo in photos:
        # Create photo response with secure URL
        photo_dict = {
            "id": photo.id,
            "event_id": photo.event_id,
            "image_path": get_secure_photo_url(photo.image_path),  # Use secure URL
            "uploaded_by": photo.uploaded_by,
            "uploaded_at": photo.uploaded_at,
            "original_filename": photo.original_filename,
            "file_size": photo.file_size,
            "mime_type": photo.mime_type
        }
        photo_responses.append(photo_dict)

    return photo_responses

@router.delete("/{photo_id}", response_model=MessageResponse)
async def delete_photo(
    photo_id: int,
    current_user: User = Depends(get_current_user),
    db: Session = Depends(get_db)
):
    """Delete a photo (only by uploader or event owner)."""
    # Get photo
    photo = db.query(Photo).filter(Photo.id == photo_id).first()
    if not photo:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="Photo not found"
        )
    
    # Get event
    event = db.query(Event).filter(Event.id == photo.event_id).first()
    
    # Check permissions (uploader or event owner)
    is_uploader = photo.uploaded_by == current_user.id
    is_event_owner = event and event.owner_id == current_user.id
    
    if not (is_uploader or is_event_owner):
        raise HTTPException(
            status_code=status.HTTP_403_FORBIDDEN,
            detail="Access denied. Only the uploader or event owner can delete this photo."
        )
    
    # Delete file from storage
    delete_file(photo.image_path)
    
    # Delete photo record
    db.delete(photo)
    db.commit()
    
    return {"message": "Photo deleted successfully"}


@router.post("/process-faces", response_model=FaceProcessingResponse)
async def process_faces_in_photos(
    request: FaceProcessingRequest,
    current_user: User = Depends(get_current_user),
    db: Session = Depends(get_db)
):
    """Process photos to detect faces and match them with registered users."""
    try:
        processed_photos = 0
        total_faces_detected = 0
        total_faces_matched = 0

        upload_dir = os.getenv("UPLOAD_DIR", "../uploads")

        for photo_id in request.photo_ids:
            # Get photo
            photo = db.query(Photo).filter(Photo.id == photo_id).first()
            if not photo:
                continue

            # Check if user has access to this photo
            event = db.query(Event).filter(Event.id == photo.event_id).first()
            if not event:
                continue

            # Check if user is owner or registered for the event
            is_owner = event.owner_id == current_user.id
            is_registered = db.query(EventRegistration).filter(
                EventRegistration.event_id == event.id,
                EventRegistration.user_id == current_user.id
            ).first() is not None

            if not (is_owner or is_registered):
                continue

            # Get the image path/URL for face processing (works with both S3 and local)
            image_path_for_processing = photo.image_path

            # For S3 storage, we need to use the secure URL for face processing
            if aws_config.use_s3_storage and photo.image_path.startswith('http'):
                # Use the S3 URL directly - our face recognition utils can handle it
                image_path_for_processing = get_secure_photo_url(photo.image_path)
            else:
                # For local storage, construct the full path
                image_path_for_processing = os.path.join(upload_dir, photo.image_path)
                if not os.path.exists(image_path_for_processing):
                    continue

            # Detect faces in the photo
            try:
                faces_data = detect_faces_in_image(image_path_for_processing)

                for face_data in faces_data:
                    # Check if this face already exists
                    existing_face = db.query(PhotoFace).filter(
                        PhotoFace.photo_id == photo.id,
                        PhotoFace.face_index == face_data["face_index"]
                    ).first()

                    if existing_face:
                        continue  # Skip if already processed

                    # Find matching users (optimized to only check users registered for this event)
                    matches = find_matching_users_for_event(face_data["embedding"], event.id, db)
                    matched_user_id = matches[0][0] if matches else None

                    # Create PhotoFace record
                    photo_face = PhotoFace(
                        photo_id=photo.id,
                        face_index=face_data["face_index"],
                        embedding=face_data["embedding"].tolist(),
                        bounding_box=face_data["bounding_box"],
                        matched_user_id=matched_user_id
                    )

                    db.add(photo_face)
                    total_faces_detected += 1

                    if matched_user_id:
                        total_faces_matched += 1

                processed_photos += 1

            except FaceRecognitionError as e:
                # Log error but continue processing other photos
                print(f"Face detection failed for photo {photo_id}: {e}")
                continue

        db.commit()

        return FaceProcessingResponse(
            processed_photos=processed_photos,
            total_faces_detected=total_faces_detected,
            total_faces_matched=total_faces_matched,
            message=f"Processed {processed_photos} photos, detected {total_faces_detected} faces, matched {total_faces_matched} faces to users"
        )

    except Exception as e:
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=f"Failed to process faces: {str(e)}"
        )


@router.get("/events/{event_identifier}/with-faces", response_model=List[PhotoWithFaces])
async def get_event_photos_with_faces(
    event_identifier: str,
    current_user: User = Depends(get_current_user),
    db: Session = Depends(get_db)
):
    """Get event photos with detected faces information."""
    # Try to find event by code first, then by ID
    event = None
    if event_identifier.isdigit():
        event = db.query(Event).filter(Event.id == int(event_identifier)).first()
    else:
        event = db.query(Event).filter(Event.event_code == event_identifier.upper()).first()

    if not event:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="Event not found"
        )

    # Check if user has access to view photos
    is_owner = event.owner_id == current_user.id
    is_registered = db.query(EventRegistration).filter(
        EventRegistration.event_id == event.id,
        EventRegistration.user_id == current_user.id
    ).first() is not None

    if not (is_owner or is_registered):
        raise HTTPException(
            status_code=status.HTTP_403_FORBIDDEN,
            detail="Access denied. You must be the event owner or a registered guest."
        )

    # Get photos with faces
    photos = db.query(Photo).filter(Photo.event_id == event.id).all()

    photos_with_faces = []
    for photo in photos:
        # Get faces for this photo
        faces = db.query(PhotoFace).filter(PhotoFace.photo_id == photo.id).all()

        photo_dict = {
            "id": photo.id,
            "event_id": photo.event_id,
            "image_path": get_secure_photo_url(photo.image_path),  # Use secure URL
            "uploaded_by": photo.uploaded_by,
            "uploaded_at": photo.uploaded_at,
            "original_filename": photo.original_filename,
            "file_size": photo.file_size,
            "mime_type": photo.mime_type,
            "faces": [
                {
                    "id": face.id,
                    "photo_id": face.photo_id,
                    "face_index": face.face_index,
                    "bounding_box": face.bounding_box,
                    "matched_user_id": face.matched_user_id,
                    "created_at": face.created_at
                }
                for face in faces
            ]
        }

        photos_with_faces.append(photo_dict)

    return photos_with_faces

@router.get("/{photo_id}/url")
async def get_photo_url(
    photo_id: int,
    current_user: User = Depends(get_current_user),
    db: Session = Depends(get_db)
):
    """Get URL for a specific photo."""
    # Get photo
    photo = db.query(Photo).filter(Photo.id == photo_id).first()
    if not photo:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="Photo not found"
        )
    
    # Check if user has access to view this photo
    event = db.query(Event).filter(Event.id == photo.event_id).first()
    is_owner = event and event.owner_id == current_user.id
    is_registered = db.query(EventRegistration).filter(
        EventRegistration.event_id == photo.event_id,
        EventRegistration.user_id == current_user.id
    ).first() is not None
    
    if not (is_owner or is_registered):
        raise HTTPException(
            status_code=status.HTTP_403_FORBIDDEN,
            detail="Access denied to this photo"
        )
    
    url = get_secure_photo_url(photo.image_path)
    return {"url": url}

