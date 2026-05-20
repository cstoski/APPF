from app.config.database import SessionLocal
from app.models.sys_models import Usuario
from app.services.seguranca_service import gerar_hash_senha

db = SessionLocal()

admin = Usuario(
    username="admin",
    senha_hash=gerar_hash_senha("admin_password_appf"),
    perfil="MASTER",
    ativo=True,
)

db.add(admin)
db.commit()

print("✅ Admin criado com sucesso")
