from cryptography.hazmat.primitives.ciphers.aead import AESGCM
import os
import asyncpg
from .models import UserDB
from asyncpg import connect as test_pg_connect
import psycopg2

class CryptoService:
    def __init__(self):
        key_hex = os.getenv("MASTER_KEY")
        if not key_hex:
            raise ValueError("MASTER_KEY not found in environment.")
        self.key = bytes.fromhex(key_hex)
        
    def encrypt(self, plaintext: str) -> bytes:
        aesgcm = AESGCM(self.key)
        nonce = os.urandom(12)
        encrypted = aesgcm.encrypt(nonce, plaintext.encode(), None)
        return nonce + encrypted
    
    def decrypt(self, encrypted: bytes) -> str:
        aesgcm = AESGCM(self.key)
        nonce = encrypted[:12]
        ciphertext = encrypted[12:]
        decrypted = aesgcm.decrypt(nonce, ciphertext, None)
        return decrypted.decode()

async def connect_to_user_db(user_db_link: UserDB, crypto_service: CryptoService):
    db_password = crypto_service.decrypt(user_db_link.encrypted_password)
    conn = psycopg2.connect(
        f"dbname={user_db_link.db_name} user={user_db_link.db_user} password={db_password} host={user_db_link.db_host}"
    )
    return conn

async def get_db_columns_schema(user_db_link: UserDB, crypto_service: CryptoService):
    try:
        db = await connect_to_user_db(user_db_link, crypto_service)
        cursor = db.cursor()
        cursor.execute(f"""
           SELECT table_name, column_name, data_type 
           FROM information_schema.columns 
           WHERE table_schema = '{user_db_link.db_schema}'
        """)
        columns = cursor.fetchall()
        #print("estas son las tablas: ",columnas)
        cursor.close()
        db.close()
        return columns
    except Exception as e:
        return f"""An error was ocurred with the database: {e}"""


# This method obtain the primary keys of the database
async def get_db_pk_schema(user_db_link: UserDB, crypto_service: CryptoService):
    try:
        db = await connect_to_user_db(user_db_link, crypto_service)
        cursor = db.cursor()
        cursor.execute(f"""
        SELECT tc.table_name, kcu.column_name
        FROM information_schema.table_constraints AS tc
        JOIN information_schema.key_column_usage AS kcu
        ON tc.constraint_name = kcu.constraint_name
        WHERE tc.constraint_type = 'PRIMARY KEY' AND tc.table_schema = '{os.getenv('DB_SCHEMA')}'
        """)
        pk_info = cursor.fetchall()
        primary_keys = {table: column for table, column in pk_info}
        #print("Estas son las claves primarias: ", len(primary_keys))
        cursor.close()
        db.close()
        return primary_keys
    except Exception as e:
        return f"""An error was ocurred with the database: {e}"""

# This method obtain the foreign keys of the database
async def get_db_fk_schema(user_db_link: UserDB, crypto_service: CryptoService):
    try:
        db = await connect_to_user_db(user_db_link, crypto_service)
        cursor = db.cursor()
        cursor.execute(f"""
        SELECT tc.table_name, kcu.column_name, fk_column.data_type AS foreign_column_data_type, ccu.table_name AS foreign_table, ccu.column_name AS foreign_column
        FROM information_schema.table_constraints AS tc
        JOIN information_schema.key_column_usage AS kcu
        ON tc.constraint_name = kcu.constraint_name
        JOIN information_schema.constraint_column_usage AS ccu
        ON ccu.constraint_name = tc.constraint_name
        JOIN information_schema.columns AS fk_column
        ON fk_column.table_name = ccu.table_name AND fk_column.column_name = ccu.column_name
        WHERE tc.constraint_type = 'FOREIGN KEY' AND tc.table_schema = '{os.getenv('DB_SCHEMA')}'
        """)
        fk_info = cursor.fetchall()
        fk_info = list(set(fk_info))  # Eliminar duplicados
        print("Estas son las nuevas claves foraneas: ", len(fk_info))
        #print("Estas son las nuevas claves foraneas: ", fk_info)
        cursor.close()
        db.close()
        return fk_info
    except Exception as e:
        return f"""An error was ocurred with the database: {e}"""

#This method organize the database schema in a specific format, for the model processing
#Format: table_name column1_name column1_type column2_name column2_type ... foreign_key: FK_name FK_type from table_name column_name primary key: column_name [SEP]
#        table_name2 ...
async def parse_schema(user_db_link: UserDB, crypto_service: CryptoService):
    foreign_keys = {}
    try:
        fk_info = await get_db_fk_schema(user_db_link, crypto_service)
        for table, column, column_type, foreign_table, foreign_column in fk_info:
            foreign_keys.setdefault(table, []).append(f'foreign_key: "{column}" {column_type} from "{foreign_table}" "{foreign_column}"')

        tables = {}
        columnas = await get_db_columns_schema(user_db_link, crypto_service)
        for table, column, col_type in columnas:
            tables.setdefault(table, []).append(f'"{column}" {col_type}') 

        schema_parts = []
        primary_keys = await get_db_pk_schema(user_db_link, crypto_service)
        for table, columns in tables.items():
            schema_line = f'"{table}" ' + " , ".join(columns)
            if table in primary_keys:
                schema_line += f' , primary key: "{primary_keys[table]}"'
            if table in foreign_keys:
                schema_line += " , " + " , ".join(foreign_keys[table])
            schema_parts.append(schema_line)

        schema = ' [SEP] '.join(schema_parts)
        
        #print("schema: ", schema)
        return schema
    except Exception as e:
        fk_info = None
        return fk_info

async def test_user_db_connection(db_user,db_name,db_host,db_port, encrypted_password):
    try:
        crypto = CryptoService()
        
        db_password = crypto.decrypt(encrypted_password)
        print("crypted password:", encrypted_password)
        print("Decrypted password:", db_password)
        conn = await test_pg_connect(
            user=db_user,
            password=db_password,
            database=db_name,
            host=db_host,
            port=db_port,
            ssl="disable"
        )
        await conn.close()
        return {"message": "Connection successful", "successful": True}
    except Exception as e:
        return {"messsage":"Connection failed", "successful":False}

"""
@router.post("/chat")
async def chat_endpoint(message: dict, request: Request, db: Session = Depends(get_db_session)):
    user = request.state.user  # asumiendo que tienes auth middleware
    user_db_link = db.query(UserDatabaseLink).filter_by(user_id=user.id).first()

    if not user_db_link:
        return {"error": "No database linked"}

    crypto_service = CryptoService()
    conn = await connect_to_user_db(user_db_link, crypto_service)

    try:
        # Aquí puedes procesar el mensaje y generar una query
        query = generate_query_from_message(message["text"])
        result = await conn.fetch(query)  # asyncpg returns list of records
        return {"data": [dict(r) for r in result]}
    except Exception as e:
        return {"error": str(e)}
    finally:
        await conn.close()
"""