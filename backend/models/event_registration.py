from sqlalchemy import Column, Integer, String, DateTime, ForeignKey, UniqueConstraint
from sqlalchemy.orm import relationship
from sqlalchemy.sql import func
from database.connection import Base

class EventRegistration(Base):
    __tablename__ = "event_registrations"
    
    id = Column(Integer, primary_key=True, index=True)
    user_id = Column(Integer, ForeignKey("users.id"), nullable=False)
    event_id = Column(Integer, ForeignKey("events.id"), nullable=False)
    role = Column(String(50), default="guest", nullable=False)  # guest, admin, etc.
    registered_at = Column(DateTime(timezone=True), server_default=func.now())
    
    # Relationships
    user = relationship("User", back_populates="event_registrations")
    event = relationship("Event", back_populates="registrations")
    
    # Ensure a user can only register once per event
    __table_args__ = (UniqueConstraint('user_id', 'event_id', name='unique_user_event'),)
    
    def __repr__(self):
        return f"<EventRegistration(user_id={self.user_id}, event_id={self.event_id}, role='{self.role}')>"
