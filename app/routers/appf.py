from fastapi import APIRouter, UploadFile, File

router = APIRouter()


@router.get("/")
def get_appf():
    return {"ok": True, "config": {}}


@router.post("/upload-assinatura")
def upload_assinatura(file: UploadFile = File(...)):
    # save to app/static/assinaturas
    path = f"app/static/assinaturas/{file.filename}"
    with open(path, "wb") as f:
        f.write(file.file.read())
    return {"ok": True, "path": path}
