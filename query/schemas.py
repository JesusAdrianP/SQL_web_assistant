from pydantic import BaseModel

# Validation and serialization schemas for queries model
class QueryBase(BaseModel):
    nl_query: str
    sql_query: str
    is_correct: bool|None = None
    user_id: int
    ai_model_id: int
    user_db_id: int
    
class QueryCreate(QueryBase):
    pass

class QueryRead(QueryBase):
    id: int

    model_config = {
        "from_attributes": True
    }

class QueryUpdate(BaseModel):
    is_correct: bool|None = None