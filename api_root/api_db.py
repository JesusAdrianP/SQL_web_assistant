from sqlalchemy import create_engine
from sqlalchemy.orm import sessionmaker, declarative_base
import os
from dotenv import load_dotenv

load_dotenv()

#obtaining the database url from the .env file
DATABASE_URL = os.getenv("DATABASE_URL")

#creating the engine, session and base for the models of the api db
engine = create_engine(DATABASE_URL)
SessionLocal = sessionmaker(autocommit=False, autoflush=False, bind=engine)
Base = declarative_base()

# Dependency to get the db session
def get_db():
    db = SessionLocal()
    try:
        yield db
    finally:
        db.close()
   
# Function to create the tables in the database     
def create_tables():
    Base.metadata.create_all(bind=engine)