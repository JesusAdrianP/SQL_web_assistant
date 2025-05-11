from pydantic import BaseModel

class QueryInput(BaseModel):
    query: str
    
class LanguageInput(BaseModel):
    language: str

class TokensInput(BaseModel):
    query: str
    db_schema: str

class DBInput(BaseModel):
    db_name: str
    db_user: str
    db_password: str
    db_host: str