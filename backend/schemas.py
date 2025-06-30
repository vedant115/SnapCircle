from pydantic import BaseModel, EmailStr
from datetime import datetime, date
from typing import Optional, List

# User schemas
class UserBase(BaseModel):
    name: str
    email: EmailStr

class UserCreate(UserBase):
    password: str
    selfie_image_path: Optional[str] = None

class UserResponse(UserBase):
    id: int
    selfie_image_path: Optional[str] = None
    created_at: datetime
    
    class Config:
        from_attributes = True

class UserLogin(BaseModel):
    email: EmailStr
    password: str

# Event schemas
class EventBase(BaseModel):
    event_name: str
    event_date: date
    description: Optional[str] = None

class EventCreate(EventBase):
    pass

class EventResponse(EventBase):
    id: int
    event_code: Optional[str] = None
    owner_id: int
    created_at: datetime

    class Config:
        from_attributes = True

class EventWithDetails(EventResponse):
    owner: UserResponse
    guest_count: int = 0
    photo_count: int = 0

# Event Registration schemas
class EventRegistrationCreate(BaseModel):
    event_id: int

class EventRegistrationWithSelfie(BaseModel):
    event_code: str
    name: str
    email: str
    password: str

class EventRegistrationResponse(BaseModel):
    id: int
    user_id: int
    event_id: int
    role: str
    registered_at: datetime

    class Config:
        from_attributes = True

# Photo schemas
class PhotoBase(BaseModel):
    original_filename: Optional[str] = None

class PhotoResponse(PhotoBase):
    id: int
    event_id: int
    image_path: str
    uploaded_by: int
    uploaded_at: datetime
    file_size: Optional[int] = None
    mime_type: Optional[str] = None

    class Config:
        from_attributes = True

# Photo Face schemas
class PhotoFaceResponse(BaseModel):
    id: int
    photo_id: int
    face_index: int
    bounding_box: Optional[str] = None
    matched_user_id: Optional[int] = None
    created_at: datetime

    class Config:
        from_attributes = True

class PhotoWithFaces(PhotoResponse):
    faces: List["PhotoFaceResponse"] = []

class FaceProcessingRequest(BaseModel):
    photo_ids: List[int]

class FaceProcessingResponse(BaseModel):
    processed_photos: int
    total_faces_detected: int
    total_faces_matched: int
    message: str

# Authentication schemas
class Token(BaseModel):
    access_token: str
    token_type: str

class TokenData(BaseModel):
    email: Optional[str] = None

# Generic response schemas
class MessageResponse(BaseModel):
    message: str

class ErrorResponse(BaseModel):
    detail: str

# Update forward references
PhotoWithFaces.model_rebuild()
