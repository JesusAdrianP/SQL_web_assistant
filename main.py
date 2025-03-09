from fastapi import FastAPI
from utils import parse_schema #,translate_to_sql
from db_connection import DBConnection
from inputs import QueryInput
from ai_models import HuggingFaceModel, GoogleModel

app = FastAPI()

#db_schema = """
#   "stadium" "Stadium_ID" int , "Location" text , "Name" text , "Capacity" int , "Highest" int , "Lowest" int , "Average" int , foreign_key:  primary key: "Stadium_ID" [SEP] "singer" "Singer_ID" int , "Name" text , "Country" text , "Song_Name" text , "Song_release_year" text , "Age" int , "Is_male" bool , foreign_key:  primary key: "Singer_ID" [SEP] "concert" "concert_ID" int , "concert_Name" text , "Theme" text , "Year" text , foreign_key: "Stadium_ID" text from "stadium" "Stadium_ID" , primary key: "concert_ID" [SEP] "singer_in_concert"  foreign_key: "concert_ID" int from "concert" "concert_ID" , "Singer_ID" text from "singer" "Singer_ID" , primary key: "concert_ID" "Singer_ID"
#"""

db_schema = parse_schema()

@app.get("/")
def read_root():
    return {"Hello": "I am your sql assistant"}

@app.post("/translate/")
async def translate_to_sql(input_data: QueryInput):
    nl_query = input_data.query
    input_text = " ".join(["Question: ",nl_query, "Schema:", db_schema])
    init_model = HuggingFaceModel()
    tokenizer = init_model.get_tokenizer()
    model = init_model.get_model()
    model_inputs = tokenizer(input_text, return_tensors="pt")
    outputs = model.generate(**model_inputs, max_length=512)
    output_text = tokenizer.batch_decode(outputs, skip_special_tokens=True)
    return {"sql_query": output_text[0]}
    

@app.post("/execute_query/")
async def execute_query(input_data: QueryInput):
    sql_query = await translate_to_sql(input_data)
    db = DBConnection()
    db.generate_db_connection()
    cursor = db.get_db_cursor()
    cursor.execute(f"""
        {sql_query.get('sql_query')}
    """)
    query_result = cursor.fetchall()
    db.quit_db_connection()
    return {"query_result": query_result}