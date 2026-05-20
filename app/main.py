from __future__ import annotations

from pathlib import Path

from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware
from fastapi.staticfiles import StaticFiles

from app.config.database import init_db, seed_admin_if_needed, ensure_singleton_config_appf
from app.routers import (
    auth_router,
    usuarios_router,
    appf_router,
    contrib_router,
    dados_router,
    sistema_router,
)

APP_DIR = Path(__file__).resolve().parent
STATIC_DIR = APP_DIR / "static"
ASSIN_DIR = STATIC_DIR / "assinaturas"
ASSIN_DIR.mkdir(parents=True, exist_ok=True)

app = FastAPI(
    title="APPF Recibos Local (Offline)",
    version="1.0.0",
)

# CORS (ambiente local / offline)
app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

# Monta diretório static para servir assinaturas via URL
app.mount("/static", StaticFiles(directory=str(STATIC_DIR)), name="static")

# Rotas
app.include_router(auth_router)
app.include_router(usuarios_router)
app.include_router(appf_router)
app.include_router(contrib_router)
app.include_router(dados_router)
app.include_router(sistema_router)


@app.get('/ping')
def ping() -> dict[str, str]:
    return {'status': 'ok'}


@app.on_event("startup")
def on_startup() -> None:
    init_db()
    # seed_admin_if_needed()  # Temporarily disabled due to passlib/bcrypt incompatibility
    # ensure_singleton_config_appf()  # Temporarily disabled