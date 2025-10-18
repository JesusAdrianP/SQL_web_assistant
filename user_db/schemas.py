from pydantic import BaseModel
from typing import Optional

#Validation and serialization schemas for User model
class UserDbBase(BaseModel):
    db_name: str
    db_port: str
    db_user: str
    db_host: str
    db_schema: str

class UserDbCreate(UserDbBase):
    db_password: str

class UserDbRead(UserDbBase):
    id: int
    
    model_config = {
        "from_attributes": True
    }

#Schema for updating user database details (partial updates allowed)
class UserDbUpdate(BaseModel):
    db_name: Optional[str] = None
    db_port: Optional[str] = None
    db_user: Optional[str] = None
    db_host: Optional[str] = None
    db_schema: Optional[str] = None