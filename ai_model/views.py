from fastapi import APIRouter, HTTPException, status, Depends
from typing import Annotated
from api_root.api_db import get_db_dependency
from models import AIModel
from schemas import AIModelBase, AIModelCreate, AIModelRead
from fastapi.responses import JSONResponse

router = APIRouter(
    prefix="/ai_models",
    tags=["ai_models"]
)

db_dependency = get_db_dependency()

@router.post("/register_model", status_code=status.HTTP_201_CREATED)
async def register_model(db: db_dependency, model: AIModelCreate):
    try:
        model_instance = AIModel(**model.dict())
        db.add(model_instance)
        db.commit()
        db.refresh(model_instance)
        return JSONResponse(content={"message": "Model registered successfully"})
    except Exception as e:
        db.rollback()
        return JSONResponse(status_code=status.HTTP_400_BAD_REQUEST, content={"error": f"{e}"})