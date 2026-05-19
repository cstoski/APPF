from fastapi import APIRouter

router = APIRouter()


@router.post("/import")
def importar():
    return {"ok": True}


@router.get("/export")
def exportar():
    return {"ok": True}
