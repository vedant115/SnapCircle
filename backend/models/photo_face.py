from sqlalchemy import Column, Integer, ForeignKey, DateTime, String
from sqlalchemy.orm import relationship
from sqlalchemy.sql import func
from sqlalchemy.dialects.postgresql import JSON
from database.connection import Base


class PhotoFace(Base):
    __tablename__ = "photo_faces"
    
    id = Column(Integer, primary_key=True, index=True)
    photo_id = Column(Integer, ForeignKey("photos.id"), nullable=False)
    face_index = Column(Integer, nullable=False)  # Index of face in the photo (0, 1, 2, etc.)
    embedding = Column(JSON, nullable=False)  # Face embedding as JSON array
    bounding_box = Column(String(50), nullable=True)  # Face bounding box coordinates as string "(x1,y1),(x2,y2)"
    matched_user_id = Column(Integer, ForeignKey("users.id"), nullable=True)  # Matched user if found
    created_at = Column(DateTime(timezone=True), server_default=func.now())
    
    # Relationships
    photo = relationship("Photo", back_populates="faces")
    matched_user = relationship("User", foreign_keys=[matched_user_id])
    
    def __repr__(self):
        return f"<PhotoFace(id={self.id}, photo_id={self.photo_id}, face_index={self.face_index}, matched_user_id={self.matched_user_id})>"
