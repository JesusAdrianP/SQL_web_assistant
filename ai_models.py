from transformers import AutoModelForSeq2SeqLM, AutoTokenizer
from google import genai

"""
Esta clase se usa para manejar el modelo extraído de huggin face: https://huggingface.co/gaussalgo/T5-LM-Large-text2sql-spider
"""
class HuggingFaceModel():
    """
    inicializa el path con la ruta de dónde se va a llamar el modelo
    inicializa el modelo y el tokenizador
    """
    def __init__(self):
        self.model_path = 'gaussalgo/T5-LM-Large-text2sql-spider'
        self.model = AutoModelForSeq2SeqLM.from_pretrained(self.model_path)
        self.tokenizer = AutoTokenizer.from_pretrained(self.model_path)

    """
    Obtener el path del modelo
    """
    def get_path(self):
        return self.model_path
    
    """
    Obtener el modelo
    """
    def get_model(self):
        return self.model
    
    """
    Obtener el tokenizador
    """
    def get_tokenizer(self):
        return self.tokenizer
    
"""
Clase para manejar el modelo de Gemini de Google
"""
class GoogleModel():
    """
    Inicializa el cliente de genai, con el api_key para poder consumir la api del modelo
    """
    def __init__(self):
        self.client = genai.Client(api_key="AIzaSyCGFus3om-YiZwLJdWlhrwEnNg0JHNk2mo")

    """
    Llama al modelo para hacer la consulta
    Parametros:
              schema: el esquema de la base de datos
              NL_query: consulta en lenguaje natural
    """
    def call_SQL_asistant(self,NL_query, schema):
        SQL_query = self.client.models.generate_content(
            model="gemini-2.0-flash",
            contents=f"based on this db schema {schema} give the SQL query to this natural language query:{NL_query}, just answer with de SQL query.",
            )
        return SQL_query.text