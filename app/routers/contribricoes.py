from fastapi import APIRouter

router = APIRouter()


@router.get("/search")
def busca():
    return {"ok": True, "result": []}


@router.post("/lancar")
def lancar():
    return {"ok": True}
