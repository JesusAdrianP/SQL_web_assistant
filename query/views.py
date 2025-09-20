from fastapi import APIRouter, HTTPException, status, Depends
from typing import Annotated
from api_root.api_db import get_db_dependency
from .models import Query
from .schemas import  QueryCreate
from fastapi.responses import JSONResponse
from users.auth import get_current_user

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
@router.get("/user_queries/{user_db_id}", status_code=status.HTTP_200_OK)
async def get_user_queries(db: db_dependency, user: user_dependency, user_db_id: int):
    try:
        if user is None or user.get("id") is None:
            return JSONResponse(status_code=status.HTTP_401_UNAUTHORIZED, content={"error": "Authentication failed"})
        queries = db.query(Query).filter(Query.user_id == user.get("id"), Query.user_db_id == user_db_id).all()
        return queries
    except Exception as e:
        return JSONResponse(status_code=status.HTTP_400_BAD_REQUEST, content={"error": f"{e}"})