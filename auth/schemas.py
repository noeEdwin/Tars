"""
auth/schemas.py
Modelos Pydantic para los endpoints de autenticación de Tars.
Toda validación de entrada se hace aquí — nunca confiar en datos del cliente.

Estructura de tabla `users` real:
    id (Integer SERIAL) | username | email | hashed_password
    first_name | last_name | hsk_level (int, default 1) | native_language (text, default 'es')
"""
import re
from pydantic import BaseModel, EmailStr, field_validator, model_validator


# ─── Registro ─────────────────────────────────────────────────────────────────

class RegisterRequest(BaseModel):
    username: str
    first_name: str
    last_name: str
    email: EmailStr
    password: str
    password_confirm: str
    # Opcionales — la BD tiene defaults pero el front puede enviarlos
    hsk_level: int = 1
    native_language: str = "es"
    learning_goals: str = "Travel"
    interests: str = ""

    @field_validator("username")
    @classmethod
    def username_valid(cls, v: str) -> str:
        v = v.strip()
        if len(v) < 3:
            raise ValueError("El nombre de usuario debe tener al menos 3 caracteres.")
        if len(v) > 50:
            raise ValueError("El nombre de usuario no puede superar los 50 caracteres.")
        if not re.match(r"^[a-zA-Z0-9_.-]+$", v):
            raise ValueError("El nombre de usuario solo puede contener letras, números, _, . y -")
        return v

    @field_validator("first_name", "last_name")
    @classmethod
    def name_not_empty(cls, v: str) -> str:
        v = v.strip()
        if not v:
            raise ValueError("Este campo no puede estar vacío.")
        if len(v) > 100:
            raise ValueError("El nombre no puede superar los 100 caracteres.")
        return v

    @field_validator("password")
    @classmethod
    def password_strength(cls, v: str) -> str:
        if len(v) < 8:
            raise ValueError("La contraseña debe tener al menos 8 caracteres.")
        if not re.search(r"[A-Z]", v):
            raise ValueError("La contraseña debe contener al menos una letra mayúscula.")
        if not re.search(r"[0-9]", v):
            raise ValueError("La contraseña debe contener al menos un número.")
        return v

    @field_validator("hsk_level")
    @classmethod
    def hsk_range(cls, v: int) -> int:
        if not (1 <= v <= 9):
            raise ValueError("hsk_level debe estar entre 1 y 9.")
        return v

    @model_validator(mode="after")
    def passwords_match(self) -> "RegisterRequest":
        if self.password != self.password_confirm:
            raise ValueError("Las contraseñas no coinciden.")
        return self


class RegisterResponse(BaseModel):
    message: str
    user_id: int       # Integer SERIAL devuelto por la BD
    username: str


# ─── Login ────────────────────────────────────────────────────────────────────

class LoginRequest(BaseModel):
    username: str
    password: str

    @field_validator("username", "password")
    @classmethod
    def not_empty(cls, v: str) -> str:
        if not v or not v.strip():
            raise ValueError("Este campo es obligatorio.")
        return v


class TokenResponse(BaseModel):
    access_token: str
    token_type: str = "bearer"
    user_id: int       # Integer SERIAL, no UUID
    username: str
    first_name: str
    hsk_level: int


# ─── Perfil ───────────────────────────────────────────────────────────────────

class UserProfile(BaseModel):
    id: int
    username: str
    first_name: str
    last_name: str
    email: str
    hsk_level: int
    native_language: str
    learning_goals: str
    interests: str


class ProfileUpdateRequest(BaseModel):
    first_name: str
    last_name: str
    hsk_level: int
    native_language: str
    learning_goals: str
    interests: str
