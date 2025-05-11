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
                print("Exceso de tokens")
                tokenizer = self.get_tokenizer()
                model = self.get_model()
                print(tokenizer.model_max_length)
                model_inputs = tokenizer(input_text, return_tensors="pt", truncation=True)
                outputs = model.generate(**model_inputs, max_length=512)
                output_text = tokenizer.batch_decode(outputs, skip_special_tokens=True)
                return output_text[0]
            else:
                print("Bien de tokens")
                tokenizer = self.get_tokenizer()
                model = self.get_model()
                model_inputs = tokenizer(input_text, return_tensors="pt")
                outputs = model.generate(**model_inputs, max_length=512)
                output_text = tokenizer.batch_decode(outputs, skip_special_tokens=True)
                return output_text[0]
        except Exception as e:
            return f"""An error was ocurred: {e}"""
        
    def split_input_text(self, input_text):
        tokenizer = self.get_tokenizer()
        model = self.get_model()
        
        # 1. Tokenizamos el texto completo (sin agregar tokens especiales)
        tokens = tokenizer.encode(input_text, add_special_tokens=False)
        
        # 2. Tamaño máximo (ajustado a lo que el modelo puede manejar)
        max_input_tokens = tokenizer.model_max_length  # o el que sea válido para tu modelo
        
        # 3. Dividimos en chunks
        chunks = [tokens[i:i+max_input_tokens] for i in range(0, len(tokens), max_input_tokens)]
        
        # 4. Generamos resultados para cada chunk
        output_texts = []
        for chunk in chunks:
            # Volvemos a convertir a texto
            chunk_text = tokenizer.decode(chunk)
            # Tokenizamos el chunk como normalmente lo haces
            model_inputs = tokenizer(chunk_text, return_tensors="pt", truncation=True, max_length=max_input_tokens)
            
            # Generación
            outputs = model.generate(**model_inputs, max_length=512)
            
            # Decodificamos la salida
            output_text = tokenizer.batch_decode(outputs, skip_special_tokens=True)[0]
            
            output_texts.append(output_text)
            
            # 5. Unimos todo lo generado
            final_output = " ".join(output_texts)
            
        return final_output

    
"""
This class is responsible for managing the Google model.
"""
class GoogleModel():
    """
    Initializes the client of genai, with the api_key to be able to consume the model's api
    """
    def __init__(self):
        self.client = genai.Client(api_key=os.getenv('GOOGLE_API_KEY'))
        self.promt = """
        Your task is to generate a SQL query based on the following database schema and the provided natural language query.
        Database schema:
        {schema}
        
        Natural language query:
        {NL_query}
        
        You must respond only with the valid SQL query that answers the question. Make sure that the table and column names in your SQL query exactly match those provided in the schema. Check the column types in the schema to construct a syntactically correct SQL query. Do not include any additional explanation or text in your answer.
        Translated with DeepL.com (free version)
        """

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
                contents=self.promt.format(schema=schema, NL_query=NL_query),
            )
            return SQL_query.text
        except Exception as e:
            return f"""An error was ocurred: {e}"""
        
        
class SelectedModel():
    
    def __init__(self):
        self.model = 'T5'