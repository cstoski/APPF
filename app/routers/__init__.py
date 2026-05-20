from app.routers.autenticacao import router as auth_router
from app.routers.usuarios import router as usuarios_router
from app.routers.appf import router as appf_router
from app.routers.contribricoes import router as contrib_router
from app.routers.dados import router as dados_router
from app.routers.relatorios import router as relatorios_router
from app.routers.sistema import router as sistema_router
from app.routers.dashboard import router as dashboard_router
from app.routers.desktop import router as desktop_router

__all__ = [
    "auth_router",
    "usuarios_router",
    "appf_router",
    "contrib_router",
    "dados_router",
    "relatorios_router",
    "sistema_router",
    "dashboard_router",
    "desktop_router",
]