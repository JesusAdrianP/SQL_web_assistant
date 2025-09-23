from api_root.api_db import Base
from sqlalchemy import Column, Integer, String, ForeignKey, DateTime, func

#creating the user_db model for the user_db table in the database
class UserDB(Base):
    __tablename__ = "user_db"
    
    id = Column(Integer, primary_key=True, index=True)
    db_name = Column(String, index=True)
    db_port = Column(String, index=True)
    db_user = Column(String, index=True)
    db_host = Column(String, index=True)
    db_schema = Column(String, index=True)
    user_id = Column(Integer, ForeignKey("users.id", ondelete="CASCADE"), index=True)
    created_at = Column(DateTime(timezone=True), server_default=func.now())