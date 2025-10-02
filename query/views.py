from fastapi import APIRouter, HTTPException, status, Depends
from fastapi import Query as FastAPIQuery
from typing import Annotated, Optional
from api_root.api_db import get_db_dependency
from .models import Query
from .schemas import  QueryCreate, QueryUpdate
from fastapi.responses import JSONResponse
from users.auth import get_current_user
from users.models import User
from ai_model.models import AIModel
from user_db.models import UserDB
from user_db.utils import connect_to_user_db
from inputs import QueryInput
from user_db.utils import CryptoService, parse_schema
from user_db.models import UserDB
from utils import identify_columns_in_query
from .utils import call_gemini_model, translate_to_sql, execute_generated_sql_query, call_deepseek_model

router = APIRouter(
    prefix="/queries",
    tags=["queries"]
)

#database and user dependencies
db_dependency = get_db_dependency()
user_dependency = Annotated[dict, Depends(get_current_user)]

#Endpoint for creating a new query
@router.post("/create_query", status_code=status.HTTP_201_CREATED)
async def create_query(db: db_dependency, user: user_dependency, query: QueryCreate):
    try:
        if user is None or user.get("id") is None:
            return JSONResponse(status_code=status.HTTP_401_UNAUTHORIZED, content={"error": "Authentication failed"})
        query_instance = Query(
            nl_query=query.nl_query,
            sql_query=query.sql_query,
            is_correct=query.is_correct,
            user_id=user.get("id"),
            ai_model_id=query.ai_model_id,
            user_db_id=query.user_db_id
        )
        db.add(query_instance)
        db.commit()
        db.refresh(query_instance)
        return {"message": "Query created successfully", "query_id": query_instance.id}
    except Exception as e:
        db.rollback()
        return JSONResponse(status_code=status.HTTP_400_BAD_REQUEST, content={"error": f"{e}"})
    
#Endpoint to get specific query from user
@router.get("/user_queries/{query_id}", status_code=status.HTTP_200_OK)
async def get_user_query(db:db_dependency, user:user_dependency, query_id: int):
    try:
        if user is None or user.get("id") is None:
            return JSONResponse(status_code=status.HTTP_401_UNAUTHORIZED, content={"error":"Authentication failed"})
        
        if query_id is None:
            return JSONResponse(status_code=status.HTTP_400_BAD_REQUEST, content={"error":"Invalid query id"})
        
        query = db.query(Query, AIModel.model_name, UserDB.db_name).join(AIModel, AIModel.id == Query.ai_model_id).join(UserDB, UserDB.id == Query.user_db_id).filter(Query.user_id == user.get("id"), Query.id ==query_id).first()
        user_db = db.query(UserDB).filter(UserDB.id == query[0].user_db_id).first()
        crypto_service = CryptoService()
        query_result = await execute_generated_sql_query(query[0].sql_query,user_db,crypto_service)
        
        response = {
            "id": query[0].id,
            "nl_query": query[0].nl_query,
            "sql_query": query[0].sql_query,
            "user_id": query[0].user_id,
            "is_correct": query[0].is_correct,
            "ai_model_id": query[0].ai_model_id,
            "ai_model_name": query[1],
            "user_db_id": query[0].user_db_id,
            "user_db_name": query[2],
            "query_result": query_result
        }
        return response
    except Exception as e:
        return JSONResponse(status_code=status.HTTP_400_BAD_REQUEST, content={"error": f"{e}"})       
        
    
#Endpoint to get all queries for the authenticated user and specific user database
@router.get("/user_queries", status_code=status.HTTP_200_OK)
async def get_user_queries(db: db_dependency, user: user_dependency, user_db_id: Optional[int] = FastAPIQuery(None)):
    try:
        if user is None or user.get("id") is None:
            return JSONResponse(status_code=status.HTTP_401_UNAUTHORIZED, content={"error": "Authentication failed"})
        
        if user_db_id is None:
            queries = db.query(Query, AIModel.model_name, UserDB.db_name).join(AIModel, AIModel.id == Query.ai_model_id).join(UserDB, UserDB.id == Query.user_db_id).filter(Query.user_id == user.get("id")).all()
        else:
            queries = db.query(Query, AIModel.model_name, UserDB.db_name).join(AIModel, AIModel.id == Query.ai_model_id).join(UserDB, UserDB.id == Query.user_db_id).filter(Query.user_id == user.get("id"), Query.user_db_id == user_db_id).all()
        response = []
        for query, model, user_db in queries:
            response.append({
                "id": query.id,
                "nl_query": query.nl_query,
                "sql_query": query.sql_query,
                "user_id": query.user_id,
                "is_correct": query.is_correct,
                "ai_model_id": query.ai_model_id,
                "ai_model_name": model,
                "user_db_id": query.user_db_id,
                "user_db_name": user_db,
            })
        return response
    except Exception as e:
        return JSONResponse(status_code=status.HTTP_400_BAD_REQUEST, content={"error": f"{e}"})

#Endpoint to update the correctness of a specific query
@router.put("/update_query/{query_id}", status_code=status.HTTP_200_OK)
async def update_query(db: db_dependency, user: user_dependency, query_id: int, query: QueryUpdate):
    try:
        if user is None or user.get("id") is None:
            return JSONResponse(status_code=status.HTTP_401_UNAUTHORIZED, content={"error": "Authentication failed"})
        query_instance = db.query(Query).filter(Query.id == query_id, Query.user_id == user.get("id")).first()
        if not query_instance:
            return JSONResponse(status_code=status.HTTP_404_NOT_FOUND, content={"error": "Query not found"})
        if query.is_correct is not None:
            query_instance.is_correct = query.is_correct
        db.commit()
        db.refresh(query_instance)
        return {"message": "Query updated successfully"}
    except Exception as e:
        db.rollback()
        return JSONResponse(status_code=status.HTTP_400_BAD_REQUEST, content={"error": f"{e}"})
    
    
"""
This endpoint execute the SQL query generated by the Google Gemini model
Params: input_data = Natural language query
Return: Json with the results of the SQL query generated by Google Gemini model from the natural language query
        {query_result: [(result_1_column_1_value, ..., result_1_column_n_value), ..., (result_n_column_1_value, ..., result_n_column_n_value)]}
"""
@router.post("/gemini/execute_query/")
async def execute_gemini_query(db:db_dependency, input_data:QueryCreate, user:user_dependency):
    try:
        if user is None or user.get("id") is None:
            return JSONResponse(status_code=status.HTTP_401_UNAUTHORIZED, content={"error": "Authentication failed"})
        crypto_service = CryptoService()
        user_db_link = db.query(UserDB).filter(UserDB.id == input_data.user_db_id).first()
        parsed_schema = await parse_schema(user_db_link=user_db_link, crypto_service=crypto_service)
        sql_query = await call_gemini_model(nl_query=input_data.nl_query, db_schema=parsed_schema)
        if sql_query.get("sql_query"):
            query_instance = Query(
                nl_query=input_data.nl_query,
                sql_query=sql_query.get("sql_query"),
                is_correct=input_data.is_correct,
                user_id=user.get("id"),
                ai_model_id=input_data.ai_model_id,
                user_db_id=input_data.user_db_id
            )
            db.add(query_instance)
            db.commit()
            db.refresh(query_instance)
            try:
                user_db = await connect_to_user_db(user_db_link, crypto_service)
                cursor = user_db.cursor()
                cursor.execute(f"""
                           {sql_query.get('sql_query')}
                           """)
                query_result = cursor.fetchall()
                cursor.close()
                user_db.close()
                return JSONResponse(status_code=status.HTTP_200_OK,content={"query_result": query_result, "columns": identify_columns_in_query(sql_query.get('sql_query'))})
            except Exception as e:
                return JSONResponse(status_code=status.HTTP_400_BAD_REQUEST, content={"error": f"An error was occurred with database connection or sql query executed: {e}"})
        else:
            JSONResponse(status_code=status.HTTP_400_BAD_REQUEST, content={"error":"The model is not responding"})
    except Exception as e:
        return JSONResponse(status_code=status.HTTP_400_BAD_REQUEST, content={"error":f"An error was ocurred: {e}"})
    
    
"""
This endpoint execute the SQL query generated by the Huggin Face model
Params: input_data = Natural language query
Return: Json with the results of the SQL query generated by Huggin Face model from the natural language query
        {query_result: [(result_1_column_1_value, ..., result_1_column_n_value), ..., (result_n_column_1_value, ..., result_n_column_n_value)]}
"""
@router.post("/t5/execute_query/")
async def execute_query(db:db_dependency, input_data: QueryCreate, user:user_dependency):
    try:
        if user is None or user.get("id") is None:
            return JSONResponse(status_code=status.HTTP_401_UNAUTHORIZED, content={"error": "Authentication failed"})
        crypto_service = CryptoService()
        user_db_link = db.query(UserDB).filter(UserDB.id == input_data.user_db_id).first()
        parsed_schema = await parse_schema(user_db_link=user_db_link, crypto_service=crypto_service)
        sql_query = await translate_to_sql(nl_query=input_data.nl_query, db_schema=parsed_schema)
        print(sql_query)
        if sql_query.get("sql_query"):
            query_instance = Query(
                nl_query=input_data.nl_query,
                sql_query = sql_query.get("sql_query"),
                is_correct = input_data.is_correct,
                user_id = user.get("id"),
                ai_model_id = input_data.ai_model_id,
                user_db_id = input_data.user_db_id
            )
            db.add(query_instance)
            db.commit()
            db.refresh(query_instance)
            try:
                user_db = await connect_to_user_db(user_db_link,crypto_service)
                cursor = user_db.cursor()
                cursor.execute(f"""
                               {sql_query.get('sql_query')}
                               """)
                query_result = cursor.fetchall()
                cursor.close()
                user_db.close()
                return JSONResponse(status_code=status.HTTP_200_OK,content={"query_result": query_result, "columns": identify_columns_in_query(sql_query.get('sql_query'))})
            except Exception as e:
                return JSONResponse(status_code=status.HTTP_400_BAD_REQUEST, content={"error": f"An error was occurred with database connection or sql query executed: {e}"})
        else:
            return JSONResponse(status_code=status.HTTP_400_BAD_REQUEST, content={"error":"The model is not responding"})
    except Exception as e:
        raise HTTPException(status_code=status.HTTP_400_BAD_REQUEST, detail=f"An error was ocurred: {e}")
    

@router.post("/deepseek/translate_query")
async def ds_translate_query(db:db_dependency, input_data:QueryInput, user:user_dependency):
    try:
        if user is None or user.get("id") is None:
            return JSONResponse(status_code=status.HTTP_401_UNAUTHORIZED, content={"error": "Authentication failed"})
        crypto_service = CryptoService()
        user_db_link = db.query(UserDB).filter(UserDB.id==input_data.user_db_id).first()
        parsed_schema = await parse_schema(user_db_link=user_db_link, crypto_service=crypto_service)
        sql_query = await call_deepseek_model(nl_query=input_data.query, db_schema=parsed_schema)
        print("sql_query: ", sql_query)
        return JSONResponse(status_code=status.HTTP_200_OK, content={"sql_query": sql_query.get('sql_query')})
    except Exception as e:
        return JSONResponse(status_code=status.HTTP_400_BAD_REQUEST, content={"error": f"{e}"})