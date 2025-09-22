from pydantic import BaseModel

#Validation and serialization schemas for User model
class UserBase(BaseModel):
    username: str
    email: str
    is_superuser: bool = False
    
class UserCreate(UserBase):
    password: str
    
class User(UserBase):
    id: int

    model_config = {
        "from_attributes": True
    }

#token schema for authentication
class Token(BaseModel):
    access_token: str
    token_type: str