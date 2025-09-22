from pydantic import BaseModel

# Validation and serialization schemas for AI Model
class AIModelBase(BaseModel):
    model_name: str
    performance: float
 
class AIModelCreate(AIModelBase):
    pass

class AIModelRead(AIModelBase):
    id: int

    model_config = {
        "from_attributes": True
    }
    
class AIModelUpdate(BaseModel):
    performance: float