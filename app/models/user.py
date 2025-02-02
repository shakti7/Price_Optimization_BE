from sqlalchemy import Column, Integer, String, Boolean
from sqlalchemy.orm import relationship
from app.core.database import Base

class User(Base):
    __tablename__ = "users"

    id = Column(Integer, primary_key=True, index=True)
    first_name = Column(String, nullable=False)
    last_name = Column(String, nullable=False)
    email = Column(String, unique=True, index=True, nullable=False)
    hashed_password = Column(String, nullable=False)  # Store hashed passwords
    is_verified = Column(Boolean, default=False)  # Email verification status
    verification_token = Column(String, nullable=True)  # For email verification

    # Lazy load the relationship to avoid import issues
    products = relationship("Product", back_populates="user")

    