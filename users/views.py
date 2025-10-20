from fastapi import APIRouter, HTTPException, status, Depends
from typing import Annotated
from sqlalchemy.orm import Session
from api_root.api_db import get_db, SessionLocal, get_db_dependency
from .models import User
from passlib.context import CryptContext
from fastapi.security import OAuth2PasswordBearer, OAuth2PasswordRequestForm
from jose import JWTError, jwt
import os
from dotenv import load_dotenv
from .schemas import UserBase, UserCreate, Token, UserUpdate
from fastapi.responses import JSONResponse
from datetime import datetime, timedelta
from .auth import authenticate_user, create_access_token, get_current_user, hash_password

load_dotenv()

router = APIRouter(
    prefix="/users",
   tags=["users"]
)

user_dependency = Annotated[dict, Depends(get_current_user)]
db_dependency = get_db_dependency()

#Endpoint for user registration
@router.post("/create_user", status_code=status.HTTP_201_CREATED)
async def create_user(db: db_dependency, user: UserCreate):
    try:
        #print("Creating user...")
        user_instance = User(
            username=user.username,
            email=user.email,
            password=hash_password(user.password),
            is_superuser=user.is_superuser
        )
        #print("User instance created:", user_instance)
        db.add(user_instance)
        db.commit()
        db.refresh(user_instance)
        return JSONResponse(content={"message": "User created successfully"})
    except Exception as e:
        db.rollback()
        return JSONResponse(status_code=status.HTTP_400_BAD_REQUEST, content={"error": f"{e}"})

#Endpoint for user login and token generation
@router.post("/login", response_model=Token)
async def login(db: db_dependency, form_data: Annotated[OAuth2PasswordRequestForm, Depends()]):
    user = authenticate_user(db, form_data.username, form_data.password)
    if not user:
        raise HTTPException(status_code=status.HTTP_401_UNAUTHORIZED, detail="Invalid credentials")
    access_token = create_access_token(user.email, user.id, timedelta(minutes=30))
    return {"access_token": access_token, "token_type": "bearer"}

#Obtaining current user details
@router.get("/me")
async def get_user(db: db_dependency, user: user_dependency):
    try:
        if user is None or user.get("id") is None:
            raise HTTPException(status_code=status.HTTP_401_UNAUTHORIZED, detail="Authentication falied")
        user = db.query(User).filter(User.id == user.get("id")).first()
        user_info = {
            "id": user.id,
            "username": user.username,
            "email": user.email
        }
        return JSONResponse(status_code=status.HTTP_200_OK, content=user_info)
    except Exception as e:
        return JSONResponse(status_code=status.HTTP_400_BAD_REQUEST, content={"error": f"{e}"})
    
#update de user information
@router.put("/update_user")
async def update_user_info(db:db_dependency, user: user_dependency, updated_info:UserUpdate):
    try:
        if user is None or user.get("id") is None:
            return JSONResponse(status_code=status.HTTP_401_UNAUTHORIZED, content={"error": "Authentication failed"})
        user_instance = db.query(User).filter(User.id==user.get("id")).first()
        if updated_info.username is not None:
            user_instance.username = updated_info.username
        if updated_info.email is not None:
            user_instance.email = updated_info.email
        if updated_info.password is not None:
            user_instance.password = hash_password(updated_info.password)
        db.commit()
        db.refresh(user_instance)
        return JSONResponse(status_code=status.HTTP_200_OK, content={"message": "User information updated successfully"})
    except Exception as e:
        db.rollback()
        return JSONResponse(status_code=status.HTTP_400_BAD_REQUEST, content={"error": f"{e}"})