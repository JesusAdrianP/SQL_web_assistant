from fastapi import APIRouter, HTTPException, status, Depends
from typing import Annotated
from api_root.api_db import get_db_dependency
from .models import AIModel
from .schemas import AIModelBase, AIModelCreate, AIModelRead, AIModelUpdate
from fastapi.responses import JSONResponse
from users.permissions import is_superuser
from users.auth import get_current_user

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
@router.put("/get_best_model/{aimodel_id}", status_code=status.HTTP_200_OK)
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