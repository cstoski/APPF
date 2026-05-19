from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware
from fastapi.staticfiles import StaticFiles

app = FastAPI(title="APPF API")

app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

# Mount static files (assinaturas)
app.mount("/static", StaticFiles(directory="app/static"), name="static")


@app.on_event("startup")
def on_startup():
    # create database tables if not present
    try:
        from .config.database import engine, Base

        Base.metadata.create_all(bind=engine)
    except Exception:
        pass


# include routers (import lazily)
try:
    from .routers import autenticacao, usuarios, appf, contribricoes, dados, sistema

    app.include_router(autenticacao.router, prefix="/api/v1/auth")
    app.include_router(usuarios.router, prefix="/api/v1/usuarios")
    app.include_router(appf.router, prefix="/api/v1/appf")
    app.include_router(contribricoes.router, prefix="/api/v1/contribuicoes")
    app.include_router(dados.router, prefix="/api/v1/dados")
    app.include_router(sistema.router, prefix="/api/v1/sistema")
except Exception:
    pass
