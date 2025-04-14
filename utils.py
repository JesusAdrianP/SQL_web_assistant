from db_connection import DBConnection
from transformers import AutoModelForSeq2SeqLM, AutoTokenizer
from inputs import QueryInput
import re
import os
from dotenv import load_dotenv

load_dotenv()

# Obtener las columnas de las tablas en el esquema 'public'
def get_db_columns_schema():
    db = DBConnection()
    db.generate_db_connection()
    cursor = db.get_db_cursor()
    cursor.execute(f"""
        SELECT table_name, column_name, data_type 
        FROM information_schema.columns 
        WHERE table_schema = '{os.getenv('DB_SCHEMA')}'
    """)
    columnas = cursor.fetchall()
    #print("estas son las tablas: ",columnas)
    db.quit_db_connection()
    return columnas


# Obtener claves primarias
def get_db_pk_schema():
    db = DBConnection()
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

# Obtener claves foráneas
def get_db_fk_schema():
    db = DBConnection()
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


#Organiza el esquema de la bd en el formato que el modelo puede procesar
def parse_schema():
    foreign_keys = {}
    fk_info = get_db_fk_schema()
    #print("info",fk_info)
    for table, column, column_type, foreign_table, foreign_column in fk_info:
        foreign_keys.setdefault(table, []).append(f'foreign_key: "{column}" {column_type} from "{foreign_table}" "{foreign_column}"')

    tables = {}
    columnas = get_db_columns_schema()
    for table, column, col_type in columnas:
        tables.setdefault(table, []).append(f'"{column}" {col_type}') 

    schema_parts = []
    primary_keys = get_db_pk_schema()
    for table, columns in tables.items():
        schema_line = f'"{table}" ' + " , ".join(columns)
        if table in primary_keys:
            schema_line += f' , primary key: "{primary_keys[table]}"'
        if table in foreign_keys:
            schema_line += " , " + " , ".join(foreign_keys[table])
        schema_parts.append(schema_line)

    schema = ' [SEP] '.join(schema_parts)

    return schema

""""
def translate_to_sql(input_data: QueryInput):
    nl_query = input_data.query
    input_text = " ".join(["Question: ",nl_query, "Schema:", db_schema])
    model_inputs = tokenizer(input_text, return_tensors="pt")
    outputs = model.generate(**model_inputs, max_length=512)
    output_text = tokenizer.batch_decode(outputs, skip_special_tokens=True)
    return output_text[0]
"""


def parse_gemini_response(response_to_parse):
    parsed_response = re.search(r'```sql\n(.*?)\n```', response_to_parse, re.DOTALL)
    parsed_response = parsed_response.group(1)
    parsed_response = parsed_response.replace("\n", " ").strip()
    return parsed_response