"""Authentication routes: register and login."""
import asyncio
import logging

from fastapi import APIRouter, HTTPException, status
from openai import OpenAI

from agents.dataBase.auth_queries import (
    get_user_by_username,
    get_user_by_email,
    get_user_by_username_simple,
    create_user,
)
from auth.security import hash_password, verify_password, create_access_token
from auth.schemas import (
    RegisterRequest,
    RegisterResponse,
    LoginRequest,
    TokenResponse,
)

logger = logging.getLogger(__name__)
router = APIRouter()
openai_client = OpenAI()


@router.post("/register", response_model=RegisterResponse, status_code=status.HTTP_201_CREATED)
async def register(req: RegisterRequest):
    if await asyncio.to_thread(get_user_by_username_simple, req.username):
        raise HTTPException(
            status_code=status.HTTP_409_CONFLICT,
            detail="El nombre de usuario ya está en uso. Elige otro.",
        )

    if await asyncio.to_thread(get_user_by_email, req.email):
        raise HTTPException(
            status_code=status.HTTP_409_CONFLICT,
            detail="Ya existe una cuenta con ese correo electrónico.",
        )

    hashed = await asyncio.to_thread(hash_password, req.password)

    try:
        new_user = await asyncio.to_thread(
            create_user,
            req.username,
            req.first_name,
            req.last_name,
            req.email,
            hashed,
            req.hsk_level,
            req.native_language,
            req.learning_goals,
            req.interests,
        )
    except Exception as exc:
        logger.error("Error creating user: %s", exc)
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail="Error interno al crear el usuario. Inténtalo de nuevo.",
        )

    return RegisterResponse(
        message="Cuenta creada exitosamente. ¡Bienvenido a Tars!",
        user_id=new_user["id"],
        username=new_user["username"],
    )


@router.post("/login", response_model=TokenResponse)
async def login(req: LoginRequest):
    user = await asyncio.to_thread(get_user_by_username, req.username)

    INVALID_CREDENTIALS = "Usuario o contraseña incorrectos."

    if not user:
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail=INVALID_CREDENTIALS,
            headers={"WWW-Authenticate": "Bearer"},
        )

    password_ok = await asyncio.to_thread(
        verify_password, req.password, user["hashed_password"]
    )
    if not password_ok:
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail=INVALID_CREDENTIALS,
            headers={"WWW-Authenticate": "Bearer"},
        )

    token = await asyncio.to_thread(
        create_access_token,
        {"sub": user["username"], "user_id": user["id"]},
    )

    return TokenResponse(
        access_token=token,
        token_type="bearer",
        user_id=user["id"],
        username=user["username"],
        first_name=user["first_name"],
        hsk_level=user["hsk_level"],
    )
