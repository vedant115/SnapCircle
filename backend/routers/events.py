from fastapi import APIRouter, Depends, HTTPException, status, Query, UploadFile, File, Form
from sqlalchemy.orm import Session
from sqlalchemy import func
from typing import List, Optional
import os

from database.connection import get_db
from models.user import User
from models.event import Event
from models.event_registration import EventRegistration
from models.photo import Photo
from schemas import (
    EventCreate,
    EventResponse,
    EventWithDetails,
    EventRegistrationCreate,
    EventRegistrationWithSelfie,
    EventRegistrationResponse,
    MessageResponse,
    UserResponse
)
from utils.auth import get_current_user, get_password_hash
from utils.qr_generator import generate_event_qr_code
from utils.file_handler import save_uploaded_file, delete_file
from utils.face_recognition_utils import generate_face_embedding, validate_face_image, FaceRecognitionError

router = APIRouter()

@router.post("/", response_model=EventResponse, status_code=status.HTTP_201_CREATED)
async def create_event(
    event_data: EventCreate,
    current_user: User = Depends(get_current_user),
    db: Session = Depends(get_db)
):
    """Create a new event."""
    from models.event import generate_event_code

    # Generate unique event code
    event_code = generate_event_code()
    print(f"🎲 Generated event code: {event_code}")

    # Ensure event code is unique
    attempts = 0
    while db.query(Event).filter(Event.event_code == event_code).first():
        event_code = generate_event_code()
        attempts += 1
        print(f"🔄 Code collision, trying again: {event_code} (attempt {attempts})")
        if attempts > 10:  # Safety check
            break

    print(f"✅ Final event code: {event_code}")

    db_event = Event(
        event_code=event_code,
        event_name=event_data.event_name,
        event_date=event_data.event_date,
        description=event_data.description,
        owner_id=current_user.id
    )

    db.add(db_event)
    db.commit()
    db.refresh(db_event)

    return db_event

@router.get("/", response_model=List[EventWithDetails])
async def get_user_events(
    current_user: User = Depends(get_current_user),
    db: Session = Depends(get_db)
):
    """Get all events for the current user (owned and registered)."""
    # Get owned events
    owned_events = db.query(Event).filter(Event.owner_id == current_user.id).all()
    
    # Get registered events
    registered_events = db.query(Event).join(EventRegistration).filter(
        EventRegistration.user_id == current_user.id
    ).all()
    
    # Combine and remove duplicates
    all_events = list({event.id: event for event in owned_events + registered_events}.values())
    
    # Add counts for each event
    events_with_details = []
    for event in all_events:
        guest_count = db.query(EventRegistration).filter(
            EventRegistration.event_id == event.id
        ).count()
        
        photo_count = db.query(Photo).filter(Photo.event_id == event.id).count()
        
        event_dict = {
            "id": event.id,
            "event_code": event.event_code,
            "event_name": event.event_name,
            "event_date": event.event_date,
            "description": event.description,
            "owner_id": event.owner_id,
            "created_at": event.created_at,
            "owner": event.owner,
            "guest_count": guest_count,
            "photo_count": photo_count
        }
        events_with_details.append(event_dict)
    
    return events_with_details

@router.get("/owned", response_model=List[EventWithDetails])
async def get_owned_events(
    current_user: User = Depends(get_current_user),
    db: Session = Depends(get_db)
):
    """Get events owned by the current user."""
    events = db.query(Event).filter(Event.owner_id == current_user.id).all()
    
    events_with_details = []
    for event in events:
        guest_count = db.query(EventRegistration).filter(
            EventRegistration.event_id == event.id
        ).count()
        
        photo_count = db.query(Photo).filter(Photo.event_id == event.id).count()
        
        event_dict = {
            "id": event.id,
            "event_code": event.event_code,
            "event_name": event.event_name,
            "event_date": event.event_date,
            "description": event.description,
            "owner_id": event.owner_id,
            "created_at": event.created_at,
            "owner": event.owner,
            "guest_count": guest_count,
            "photo_count": photo_count
        }
        events_with_details.append(event_dict)
    
    return events_with_details

@router.get("/registered", response_model=List[EventWithDetails])
async def get_registered_events(
    current_user: User = Depends(get_current_user),
    db: Session = Depends(get_db)
):
    """Get events the current user is registered for (as a guest)."""
    events = db.query(Event).join(EventRegistration).filter(
        EventRegistration.user_id == current_user.id,
        Event.owner_id != current_user.id  # Exclude owned events
    ).all()
    
    events_with_details = []
    for event in events:
        guest_count = db.query(EventRegistration).filter(
            EventRegistration.event_id == event.id
        ).count()
        
        photo_count = db.query(Photo).filter(Photo.event_id == event.id).count()
        
        event_dict = {
            "id": event.id,
            "event_code": event.event_code,
            "event_name": event.event_name,
            "event_date": event.event_date,
            "description": event.description,
            "owner_id": event.owner_id,
            "created_at": event.created_at,
            "owner": event.owner,
            "guest_count": guest_count,
            "photo_count": photo_count
        }
        events_with_details.append(event_dict)
    
    return events_with_details

@router.get("/public/{event_code}", response_model=EventWithDetails)
async def get_event_public(
    event_code: str,
    db: Session = Depends(get_db)
):
    """Get basic event information for join purposes (no authentication required)."""
    event = db.query(Event).filter(Event.event_code == event_code.upper()).first()
    if not event:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="Event not found"
        )

    # Return basic event info for join purposes (no sensitive data)
    return {
        "id": event.id,
        "event_code": event.event_code,
        "event_name": event.event_name,
        "event_date": event.event_date,
        "description": event.description,
        "owner_id": event.owner_id,
        "created_at": event.created_at,
        "owner": event.owner,
        "guest_count": 0,  # Don't reveal actual count to public
        "photo_count": 0   # Don't reveal actual count to public
    }

@router.get("/{event_code}", response_model=EventWithDetails)
async def get_event(
    event_code: str,
    current_user: User = Depends(get_current_user),
    db: Session = Depends(get_db)
):
    """Get a specific event by event code."""
    event = db.query(Event).filter(Event.event_code == event_code.upper()).first()
    if not event:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="Event not found"
        )

    # Check user's relationship to this event
    is_owner = event.owner_id == current_user.id
    is_registered = db.query(EventRegistration).filter(
        EventRegistration.event_id == event.id,
        EventRegistration.user_id == current_user.id
    ).first() is not None

    # Allow viewing basic event info for join purposes, but restrict detailed access
    has_access = is_owner or is_registered

    # If user doesn't have access, return basic info only (for join flow)
    if not has_access:
        return {
            "id": event.id,
            "event_code": event.event_code,
            "event_name": event.event_name,
            "event_date": event.event_date,
            "description": event.description,
            "owner_id": event.owner_id,
            "created_at": event.created_at,
            "owner": event.owner,
            "guest_count": 0,  # Don't reveal actual count to non-members
            "photo_count": 0   # Don't reveal actual count to non-members
        }
    
    guest_count = db.query(EventRegistration).filter(
        EventRegistration.event_id == event.id
    ).count()
    
    photo_count = db.query(Photo).filter(Photo.event_id == event.id).count()
    
    return {
        "id": event.id,
        "event_code": event.event_code,
        "event_name": event.event_name,
        "event_date": event.event_date,
        "description": event.description,
        "owner_id": event.owner_id,
        "created_at": event.created_at,
        "owner": event.owner,
        "guest_count": guest_count,
        "photo_count": photo_count
    }

@router.post("/{event_code}/join", response_model=EventRegistrationResponse, status_code=status.HTTP_201_CREATED)
async def join_event(
    event_code: str,
    current_user: User = Depends(get_current_user),
    db: Session = Depends(get_db)
):
    """Join an event as a guest."""
    # Check if event exists
    event = db.query(Event).filter(Event.event_code == event_code.upper()).first()
    if not event:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="Event not found"
        )

    # Check if user is the owner
    if event.owner_id == current_user.id:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail="Cannot join your own event"
        )

    # Check if already registered
    existing_registration = db.query(EventRegistration).filter(
        EventRegistration.event_id == event.id,
        EventRegistration.user_id == current_user.id
    ).first()

    if existing_registration:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail="Already registered for this event"
        )

    # Create registration
    registration = EventRegistration(
        user_id=current_user.id,
        event_id=event.id,
        role="guest"
    )

    db.add(registration)
    db.commit()
    db.refresh(registration)

    return registration

@router.delete("/{event_code}/leave", response_model=MessageResponse)
async def leave_event(
    event_code: str,
    current_user: User = Depends(get_current_user),
    db: Session = Depends(get_db)
):
    """Leave an event (remove registration)."""
    # Check if event exists
    event = db.query(Event).filter(Event.event_code == event_code.upper()).first()
    if not event:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="Event not found"
        )

    # Check if user is the owner
    if event.owner_id == current_user.id:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail="Cannot leave your own event"
        )

    # Find registration
    registration = db.query(EventRegistration).filter(
        EventRegistration.event_id == event.id,
        EventRegistration.user_id == current_user.id
    ).first()

    if not registration:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail="Not registered for this event"
        )

    db.delete(registration)
    db.commit()

    return {"message": "Successfully left the event"}

@router.get("/{event_code}/guests", response_model=List[UserResponse])
async def get_event_guests(
    event_code: str,
    current_user: User = Depends(get_current_user),
    db: Session = Depends(get_db)
):
    """Get list of guests for an event (only accessible by event owner)."""
    # Check if event exists
    event = db.query(Event).filter(Event.event_code == event_code.upper()).first()
    if not event:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="Event not found"
        )

    # Check if user is the owner
    if event.owner_id != current_user.id:
        raise HTTPException(
            status_code=status.HTTP_403_FORBIDDEN,
            detail="Only event owner can view guest list"
        )

    # Get guests
    guests = db.query(User).join(EventRegistration).filter(
        EventRegistration.event_id == event.id
    ).all()

    return guests

@router.delete("/{event_code}", response_model=MessageResponse)
async def delete_event(
    event_code: str,
    current_user: User = Depends(get_current_user),
    db: Session = Depends(get_db)
):
    """Delete an event (only accessible by event owner)."""
    # Check if event exists
    event = db.query(Event).filter(Event.event_code == event_code.upper()).first()
    if not event:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="Event not found"
        )

    # Check if user is the owner
    if event.owner_id != current_user.id:
        raise HTTPException(
            status_code=status.HTTP_403_FORBIDDEN,
            detail="Only event owner can delete the event"
        )

    db.delete(event)
    db.commit()

    return {"message": "Event deleted successfully"}

@router.get("/{event_code}/qr-code")
async def get_event_qr_code(
    event_code: str,
    current_user: User = Depends(get_current_user),
    db: Session = Depends(get_db)
):
    """Generate QR code for event registration (only accessible by event owner)."""
    # Check if event exists
    event = db.query(Event).filter(Event.event_code == event_code.upper()).first()
    if not event:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="Event not found"
        )

    # Check if user is the owner
    if event.owner_id != current_user.id:
        raise HTTPException(
            status_code=status.HTTP_403_FORBIDDEN,
            detail="Only event owner can generate QR code"
        )

    # Generate QR code
    qr_code_data = generate_event_qr_code(event.event_code)

    return {
        "qr_code": qr_code_data,
        "registration_url": f"http://localhost:3000/join/{event.event_code}"
    }

@router.get("/code/{event_code}", response_model=EventWithDetails)
async def get_event_by_code(
    event_code: str,
    current_user: User = Depends(get_current_user),
    db: Session = Depends(get_db)
):
    """Get a specific event by event code."""
    event = db.query(Event).filter(Event.event_code == event_code.upper()).first()
    if not event:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="Event not found"
        )

    # Check user's relationship to this event
    is_owner = event.owner_id == current_user.id
    is_registered = db.query(EventRegistration).filter(
        EventRegistration.event_id == event.id,
        EventRegistration.user_id == current_user.id
    ).first() is not None

    # Allow viewing basic event info for join purposes, but restrict detailed access
    has_access = is_owner or is_registered

    # If user doesn't have access, return basic info only (for join flow)
    if not has_access:
        return {
            "id": event.id,
            "event_code": event.event_code,
            "event_name": event.event_name,
            "event_date": event.event_date,
            "description": event.description,
            "owner_id": event.owner_id,
            "created_at": event.created_at,
            "owner": event.owner,
            "guest_count": 0,  # Don't reveal actual count to non-members
            "photo_count": 0   # Don't reveal actual count to non-members
        }

    guest_count = db.query(EventRegistration).filter(
        EventRegistration.event_id == event.id
    ).count()

    photo_count = db.query(Photo).filter(Photo.event_id == event.id).count()

    return {
        "id": event.id,
        "event_code": event.event_code,
        "event_name": event.event_name,
        "event_date": event.event_date,
        "description": event.description,
        "owner_id": event.owner_id,
        "created_at": event.created_at,
        "owner": event.owner,
        "guest_count": guest_count,
        "photo_count": photo_count
    }

@router.post("/code/{event_code}/join", response_model=EventRegistrationResponse, status_code=status.HTTP_201_CREATED)
async def join_event_by_code(
    event_code: str,
    current_user: User = Depends(get_current_user),
    db: Session = Depends(get_db)
):
    """Join an event using event code."""
    # Check if event exists
    event = db.query(Event).filter(Event.event_code == event_code.upper()).first()
    if not event:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="Event not found"
        )

    # Check if user is the owner
    if event.owner_id == current_user.id:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail="Cannot join your own event"
        )

    # Check if already registered
    existing_registration = db.query(EventRegistration).filter(
        EventRegistration.event_id == event.id,
        EventRegistration.user_id == current_user.id
    ).first()

    if existing_registration:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail="Already registered for this event"
        )

    # Create registration
    registration = EventRegistration(
        user_id=current_user.id,
        event_id=event.id,
        role="guest"
    )

    db.add(registration)
    db.commit()
    db.refresh(registration)

    return registration


@router.post("/code/{event_code}/register-with-selfie", response_model=EventRegistrationResponse, status_code=status.HTTP_201_CREATED)
async def register_and_join_event_with_selfie(
    event_code: str,
    name: str = Form(...),
    email: str = Form(...),
    password: str = Form(...),
    selfie: UploadFile = File(...),
    db: Session = Depends(get_db)
):
    """Register a new user with selfie and join an event."""
    print(f"🔄 Registration request for event {event_code}")
    print(f"👤 User data: name={name}, email={email}")
    print(f"📁 Selfie file: {selfie.filename}, size={selfie.size if hasattr(selfie, 'size') else 'unknown'}")

    try:
        # Check if event exists
        event = db.query(Event).filter(Event.event_code == event_code.upper()).first()
        if not event:
            raise HTTPException(
                status_code=status.HTTP_404_NOT_FOUND,
                detail="Event not found"
            )

        # Check if user already exists
        existing_user = db.query(User).filter(User.email == email).first()
        if existing_user:
            raise HTTPException(
                status_code=status.HTTP_400_BAD_REQUEST,
                detail="Email already registered. Please login instead."
            )

        # Save the selfie file
        file_path, metadata = await save_uploaded_file(
            selfie,
            "profiles",
            max_width=800,
            max_height=800
        )

        # Get the image path/URL for face recognition (works with both S3 and local)
        from utils.aws_config import aws_config
        from routers.photos import get_secure_photo_url

        image_path_for_processing = file_path

        # For S3 storage, we need to use the secure URL for face processing
        if aws_config.use_s3_storage and file_path.startswith('http'):
            # Use the S3 URL directly - our face recognition utils can handle it
            image_path_for_processing = get_secure_photo_url(file_path)
        else:
            # For local storage, construct the full path
            upload_dir = os.getenv("UPLOAD_DIR", "../uploads")
            image_path_for_processing = os.path.join(upload_dir, file_path)

        # Validate that the image contains a suitable face for recognition
        print(f"🔍 Validating face in selfie: {image_path_for_processing}")
        if not validate_face_image(image_path_for_processing):
            print(f"❌ Face validation failed for {image_path_for_processing}")
            delete_file(file_path)
            raise HTTPException(
                status_code=status.HTTP_400_BAD_REQUEST,
                detail="Selfie must contain at least one clearly visible face. Please upload a clear photo of your face."
            )
        print(f"✅ Face validation passed for {image_path_for_processing}")

        # Generate face embedding
        print(f"🤖 Generating face embedding for {image_path_for_processing}")
        try:
            face_embedding = generate_face_embedding(image_path_for_processing)
            if face_embedding is None:
                print(f"❌ No face embedding generated for {image_path_for_processing}")
                delete_file(file_path)
                raise HTTPException(
                    status_code=status.HTTP_400_BAD_REQUEST,
                    detail="Could not detect a face in the uploaded selfie. Please try a clearer photo."
                )
            print(f"✅ Face embedding generated successfully, shape: {face_embedding.shape}")
        except FaceRecognitionError as e:
            print(f"❌ Face recognition error: {str(e)}")
            delete_file(file_path)
            raise HTTPException(
                status_code=status.HTTP_400_BAD_REQUEST,
                detail=f"Face recognition failed: {str(e)}"
            )
        except Exception as e:
            print(f"❌ Unexpected error during face embedding: {str(e)}")
            delete_file(file_path)
            raise HTTPException(
                status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
                detail="An unexpected error occurred during face processing. Please try again."
            )

        # Create new user with face embedding
        print(f"👤 Creating new user: {name} ({email})")
        hashed_password = get_password_hash(password)
        new_user = User(
            name=name,
            email=email,
            password_hash=hashed_password,
            selfie_image_path=file_path,
            embedding=face_embedding.tolist()
        )
        print(f"✅ User object created successfully")

        # Save user to database
        print(f"💾 Saving user to database")
        db.add(new_user)
        db.commit()
        db.refresh(new_user)
        print(f"✅ User saved with ID: {new_user.id}")

        # Register user for the event
        print(f"🎫 Registering user for event")
        registration = EventRegistration(
            user_id=new_user.id,
            event_id=event.id,
            role="guest"
        )

        db.add(registration)
        db.commit()
        db.refresh(registration)
        print(f"✅ Registration completed with ID: {registration.id}")

        return registration

    except HTTPException:
        raise
    except Exception as e:
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=f"Failed to register user and join event: {str(e)}"
        )
