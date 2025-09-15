from fastapi import APIRouter, HTTPException, status, Depends
from typing import Annotated
from sqlalchemy.orm import Session
from api_root.api_db import get_db, SessionLocal, db_dependency
from .models import User
from passlib.context import CryptContext
from fastapi.security import OAuth2PasswordBearer, OAuth2PasswordRequestForm
from jose import JWTError, jwt
import os
from dotenv import load_dotenv
from .schemas import UserBase, UserCreate, Token
from fastapi.responses import JSONResponse
from datetime import datetime, timedelta
from .auth import authenticate_user, create_access_token, get_current_user

load_dotenv()

router = APIRouter(
    prefix="/users",
   tags=["users"]
)

user_dependency = Annotated[dict, Depends(get_current_user)]

#Endpoint for user registration
@router.post("/create_user", status_code=status.HTTP_201_CREATED)
async def create_user(db: db_dependency, user: UserCreate):
    try:
        #print("Creating user...")
        user_instance = User(
            username=user.username,
            email=user.email,
            password=bycrypt_context.hash(user.password)
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
    if user is None:
        raise HTTPException(status_code=status.HTTP_401_UNAUTHORIZED, detail="Authentication falied")
    return {"email": user['email'], "id": user['id']}