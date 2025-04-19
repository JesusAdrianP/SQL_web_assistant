from pydantic import BaseModel

class QueryInput(BaseModel):
    query: str
    
class LanguageInput(BaseModel):
    language: str