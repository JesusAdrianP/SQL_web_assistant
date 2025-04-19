from pydantic import BaseModel

class LanguageConfig():
    
    def __init__(self):
        self.language = "Ingles"
        
    def get_config_language(self):
        return self.language
    
    def set_language(self, new_language):
        self.language = new_language