from fastapi import APIRouter, HTTPException, status, Depends
from typing import Annotated
from api_root.api_db import get_db_dependency
from .models import UserDB
from .schemas import UserDbCreate, UserDbUpdate
from fastapi.responses import JSONResponse
from users.auth import get_current_user
from .utils import CryptoService, test_user_db_connection
from asyncpg import connect as test_pg_connect

router = APIRouter(
    prefix="/user_dbs",
    tags=["user_dbs"]
)

#database and user dependencies
db_dependency = get_db_dependency()
user_dependency = Annotated[dict, Depends(get_current_user)]

#Endpoint for registering a new user database
@router.post("/register_db", status_code=status.HTTP_201_CREATED)
async def register_db(db: db_dependency, user: user_dependency, user_db: UserDbCreate):
    try:
        if user is None or user.get("id") is None:
            return JSONResponse(status_code=status.HTTP_401_UNAUTHORIZED, content={"error": "Authentication failed"})
        
        crypto = CryptoService()
        encrypted_password = crypto.encrypt(user_db.db_password)
        
        db_connection = await test_user_db_connection(user_db.db_user,user_db.db_name,user_db.db_host,user_db.db_port, encrypted_password)
        
        if db_connection.get("successful"):
            user_db_instance = UserDB(
                user_id=user.get("id"),
                db_name=user_db.db_name,
                db_port=user_db.db_port,
                db_user=user_db.db_user,
                db_host=user_db.db_host,
                db_schema=user_db.db_schema,
                encrypted_password=encrypted_password
            )
            db.add(user_db_instance)
            db.commit()
            db.refresh(user_db_instance)
            return {"message": "User database registered successfully", "db_name": user_db_instance.db_name}
        else:
            return JSONResponse(status_code=status.HTTP_400_BAD_REQUEST, content={"error":"database connection failed"})
    except Exception as e:
        db.rollback()
        return JSONResponse(status_code=status.HTTP_400_BAD_REQUEST, content={"error": f"{e}"})
    
#Endpoint to get all user databases for the authenticated user
@router.get("/user_dbs", status_code=status.HTTP_200_OK)
async def get_user_dbs(db: db_dependency, user: user_dependency):
    try:
        if user is None or user.get("id") is None:
            return JSONResponse(status_code=status.HTTP_401_UNAUTHORIZED, content={"error": "Authentication failed"})
        user_dbs = db.query(UserDB.id, UserDB.db_name, UserDB.created_at, UserDB.db_host, UserDB.db_port, UserDB.db_schema, UserDB.db_user).filter(UserDB.user_id == user.get("id")).all()
        return [{"id": db.id, "db_name": db.db_name, "db_user": db.db_user, "db_host": db.db_host,"db_port": db.db_port,"db_schema": db.db_schema,"created_at": db.created_at} for db in user_dbs]
    except Exception as e:
        return JSONResponse(status_code=status.HTTP_400_BAD_REQUEST, content={"error": f"{e}"})
    
#Endpoint to update a user database
@router.put("/update_db/{db_id}", status_code=status.HTTP_200_OK)
async def update_user_db(user_db_id: int, db: db_dependency, user: user_dependency, user_db: UserDbUpdate):
    try:
        if user is None or user.get("id") is None:
            return JSONResponse(status_code=status.HTTP_401_UNAUTHORIZED, content={"error": "Authentication failed"})
        user_db_instance = db.query(UserDB).filter(UserDB.id == user_db_id, UserDB.user_id == user.get("id")).first()
        if not user_db_instance:
            return JSONResponse(status_code=status.HTTP_404_NOT_FOUND, content={"error": "User database not found"})
        #updating only provided fields
        for field, value in user_db.model_dump(exclude_unset=True).items():
            setattr(user_db_instance, field, value)
            
        """ user_db_instance.db_name = user_db.db_name
        user_db_instance.db_port = user_db.db_port
        user_db_instance.db_user = user_db.db_user
        user_db_instance.db_host = user_db.db_host
        user_db_instance.db_schema = user_db.db_schema"""
        
        db.commit()
        db.refresh(user_db_instance)
        return {"message": "User database updated successfully", "db_name": user_db_instance.db_name}
    except Exception as e:
        db.rollback()
        return JSONResponse(status_code=status.HTTP_400_BAD_REQUEST, content={"error": f"{e}"})
    
#Endpoint to get all user databases for the authenticated user
@router.get("/user_dbs_names", status_code=status.HTTP_200_OK)
async def get_user_dbs_names(db: db_dependency, user: user_dependency):
    try:
        if user is None or user.get("id") is None:
            return JSONResponse(status_code=status.HTTP_401_UNAUTHORIZED, content={"error": "Authentication failed"})
        user_dbs = db.query(UserDB.id, UserDB.db_name).filter(UserDB.user_id == user.get("id")).all()
        return [{"id": db.id, "db_name": db.db_name} for db in user_dbs]
    except Exception as e:
        return JSONResponse(status_code=status.HTTP_400_BAD_REQUEST, content={"error": f"{e}"})
    
@router.get("/test_connection/{db_id}", status_code=status.HTTP_200_OK)
async def test_db_connection(db_id: int, db: db_dependency):
    try:
        crypto = CryptoService()
        user_db_instance = db.query(UserDB).filter(UserDB.id == db_id).first()
        db_password = crypto.decrypt(user_db_instance.encrypted_password)
        print("crypted password:", user_db_instance.encrypted_password)
        print("Decrypted password:", db_password)
        conn = await test_pg_connect(
            user=user_db_instance.db_user,
            password=db_password,
            database=user_db_instance.db_name,
            host=user_db_instance.db_host,
            port=user_db_instance.db_port,
            ssl="disable"
        )
        await conn.close()
        return {"message": "Connection successful"}
    except Exception as e:
        return JSONResponse(status_code=status.HTTP_400_BAD_REQUEST, content={"error": f"No se pudo conectar a la base de datos: {str(e)}"})