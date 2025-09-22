from api_root.api_db import Base
from sqlalchemy import Column, Integer, String, Boolean

#creating the User model for the users table in the database
class User(Base):
    __tablename__ = "users"
    
    id = Column(Integer, primary_key=True, index=True)
    username = Column(String, index=True)
    email = Column(String, unique=True, index=True)
    password = Column(String)
    is_superuser = Column(Boolean, default=False, index=True)