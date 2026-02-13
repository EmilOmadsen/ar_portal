from sqlalchemy import Column, Integer, String, Boolean, Text
from app.db.base import Base

class User(Base):
    __tablename__ = "users"

    id = Column(Integer, primary_key=True, index=True)
    email = Column(String, unique=True, index=True, nullable=False)
    name = Column(String, nullable=True)
    hashed_password = Column(String, nullable=True)  # Made nullable for Microsoft auth users
    role = Column(String, nullable=False)
    is_active = Column(Boolean, default=True)
    microsoft_token = Column(Text, nullable=True)  # Store Microsoft Graph API token
    microsoft_refresh_token = Column(Text, nullable=True)  # Store refresh token
