from api_root.api_db import Base
from sqlalchemy import Column, Integer, String, DECIMAL

#creating the AIModel model for the ai_model table in the database
class AIModel(Base):
    __tablename__ = "ai_model"
    
    id = Column(Integer, primary_key=True, index=True)
    model_name = Column(String, index=True)
    performance = Column(DECIMAL)