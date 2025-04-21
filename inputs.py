from pydantic import BaseModel

class QueryInput(BaseModel):
    query: str
    
class LanguageInput(BaseModel):
    language: str

class TokensInput(BaseModel):
    query: str
    db_schema: str