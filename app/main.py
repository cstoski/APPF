from __future__ import annotations



from pathlib import Path



from fastapi import FastAPI, HTTPException, Request

from fastapi.middleware.cors import CORSMiddleware

from fastapi.responses import FileResponse

from fastapi.staticfiles import StaticFiles



from app.config.database import init_db, seed_admin_if_needed

from app.runtime_paths import get_assinaturas_dir, get_frontend_dist_dir

from app.routers import (

    auth_router,

    usuarios_router,

    appf_router,

    contrib_router,

    dados_router,

    relatorios_router,

    sistema_router,

    dashboard_router,

    desktop_router,

)



ASSIN_DIR = get_assinaturas_dir()



app = FastAPI(

    title="ZELO - Contribuições APPF",

    version="1.0.0",

)



app.add_middleware(

    CORSMiddleware,

    allow_origins=["*"],

    allow_credentials=True,

    allow_methods=["*"],

    allow_headers=["*"],

)



app.mount(
    "/static/assinaturas",
    StaticFiles(directory=str(ASSIN_DIR)),
    name="assinaturas",
)



app.include_router(auth_router)

app.include_router(usuarios_router)

app.include_router(appf_router)

app.include_router(contrib_router)

app.include_router(dados_router)

app.include_router(relatorios_router)

app.include_router(sistema_router)

app.include_router(dashboard_router)

app.include_router(desktop_router)


@app.middleware("http")
async def rastrear_usuarios_ativos(request: Request, call_next):
    from app.services.seguranca_service import decodificar_token
    from app.services.sessao_ativa_service import registrar_atividade

    response = await call_next(request)
    auth = request.headers.get("authorization") or ""
    if auth.lower().startswith("bearer "):
        token = auth[7:].strip()
        if token:
            try:
                payload = decodificar_token(token)
                sub = payload.get("sub")
                if sub:
                    registrar_atividade(str(sub))
            except HTTPException:
                pass
    return response





@app.get("/ping")

def ping() -> dict[str, str]:

    return {"status": "ok"}





def _montar_frontend_spa() -> None:

    dist = get_frontend_dist_dir()

    index = dist / "index.html"

    if not index.is_file():

        return



    @app.get("/")

    async def spa_index():

        return FileResponse(index)



    @app.get("/{full_path:path}")

    async def spa_files(full_path: str):

        if full_path.startswith("api/") or full_path.startswith("static/"):

            raise HTTPException(status_code=404, detail="Not found")

        alvo = dist / full_path

        if alvo.is_file():

            return FileResponse(alvo)

        return FileResponse(index)





_montar_frontend_spa()





@app.on_event("startup")

def on_startup() -> None:

    init_db()

    seed_admin_if_needed()

