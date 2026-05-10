import os
import bcrypt  # Usamos la librería nativa directamente
from datetime import datetime, timedelta, timezone
from typing import Any
from jose import jwt, JWTError
from fastapi import Depends, HTTPException, status
from fastapi.security import OAuth2PasswordBearer

# ─── Configuración JWT ────────────────────────────────────────────────────────
#usamos JWT un valor por defecto para desarrollo, pero SE CAMBIA EN PRODUCCIÓN
_JWT_SECRET: str = os.getenv("JWT_SECRET", "CAMBIAR_PRODUCCION")
_JWT_ALGORITHM: str = "HS256"
_JWT_EXPIRE_MINUTES: int = int(os.getenv("JWT_EXPIRE_MINUTES", "60"))

# ─── Funciones de contraseña (Sin Passlib para evitar el error 500) ──────────

def hash_password(plain_password: str) -> str:
    """
    Hashea la contraseña usando bcrypt nativo.
    Esto evita el error de '72 bytes' de passlib.
    """
    # Convertir a bytes, generar salt (12 rondas para OWASP) y hashear
    pwd_bytes = plain_password.encode('utf-8')
    salt = bcrypt.gensalt(rounds=12)
    hashed = bcrypt.hashpw(pwd_bytes, salt)
    return hashed.decode('utf-8')

def verify_password(plain_password: str, hashed_password: str) -> bool:
    """
    Verifica la contraseña comparando los bytes de forma segura.
    """
    try:
        return bcrypt.checkpw(
            plain_password.encode('utf-8'),
            hashed_password.encode('utf-8')
        )
    except Exception:
        return False

# ─── Funciones JWT ────────────────────────────────────────────────────────────

def create_access_token(data: dict[str, Any]) -> str:
    """Genera el token JWT firmado."""
    to_encode = data.copy()
    expire = datetime.now(tz=timezone.utc) + timedelta(minutes=_JWT_EXPIRE_MINUTES)
    to_encode["exp"] = expire
    to_encode["iat"] = datetime.now(tz=timezone.utc)
    return jwt.encode(to_encode, _JWT_SECRET, algorithm=_JWT_ALGORITHM)


oauth2_scheme = OAuth2PasswordBearer(tokenUrl="/auth/login")

def get_current_user(token: str = Depends(oauth2_scheme)) -> int:
    """Valida el token y devuelve el ID del usuario."""
    credentials_exception = HTTPException(
        status_code=status.HTTP_401_UNAUTHORIZED,
        detail="Could not validate credentials",
        headers={"WWW-Authenticate": "Bearer"},
    )
    try:
        payload = jwt.decode(token, _JWT_SECRET, algorithms=[_JWT_ALGORITHM])
        user_id: int = payload.get("user_id")
        if user_id is None:
            raise credentials_exception
        return user_id
    except JWTError:
        raise credentials_exception