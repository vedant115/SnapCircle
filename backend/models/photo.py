from sqlalchemy import Column, Integer, String, DateTime, ForeignKey, Text
from sqlalchemy.orm import relationship
from sqlalchemy.sql import func
from database.connection import Base

class Photo(Base):
    __tablename__ = "photos"
    
    id = Column(Integer, primary_key=True, index=True)
    event_id = Column(Integer, ForeignKey("events.id"), nullable=False)
    image_path = Column(String(1000), nullable=False)  # Local path or S3 URL for cloud storage
    uploaded_by = Column(Integer, ForeignKey("users.id"), nullable=False)
    uploaded_at = Column(DateTime(timezone=True), server_default=func.now())
    
    # Optional metadata
    original_filename = Column(String(255), nullable=True)
    file_size = Column(Integer, nullable=True)  # Size in bytes
    mime_type = Column(String(100), nullable=True)
    
    # Relationships
    event = relationship("Event", back_populates="photos")
    uploader = relationship("User", back_populates="uploaded_photos")
    faces = relationship("PhotoFace", back_populates="photo", cascade="all, delete-orphan")
    
    def __repr__(self):
        return f"<Photo(id={self.id}, event_id={self.event_id}, path='{self.image_path}')>"
