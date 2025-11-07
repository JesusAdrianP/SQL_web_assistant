# SQL_web_assistant

SQL Natural Assistant is a backend application that allows SQL queries to be made to databases using natural language.
The system interprets user questions with the help of artificial intelligence (AI) models and automatically translates them into SQL statements.

SQL Natural Assistant es una aplicación backend que permite realizar consultas SQL a bases de datos utilizando lenguaje natural. El sistema interpreta las preguntas del usuario con ayuda de modelos de inteligencia artificial (IA) y las traduce automáticamente en sentencias SQL.

Requires python versions from 3.9 to 3.10.11

Requiere versiones de python 3.9 a 3.10.11

For running locally, yo need to follow these steps:

1. After cloning the repository, go to the project folder and create the virtual environment with this command:  

 python -m venv venv

2. Once the virtual environment has been created, you must activate it with the following command:  

 on Windows:  
 source venv/scripts/activate  

 on Linux:  
 source venv/bin/activate  

3. Install the dependencies used in the project with the following command:

 pip install -r requirements.txt

4. Next, create a .env file in the project folder. The file should have the following structure:

GOOGLE_API_KEY="Your_Gemini_Api_Key"
DATABASE_URL=“your_postgresql_db_url”
SECRET_KEY="your_token_secret_key"
ALGORITHM=HS256
MASTER_KEY="your_crypto_master_key"
DEEPSEEK_API_KEY="Your_DeepSeek_Api_Key"

Note: Both the SECRET_KEY and MASTER_KEY can be generated with libraries such as Python secrets, or any other tool you prefer, and generate a 32-byte key.

5. Once the environment variables are configured, you must create the database migrations so that the tables and columns are created:  
  
  - To create the migrations: alembic revision --autogenerate -m “migrations details”  

  - To execute them and apply the changes: alembic upgrade head  

6. Finally, run the application with the following command:  

  uvicorn main:app --reload

Para ejecutar el proyecto localmente, debes seguir estos pasos:

1. Después de clonar el repositorio, ve a la carpeta del proyecto y crea el ambiente virtual con este comando:

 python -m venv venv

2. Una vez creado el ambiente virtual, debes activarlo con el siguiente comando:

 en windows:
 source venv/scripts/activate

 en linux:
 source venv/bin/activate

3. Instala las dependencias usadas en el proyecto con el siguiente comando:

 pip install -r requirements.txt

4. Luego, debes crear un archivo .env en la carpeta del poyecto, el archivo debe tener esta estructura:

GOOGLE_API_KEY="Your_Gemini_Api_Key"
DATABASE_URL="your_postgresql_db_url"
SECRET_KEY="your_token_secret_key"
ALGORITHM=HS256
MASTER_KEY="your_crypto_master_key"
DEEPSEEK_API_KEY="Your_DeepSeek_Api_Key"

Nota: Tanto la SECRET_KEY como la MASTER_KEY las puedes generar con librerías como secrets de python, o cualquier otra herramienta que se prefiera y generar una clave de 32 bytes

5. Una vez configuradas las variables de entorno, debes crear las migraciones de la base de datos para que se creen las tablas y columnas:  
  
  - Para crear las migraciones: alembic revision --autogenerate -m "migrations details"

  - Para ejecutarlas y aplicar los cambios: alembic upgrade head

6. Finalmente, ejecutar la aplicación con el siguiente comando: 

  uvicorn main:app --reload
