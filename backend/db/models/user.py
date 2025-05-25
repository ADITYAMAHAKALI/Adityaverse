from sqlalchemy import Column, String, Boolean
from backend.db.session import Base
import uuid

def generate_uuid():
    return str(uuid.uuid4())

class User(Base):
    __tablename__ = "users"

    id = Column(String, primary_key=True, default=generate_uuid)
    email = Column(String, unique=True, index=True, nullable=False)
    hashed_password = Column(String, nullable=True)        # nullable when OAuth user
    is_active = Column(Boolean, default=True)
    role = Column(String, default="researcher")
    full_name = Column(String, nullable=True)
    avatar_url = Column(String, nullable=True)
