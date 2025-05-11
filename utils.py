from db_connection import DBConnection, DBConnectionAPI
from transformers import AutoModelForSeq2SeqLM, AutoTokenizer
from inputs import QueryInput
import re
import os
from dotenv import load_dotenv
from ai_models import HuggingFaceModel

load_dotenv()

db = DBConnectionAPI(db_host=None, db_name=None, db_password=None, db_user=None)

# This method obtain the tables of the database schema
def get_db_columns_schema(db_host, db_name, db_password, db_user):
    try:

        db = DBConnectionAPI(db_host=db_host, db_name=db_name, db_password=db_password, db_user=db_user)
        db.generate_db_connection()
        cursor = db.get_db_cursor()
        cursor.execute(f"""
           SELECT table_name, column_name, data_type 
           FROM information_schema.columns 
           WHERE table_schema = '{os.getenv('DB_SCHEMA')}'
        """)
        columns = cursor.fetchall()
        #print("estas son las tablas: ",columnas)
        db.quit_db_connection()
        return columns
    except Exception as e:
        return f"""An error was ocurred with the database: {e}"""


# This method obtain the primary keys of the database
def get_db_pk_schema(db_host, db_name, db_password, db_user):
    try:
        db = DBConnectionAPI(db_host=db_host, db_name=db_name, db_password=db_password, db_user=db_user)
        db.generate_db_connection()
        cursor = db.get_db_cursor()
        cursor.execute(f"""
        SELECT tc.table_name, kcu.column_name
        FROM information_schema.table_constraints AS tc
        JOIN information_schema.key_column_usage AS kcu
        ON tc.constraint_name = kcu.constraint_name
        WHERE tc.constraint_type = 'PRIMARY KEY' AND tc.table_schema = '{os.getenv('DB_SCHEMA')}'
        """)
        pk_info = cursor.fetchall()
        primary_keys = {table: column for table, column in pk_info}
        #print("Estas son las claves primarias: ", len(primary_keys))
        db.quit_db_connection()
        return primary_keys
    except Exception as e:
        return f"""An error was ocurred with the database: {e}"""

# This method obtain the foreign keys of the database
def get_db_fk_schema(db_host, db_name, db_password, db_user):
    try:
        db = DBConnectionAPI(db_host=db_host, db_name=db_name, db_password=db_password, db_user=db_user)
        db.generate_db_connection()
        cursor = db.get_db_cursor()
        cursor.execute(f"""
        SELECT tc.table_name, kcu.column_name, fk_column.data_type AS foreign_column_data_type, ccu.table_name AS foreign_table, ccu.column_name AS foreign_column
        FROM information_schema.table_constraints AS tc
        JOIN information_schema.key_column_usage AS kcu
        ON tc.constraint_name = kcu.constraint_name
        JOIN information_schema.constraint_column_usage AS ccu
        ON ccu.constraint_name = tc.constraint_name
        JOIN information_schema.columns AS fk_column
        ON fk_column.table_name = ccu.table_name AND fk_column.column_name = ccu.column_name
        WHERE tc.constraint_type = 'FOREIGN KEY' AND tc.table_schema = '{os.getenv('DB_SCHEMA')}'
        """)
        fk_info = cursor.fetchall()
        fk_info = list(set(fk_info))  # Eliminar duplicados
        print("Estas son las nuevas claves foraneas: ", len(fk_info))
        #print("Estas son las nuevas claves foraneas: ", fk_info)
        db.quit_db_connection()
        return fk_info
    except Exception as e:
        return f"""An error was ocurred with the database: {e}"""

#This method organize the database schema in a specific format, for the model processing
#Format: table_name column1_name column1_type column2_name column2_type ... foreign_key: FK_name FK_type from table_name column_name primary key: column_name [SEP]
#        table_name2 ...
def parse_schema(db_host, db_name, db_password, db_user):
    foreign_keys = {}
    try:
        fk_info = get_db_fk_schema(db_host, db_name, db_password, db_user)
        for table, column, column_type, foreign_table, foreign_column in fk_info:
            foreign_keys.setdefault(table, []).append(f'foreign_key: "{column}" {column_type} from "{foreign_table}" "{foreign_column}"')

        tables = {}
        columnas = get_db_columns_schema(db_host, db_name, db_password, db_user)
        for table, column, col_type in columnas:
            tables.setdefault(table, []).append(f'"{column}" {col_type}') 

        schema_parts = []
        primary_keys = get_db_pk_schema(db_host, db_name, db_password, db_user)
        for table, columns in tables.items():
            schema_line = f'"{table}" ' + " , ".join(columns)
            if table in primary_keys:
                schema_line += f' , primary key: "{primary_keys[table]}"'
            if table in foreign_keys:
                schema_line += " , " + " , ".join(foreign_keys[table])
            schema_parts.append(schema_line)

        schema = ' [SEP] '.join(schema_parts)
        
        #print("schema: ", schema)
        return schema
    except Exception as e:
        fk_info = None
        return fk_info

""""
def translate_to_sql(input_data: QueryInput):
    nl_query = input_data.query
    input_text = " ".join(["Question: ",nl_query, "Schema:", db_schema])
    model_inputs = tokenizer(input_text, return_tensors="pt")
    outputs = model.generate(**model_inputs, max_length=512)
    output_text = tokenizer.batch_decode(outputs, skip_special_tokens=True)
    return output_text[0]
"""

"""
This method parse the gemini response eliminating special characters, extra whithespaces and line breaks.
Using RE library to implement regular expressions
"""
def parse_gemini_response(response_to_parse):
    parsed_response = re.search(r'```sql\n(.*?)\n```', response_to_parse, re.DOTALL)
    parsed_response = parsed_response.group(1)
    parsed_response = parsed_response.replace("\n", " ").strip()
    return parsed_response

def search_column_in_schema():
    return True

def count_tokens_in_string(nl_query, db_schema):
    """
    Count the number of tokens in a string using the tokenizer.
    """
    init_model = HuggingFaceModel()
    input_text = " ".join(["Question: ",nl_query, "Schema:", db_schema])
    tokens_input = init_model.count_tokens(input_text)
    return tokens_input


def identify_tables_in_query(query):
    """
    Identify the tables in the query using regex.
    """
    pattern = r'FROM\s+([a-zA-Z0-9_]+)'
    matches = re.findall(pattern, query, re.IGNORECASE)
    return matches

def identify_columns_in_query(query):
    """
    Identify the columns in the query using regex.
    """
    pattern = r'SELECT\s+([a-zA-Z0-9_()*.,\s]+)\s+FROM'
    matches = re.findall(pattern, query, re.IGNORECASE)
    return matches[0].split(",") if matches else []