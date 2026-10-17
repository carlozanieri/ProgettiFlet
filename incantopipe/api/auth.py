# api/auth.py
import jwt
from datetime import datetime, timedelta, timezone
from fastapi import Depends, HTTPException, status
from fastapi.security import OAuth2PasswordBearer
from config import SECRET_KEY, JWT_ALGORITHM, JWT_EXPIRE_MINUTES
from typing import Optional
from fastapi.security import HTTPBearer, HTTPAuthorizationCredentials

security_optional = HTTPBearer(auto_error=False)
# Configura Django per usare solo i suoi hashers (PRIMA di importarli)
import django_setup  # noqa: F401
from django.contrib.auth.hashers import make_password, check_password


oauth2_scheme = OAuth2PasswordBearer(tokenUrl="api/v1/auth/login")


def verify_password(plain_password: str, hashed_password: str) -> bool:
    try:
        return check_password(plain_password, hashed_password)
    except Exception:
        return False


def hash_password(plain_password: str) -> str:
    return make_password(plain_password)


def create_access_token(data: dict) -> str:
    to_encode = data.copy()
    expire = datetime.now(timezone.utc) + timedelta(minutes=JWT_EXPIRE_MINUTES)
    to_encode.update({"exp": expire})
    return jwt.encode(to_encode, SECRET_KEY, algorithm=JWT_ALGORITHM)


def get_current_user(token: str = Depends(oauth2_scheme)) -> dict:
    credentials_exception = HTTPException(
        status_code=status.HTTP_401_UNAUTHORIZED,
        detail="Credenziali non valide",
        headers={"WWW-Authenticate": "Bearer"},
    )
    try:
        payload = jwt.decode(token, SECRET_KEY, algorithms=[JWT_ALGORITHM])
        username = payload.get("sub")
        user_id = payload.get("user_id")
        if username is None or user_id is None:
            raise credentials_exception
        return {"username": username, "user_id": user_id}
    except jwt.PyJWTError:
        
        raise credentials_exception


def get_optional_user(
    credentials: Optional[HTTPAuthorizationCredentials] = Depends(security_optional),
) -> Optional[dict]:
    """Restituisce l'utente se c'è un token valido, altrimenti None."""
    if not credentials:
        return None
    try:
        payload = jwt.decode(credentials.credentials, SECRET_KEY, algorithms=[JWT_ALGORITHM])
        username = payload.get("sub")
        user_id = payload.get("user_id")
        if username is None or user_id is None:
            return None
        return {"username": username, "user_id": user_id}
    except jwt.PyJWTError:
        return None

def get_current_admin(current_user: dict = Depends(get_current_user)) -> dict:
    """Verifica che l'utente sia staff/admin, altrimenti 403."""
    import psycopg2
    from psycopg2.extras import RealDictCursor
    from config import DATABASE_URL

    conn = None
    try:
        conn = psycopg2.connect(DATABASE_URL, cursor_factory=RealDictCursor)
        with conn.cursor() as cur:
            cur.execute(
                "SELECT is_staff FROM auth_user WHERE id = %s",
                (current_user["user_id"],)
            )
            row = cur.fetchone()
            if not row or not row["is_staff"]:
                raise HTTPException(
                    status_code=403,
                    detail="Accesso riservato agli amministratori"
                )
        return current_user
    finally:
        if conn:
            conn.close()

    