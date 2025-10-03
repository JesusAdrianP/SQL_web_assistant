from fastapi import APIRouter, HTTPException, status, Depends
from fastapi import Query as FastAPIQuery
from typing import Annotated, Optional
from api_root.api_db import get_db_dependency
from .models import AIModel
from .schemas import AIModelBase, AIModelCreate, AIModelRead, AIModelUpdate
from fastapi.responses import JSONResponse
from users.permissions import is_superuser
from users.auth import get_current_user
from query.models import Query
from sqlalchemy import func, case
from ai_model.models import AIModel
from .utils import calculate_percentage

router = APIRouter(
    prefix="/ai_models",
    tags=["ai_models"]
)

#database and user dependencies
db_dependency = get_db_dependency()
superuser_dependency = Annotated[dict, Depends(is_superuser)]
user_dependency = Annotated[dict, Depends(get_current_user)]

#Endpoint for registering a new AI model (superuser only)
@router.post("/register_model", status_code=status.HTTP_201_CREATED)
async def register_model(db: db_dependency, model: AIModelCreate, user: superuser_dependency):
    try:
        if user is None:
            raise HTTPException(status_code=status.HTTP_401_UNAUTHORIZED, detail="Invalid credentials")
        elif user.get("is_superuser", False) == False or user.get("is_superuser") is None:
            raise HTTPException(status_code=status.HTTP_403_FORBIDDEN, detail="Not enough permissions")
        model_instance = AIModel(
            model_name=model.model_name
        )
        db.add(model_instance)
        db.commit()
        db.refresh(model_instance)
        return JSONResponse(content={"message": "Model registered successfully"})
    except Exception as e:
        db.rollback()
        return JSONResponse(status_code=status.HTTP_400_BAD_REQUEST, content={"error": f"{e}"})

#Endpoint for retrieving all available AI models
@router.get("/get_models", status_code=status.HTTP_200_OK)
async def get_available_models(db: db_dependency, user: user_dependency):
    try:
        if user is None:
            return JSONResponse(status_code=status.HTTP_401_UNAUTHORIZED, content={"error": "Authentication failed"})
        models = db.query(AIModel).all()
        return models
    except Exception as e:
        return JSONResponse(status_code=status.HTTP_400_BAD_REQUEST, content={"error": f"{e}"})
    
#Endpoint for update AI model performance
@router.put("/update_model_performance/{aimodel_id}", status_code=status.HTTP_200_OK)
async def update_model_performance(db: db_dependency, model: AIModelUpdate, user: user_dependency, model_id: int):
    try:
        if user is None:
            return JSONResponse(status_code=status.HTTP_401_UNAUTHORIZED, content={"error": "Authentication failed"})
        model_instance = db.query(AIModel).filter(AIModel.id == model_id).first()
        if model_instance is None:
            return JSONResponse(status_code=status.HTTP_404_NOT_FOUND, content={"error": "Model not found"})
        
        #update model performance
        model_instance.performance = model.performance
        db.commit()
        db.refresh(model_instance)
        
        return {"message": "Model updated successfully", "model": model_instance.model_name}
    except Exception as e:
        db.rollback()
        return JSONResponse(status_code=status.HTTP_400_BAD_REQUEST, content={"error": f"{e}"})
    
@router.get("/calculate_model_performance")
async def calculate_model_perfomance(db: db_dependency, user: user_dependency, user_db_id: Optional[int] = FastAPIQuery(None)):
    try:
        if user is None or user.get("id") is None:
            return JSONResponse(status_code=status.HTTP_401_UNAUTHORIZED, content={"error": "Authentication failed"})
        if user_db_id is None:
            query_results_by_model = db.query(
                AIModel.id,
                AIModel.model_name,
                func.count(case((Query.is_correct == True,1))).label("correct_queries"),
                func.count(case((Query.is_correct!=True,1))).label("incorrect_queries"),
                func.count(Query.ai_model_id).label("total_queries_by_model")
                ).join(AIModel, Query.ai_model_id==AIModel.id).group_by(AIModel.id, AIModel.model_name).filter(Query.user_id == user.get("id"))
            executed_queries = db.query(Query).filter(Query.user_id == user.get("id"))
        else:
            query_results_by_model = db.query(
                AIModel.id,
                AIModel.model_name,
                func.count(case((Query.is_correct == True,1))).label("correct_queries"),
                func.count(case((Query.is_correct!=True,1))).label("incorrect_queries"),
                func.count(Query.ai_model_id).label("total_queries_by_model")
                ).join(AIModel, Query.ai_model_id==AIModel.id).group_by(AIModel.id, AIModel.model_name).filter(Query.user_id == user.get("id"), Query.user_db_id==user_db_id)
            executed_queries = db.query(Query).filter(Query.user_id == user.get("id"), Query.user_db_id== user_db_id)
        total_queries = executed_queries.count()
        performance_stats = [
            {
                "id_model": id_model,
                "model_name": model_name,
                "correct_quantity": correct_quantity,
                "incorrect_quantity": incorrect_quantity,
                "usage_percentage": calculate_percentage(total_queries, total_queries_by_model)
            }
            for id_model, model_name, correct_quantity, incorrect_quantity, total_queries_by_model in query_results_by_model
        ]
        return JSONResponse(status_code=status.HTTP_200_OK, content={"performance_stats":performance_stats})
    except Exception as e:
        return JSONResponse(status_code=status.HTTP_400_BAD_REQUEST, content={"error": f"{e}"})