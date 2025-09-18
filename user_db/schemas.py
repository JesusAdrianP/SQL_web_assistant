from pydantic import BaseModel

#Validation and serialization schemas for User model
class UserDbBase(BaseModel):
    db_name: str
    db_port: str
    db_user: str
    db_host: str
    db_schema: str
    user_id: int

class UserDbCreate(UserDbBase):
    pass

class UserDbRead(UserDbBase):
    id: int
    
    model_config = {
        "from_attributes": True
    }