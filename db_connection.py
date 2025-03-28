# psycopg2 para obtener el esquema de la bd de postgres, para posteriomente proporcionarle esta información al modelo a utilizar
import psycopg2
import os

from dotenv import load_dotenv
load_dotenv()

class DBConnection:
    
    """
      Initializes the objects that will interact with the db. 
      First the connection and the cursor in none, then they will be change their values when the db is connected
    """
    def __init__(self):
        self.conn = None
        self.cursor = None

    """
      Generate the db connection with the credentials provided in the .env file
    """
    def generate_db_connection(self):
        #obtaining the db credentianls
        self.conn = psycopg2.connect(
            f"dbname={os.getenv('DB_NAME')} user={os.getenv('DB_USER')} password={os.getenv('DB_PASSWORD')} host={os.getenv('DB_HOST')}"
            )
        #change the cursor value to interact with the db
        self.cursor = self.conn.cursor()
    
    """
      Quit the db connection
    """
    def quit_db_connection(self):
        self.cursor.close()
        self.conn.close()

    """
      Get the db connection
    """
    def get_db_conn(self):
        return self.conn
    
    """
      Get the db cursor
    """
    def get_db_cursor(self):
        return self.cursor