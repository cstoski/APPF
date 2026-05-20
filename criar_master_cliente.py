"""
Cria ou atualiza o usuário MASTER da instituição (cliente).

Uso (na raiz do projeto):
  python criar_master_cliente.py

Credenciais:
  Usuário: zelo_master
  Senha:   ZeloMaster2026
"""
from __future__ import annotations

from datetime import datetime

import bcrypt

from app.config.database import SessionLocal, init_db
from app.models.sys_models import Usuario

USERNAME = "zelo_master"
PASSWORD = "ZeloMaster2026"
PERFIL = "MASTER"


def _hash_senha(senha: str) -> str:
    return bcrypt.hashpw(senha.encode("utf-8"), bcrypt.gensalt()).decode("utf-8")


def main() -> None:
    init_db()
    db = SessionLocal()
    try:
        senha_hash = _hash_senha(PASSWORD)
        user = db.query(Usuario).filter(Usuario.username == USERNAME).first()
        if user:
            user.perfil = PERFIL
            user.senha_hash = senha_hash
            user.ativo = True
            acao = "atualizado"
        else:
            agora = datetime.utcnow()
            db.add(
                Usuario(
                    username=USERNAME,
                    senha_hash=senha_hash,
                    perfil=PERFIL,
                    ativo=True,
                    data_criacao=agora,
                    data_alteracao=agora,
                )
            )
            acao = "criado"

        for nome in ("admin", "Cristiano", "Fernanda"):
            u = db.query(Usuario).filter(Usuario.username == nome).first()
            if u and u.perfil != "MASTER":
                u.perfil = "MASTER"
                print(f"Perfil de '{nome}' corrigido para MASTER.")

        db.commit()
        print(f"Usuario MASTER {acao} com sucesso.")
        print(f"  Usuario: {USERNAME}")
        print(f"  Senha:   {PASSWORD}")
        print(f"  Perfil:  {PERFIL}")
        print()
        print("Se ja estava logado, use 'Sair e trocar usuario' e entre de novo para atualizar o perfil no token.")
    finally:
        db.close()


if __name__ == "__main__":
    main()
