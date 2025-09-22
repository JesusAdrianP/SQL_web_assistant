from jose import JWTError, jwt
from .models import User
from typing import Annotated
from fastapi import Depends, HTTPException, status
from .auth import SECRET_KEY, ALGORITHM, oauth2_bearer
from api_root.api_db import get_db_dependency

db_dependency = get_db_dependency()

async def is_superuser(token: Annotated[str, Depends(oauth2_bearer)], db: db_dependency):
    try:
        payload = jwt.decode(token, SECRET_KEY, algorithms=[ALGORITHM])
        email: str = payload.get("sub")
        user_id: int = payload.get("id")
        if email is None or user_id is None:
            print(user_id)
            print(email)
            raise HTTPException(status_code=status.HTTP_401_UNAUTHORIZED, detail="Invalid token")
        is_superuser = db.query(User).filter(User.id == user_id).first().is_superuser
        if is_superuser is None:
            raise HTTPException(status_code=status.HTTP_403_FORBIDDEN, detail="Not enough permissions")
        return {"is_superuser": is_superuser}
    except JWTError as e:
        print("otro error")
        raise HTTPException(status_code=status.HTTP_401_UNAUTHORIZED, detail=f"Invalid token {e}")