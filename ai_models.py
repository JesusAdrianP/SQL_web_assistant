from transformers import AutoModelForSeq2SeqLM, AutoTokenizer
from google import genai
import os

from dotenv import load_dotenv
load_dotenv()

"""
This class is responsible for managing the Hugging Face model. 
Extracted from: https://huggingface.co/gaussalgo/T5-LM-Large-text2sql-spider
"""
class HuggingFaceModel():
    """
    Initializes the path with the path of where the model is going to be called
    Initializes the model and the tokenizer
    """
    def __init__(self):
        self.model_path = 'gaussalgo/T5-LM-Large-text2sql-spider'
        self.model = AutoModelForSeq2SeqLM.from_pretrained(self.model_path)
        self.tokenizer = AutoTokenizer.from_pretrained(self.model_path)

    """
    Get the path model
    """
    def get_path(self):
        return self.model_path
    
    """
    Get the model
    """
    def get_model(self):
        return self.model
    
    """
    Get the tokenizer
    """
    def get_tokenizer(self):
        return self.tokenizer
    
    """
    This method count the tokens in a text data.
    Is used to count the number of tokens in the schema and input query that was passed to the model
    """
    def count_tokens(self, input_data):
        try:
            tokenizer = self.get_tokenizer()
            model_inputs = tokenizer.encode(input_data)
            return len(model_inputs)
        except Exception as e:
            return f"""An error was ocurred: {e}"""
    
    """
    Call the hugging face model to translate the nl query to SQL query
    """
    def call_translate_model(self, input_text):
        try:
            num_tokens = self.count_tokens(input_text)
            if num_tokens > 512:
                tokenizer = self.get_tokenizer()
                model = self.get_model()
                model_inputs = tokenizer(input_text, return_tensors="pt", truncation=True)
                outputs = model.generate(**model_inputs, max_length=512)
                output_text = tokenizer.batch_decode(outputs, skip_special_tokens=True)
                return output_text[0]
            else:
                tokenizer = self.get_tokenizer()
                model = self.get_model()
                model_inputs = tokenizer(input_text, return_tensors="pt")
                outputs = model.generate(**model_inputs, max_length=512)
                output_text = tokenizer.batch_decode(outputs, skip_special_tokens=True)
                return output_text[0]
        except Exception as e:
            return f"""An error was ocurred: {e}"""
    
"""
This class is responsible for managing the Google model.
"""
class GoogleModel():
    """
    Initializes the client of genai, with the api_key to be able to consume the model's api
    """
    def __init__(self):
        self.client = genai.Client(api_key=os.getenv('GOOGLE_API_KEY'))

    """
    Call the model to make the query
    Parameters:
        schema: the database schema
        NL_query: natural language query
    """
    def call_SQL_asistant(self,NL_query, schema):
        try:
            SQL_query = self.client.models.generate_content(
                model="gemini-2.0-flash",
                contents=f"based on this db schema {schema} give the SQL query to this natural language query:{NL_query}, just answer with de SQL query.",
            )
            return SQL_query.text
        except Exception as e:
            return f"""An error was ocurred: {e}"""