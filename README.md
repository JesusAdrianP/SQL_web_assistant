# SQL_web_assistant
Web application to perform sql queries in natural language to a connected database

Requires python versions from 3.9 to 3.10.11

For running locally, yo need to follow these steps:

1. Go to the project directory and create the virtual environment there:

 python -m venv venv

2. Then of the virtual env has been created, you need to activate it:

 on windows:
 source venv/scripts/activate

 on linux:
 source venv/bin/activate

3. Install the dependencies in the project directory:

 pip install -r requirements.txt

4. Then, you need to create a .env file in the project directory with the following structure:

 DB_NAME=db_name  
 DB_USER=db_user  
 DB_PASSWORD=db_password  
 DB_HOST=db_host  
 DB_PORT=db_port  
 GOOGLE_API_KEY=your_api_key

5. Finally, you can run the local server with the following instruction:

 uvicorn main:app --reload
