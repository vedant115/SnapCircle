from sqlalchemy import Column, Integer, String, DateTime, Text, ForeignKey, Date
from sqlalchemy.orm import relationship
from sqlalchemy.sql import func
from database.connection import Base
import string
import random

def generate_event_code():
    """Generate a 6-character random event code."""
    characters = string.ascii_uppercase + string.digits
    # Exclude confusing characters like 0, O, I, 1
    characters = characters.replace('0', '').replace('O', '').replace('I', '').replace('1', '')
    code = ''.join(random.choices(characters, k=6))
    print(f"🎲 Generated code: {code} from characters: {characters[:10]}...")
    return code

class Event(Base):
    __tablename__ = "events"

    id = Column(Integer, primary_key=True, index=True)
    event_code = Column(String(6), unique=True, index=True, nullable=False)
    event_name = Column(String(200), nullable=False)
    event_date = Column(Date, nullable=False)
    description = Column(Text, nullable=True)
    owner_id = Column(Integer, ForeignKey("users.id"), nullable=False)
    created_at = Column(DateTime(timezone=True), server_default=func.now())
    updated_at = Column(DateTime(timezone=True), onupdate=func.now())
    
    # Relationships
    owner = relationship("User", back_populates="owned_events")
    registrations = relationship("EventRegistration", back_populates="event", cascade="all, delete-orphan")
    photos = relationship("Photo", back_populates="event", cascade="all, delete-orphan")
    
    def __repr__(self):
        return f"<Event(id={self.id}, name='{self.event_name}', date='{self.event_date}')>"
