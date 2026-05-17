from api.routes.auth import router as auth_router
from api.routes.chat import router as chat_router
from api.routes.profile import router as profile_router
from api.routes.roleplay import router as roleplay_router
from api.routes.stt import router as stt_router
from api.routes.admin import router as admin_router

__all__ = [
    "auth_router",
    "chat_router",
    "profile_router",
    "roleplay_router",
    "stt_router",
    "admin_router",
]
