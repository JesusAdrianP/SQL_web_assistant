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