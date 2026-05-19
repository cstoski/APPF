from fastapi import APIRouter, HTTPException

router = APIRouter()


@router.get("/", tags=["usuarios"])
def listar_usuarios():
    # placeholder: require MASTER/DEV perfis
    return {"ok": True, "usuarios": []}
