from api_root.api_db import Base
from sqlalchemy import Column, Integer, String, ForeignKey, Boolean

#creating the Query model for the query table in the database
class Query(Base):
    __tablename__ = "query"
    
    id = Column(Integer, primary_key=True, index=True)
    nl_query = Column(String)
    sql_query = Column(String)
    is_correct = Column(Boolean, nullable=True)
    user_id = Column(Integer, ForeignKey("users.id", ondelete="CASCADE"), index=True)
    ai_model_id = Column(Integer, ForeignKey("ai_model.id", ondelete="CASCADE"), index=True)
    user_db_id = Column(Integer, ForeignKey("user_db.id", ondelete="CASCADE"), index=True)