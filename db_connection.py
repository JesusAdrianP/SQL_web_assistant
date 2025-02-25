# psycopg2 para obtener el esquema de la bd de postgres, para posteriomente proporcionarle esta información al modelo a utilizar
import psycopg2
import os

from dotenv import load_dotenv
load_dotenv()

class DBConnection:
    """
      Se inicializan en none los objetos que van a interactuar con la bd porque la conexión se hará al llamar los métodos definidos para eso
    """
    def __init__(self):
        self.conn = None
        self.cursor = None

    """
      genera la conexión con la base de datos a la cual se le harán las consultas
    """
    def generate_db_connection(self):
        #se obtienen las credenciales de la bd para poder extraer el esquema
        self.conn = psycopg2.connect(
            f"dbname={os.getenv('DB_NAME')} user={os.getenv('DB_USER')} password={os.getenv('DB_PASSWORD')} host={os.getenv('DB_HOST')}"
            )
        #objeto encargado de interactuar con la bd
        self.cursor = self.conn.cursor()
    
    """
      cierra la conexión con la base de datos a la cual se le harán las consultas
    """
    def quit_db_connection(self):
        self.cursor.close()
        self.conn.close()

    def get_db_conn(self):
        return self.conn
    
    def get_db_cursor(self):
        return self.cursor