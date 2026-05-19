from fastapi import APIRouter

router = APIRouter()


@router.get("/licenca")
def get_licenca():
    return {"ok": True, "licenca": {}}


@router.post("/licenca/ativar")
def ativar_licenca():
    return {"ok": True}
