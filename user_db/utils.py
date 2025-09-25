from cryptography.hazmat.primitives.ciphers.aead import AESGCM
import os
import asyncpg
from .models import UserDB
from asyncpg import connect as test_pg_connect

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
    password = crypto_service.decrypt(user_db_link.encrypted_password)
    conn = await asyncpg.connect(
        user=user_db_link.username,
        password=password,
        database=user_db_link.db_name,
        host=user_db_link.host,
        port=user_db_link.port,
        ssl="require"  
    )
    return conn

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