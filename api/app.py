"""
FastAPI application factory for Tars.
Sets up lifespan, CORS middleware, and includes all route modules.
"""
from contextlib import asynccontextmanager

from dotenv import load_dotenv
from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware
from langgraph.checkpoint.postgres.aio import AsyncPostgresSaver

from agents.brain.nodes import workflow
from agents.RAG.save_memory import get_db_uri
from api.routes import (
    auth_router,
    chat_router,
    profile_router,
    roleplay_router,
    stt_router,
    admin_router,
)

load_dotenv()

app_state: dict = {}
DB_URI = get_db_uri()


@asynccontextmanager
async def lifespan(app: FastAPI):
    async with AsyncPostgresSaver.from_conn_string(DB_URI) as checkpointer:
        await checkpointer.setup()

        app_state["checkpointer"] = checkpointer
        app_instance = workflow.compile(checkpointer=checkpointer)
        app_state["app_instance"] = app_instance

        # Share app_state with the chat router
        from api.routes.chat import app_state as chat_state
        chat_state.update(app_state)

        # Share app_state with the profile router (for lesson progress)
        from api.routes.profile import app_state as profile_state
        profile_state.update(app_state)

        try:
            yield
        finally:
            from agents.dataBase.pool import close_pool
            close_pool()


app = FastAPI(title="Tars API", lifespan=lifespan)

app.add_middleware(
    CORSMiddleware,
    allow_origins=[
        "https://localhost:5173",
        "https://127.0.0.1:5173",
        "http://localhost:5173",
        "http://127.0.0.1:5173",
        "https://192.168.3.11:5173",
        "http://192.168.3.11:5173",
    ],
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

# Health check
@app.get("/health")
def health():
    return {"status": "ok"}

# Include route modules
app.include_router(auth_router, prefix="/auth", tags=["auth"])
app.include_router(chat_router, tags=["chat"])
app.include_router(profile_router, tags=["profile"])
app.include_router(roleplay_router, prefix="/roleplay", tags=["roleplay"])
app.include_router(stt_router, prefix="/stt", tags=["stt"])
app.include_router(admin_router, prefix="/admin", tags=["admin"])
