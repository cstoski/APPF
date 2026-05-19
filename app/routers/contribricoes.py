from __future__ import annotations

from datetime import datetime
from typing import List

from fastapi import APIRouter, Depends, HTTPException, status, BackgroundTasks
from sqlalchemy import select, func
from sqlalchemy.exc import IntegrityError
from sqlalchemy.orm import Session

from app.config.database import get_db
from app.models.core_models import Contribuinte, Recibo, Aluno, AlunoResponsavel
from app.models.sys_models import ConfigAPPF
from app.schemas.core_schemas import (
    ContribuinteCreate,
    ContribuinteOut,
    ContribuinteBuscaOut,
    ReciboCreate,
    ReciboOut,
    ReciboCancelamentoIn,
    EmailRelatorioIn,
    SMTPConfigIn,
    AlunoCreate,
    AlunoOut,
    VinculoCreate,
    VinculoOut,
)
from app.services.licenca_service import require_licenca
from app.services.seguranca_service import (
    cifrar,
    decifrar,
    normalizar_cpf,
    mascarar_cpf,
    get_current_username,
)
from app.services.email_service import construir_tabela_html, disparar_email_background

router = APIRouter(prefix="/api/v1", tags=["Contribuições e Recibos"])


def _obter_config_appf(db: Session) -> ConfigAPPF:
    cfg = db.query(ConfigAPPF).first()
    if not cfg:
        cfg = ConfigAPPF(
            razao_social="",
            cnpj="",
            endereco="",
            nome_presidente="",
            caminho_assinatura_presidente="",
            nome_tesoureiro="",
            caminho_assinatura_tesoureiro="",
        )
        db.add(cfg)
        db.commit()
        db.refresh(cfg)
    return cfg


def _gerar_texto_legal(cfg: ConfigAPPF) -> str:
    return (
        f"Recibo referente a contribuição voluntária registrada para a APPF.\n"
        f"Instituição: {cfg.razao_social} | CNPJ: {cfg.cnpj}\n"
        f"Gestão vigente à época: Presidente: {cfg.nome_presidente} | Tesoureiro: {cfg.nome_tesoureiro}\n"
        f"Assinaturas: presidente={cfg.caminho_assinatura_presidente} | tesoureiro={cfg.caminho_assinatura_tesoureiro}\n"
        f"Este registro é emitido por sistema local com rastreabilidade temporal."
    )


def _proximo_numero_recibo(db: Session) -> str:
    hoje = datetime.utcnow().strftime("%Y%m%d")
    prefixo = hoje

    # lock de escrita cedo (SQLite) para reduzir colisões
    db.execute("BEGIN IMMEDIATE")

    max_num = db.execute(
        select(func.max(Recibo.numero)).where(Recibo.numero.like(f"{prefixo}%"))
    ).scalar_one_or_none()

    if not max_num:
        contador = 1
    else:
        try:
            contador = int(max_num[-4:]) + 1
        except Exception:
            contador = 1

    return f"{prefixo}{contador:04d}"


# =========================================================
# CONTRIBUINTES
# =========================================================

@router.get("/contribuintes/buscar", response_model=List[ContribuinteBuscaOut], dependencies=[Depends(require_licenca)])
def buscar_contribuintes(termo: str, db: Session = Depends(get_db)) -> List[ContribuinteBuscaOut]:
    t = termo.strip()
    if not t:
        return []

    candidatos = (
        db.query(Contribuinte)
        .filter(Contribuinte.nome_completo.ilike(f"%{t}%"))
        .limit(30)
        .all()
    )

    digits = normalizar_cpf(t)

    if not candidatos and digits:
        candidatos = db.query(Contribuinte).limit(2000).all()

    resultados: List[ContribuinteBuscaOut] = []
    for c in candidatos:
        cpf_real = decifrar(c.cpf_cifrado) or ""
        cpf_norm = normalizar_cpf(cpf_real)

        match_nome = t.lower() in c.nome_completo.lower()
        match_cpf = bool(digits) and digits in cpf_norm

        if match_nome or match_cpf:
            resultados.append(
                ContribuinteBuscaOut(
                    id=c.id,
                    nome_completo=c.nome_completo,
                    cpf=mascarar_cpf(cpf_real),
                )
            )

    return resultados


@router.post("/contribuintes", response_model=ContribuinteOut, status_code=201, dependencies=[Depends(require_licenca)])
def criar_contribuinte(data: ContribuinteCreate, db: Session = Depends(get_db)) -> ContribuinteOut:
    if data.consentimento_lgpd is False:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail="O cadastro exige o consentimento do contribuinte conforme LGPD.",
        )

    cpf_norm = normalizar_cpf(data.cpf)
    if len(cpf_norm) < 5:
        raise HTTPException(status_code=400, detail="CPF inválido.")

    cpf_cif = cifrar(cpf_norm)

    if db.query(Contribuinte).filter(Contribuinte.cpf_cifrado == cpf_cif).first():
        raise HTTPException(status_code=400, detail="CPF já cadastrado nesta máquina.")

    c = Contribuinte(
        nome_completo=data.nome_completo.strip(),
        cpf_cifrado=cpf_cif,
        email_cifrado=cifrar(data.email) if data.email else None,
        telefone_cifrado=cifrar(data.telefone) if data.telefone else None,
        consentimento_lgpd=bool(data.consentimento_lgpd),
        observacoes=(data.observacoes.strip() if data.observacoes else None),
    )
    db.add(c)
    db.commit()
    db.refresh(c)
    return c


# =========================================================
# ALUNOS (CRUD)
# =========================================================

@router.post("/alunos", response_model=AlunoOut, status_code=201, dependencies=[Depends(require_licenca)])
def criar_aluno(body: AlunoCreate, db: Session = Depends(get_db)) -> AlunoOut:
    aluno = Aluno(
        nome_completo=body.nome_completo.strip(),
        turma=(body.turma.strip() if body.turma else None),
        matricula=(body.matricula.strip() if body.matricula else None),
    )
    db.add(aluno)
    db.commit()
    db.refresh(aluno)
    return aluno


@router.get("/alunos", response_model=List[AlunoOut], dependencies=[Depends(require_licenca)])
def listar_alunos(db: Session = Depends(get_db)) -> List[AlunoOut]:
    return db.query(Aluno).order_by(Aluno.id.asc()).limit(2000).all()


@router.get("/alunos/buscar", response_model=List[AlunoOut], dependencies=[Depends(require_licenca)])
def buscar_alunos(termo: str, db: Session = Depends(get_db)) -> List[AlunoOut]:
    t = termo.strip()
    if not t:
        return []
    return (
        db.query(Aluno)
        .filter(
            (Aluno.nome_completo.ilike(f"%{t}%"))
            | (Aluno.matricula.ilike(f"%{t}%"))  # type: ignore[arg-type]
        )
        .order_by(Aluno.id.asc())
        .limit(200)
        .all()
    )


@router.get("/alunos/{aluno_id}", response_model=AlunoOut, dependencies=[Depends(require_licenca)])
def obter_aluno(aluno_id: int, db: Session = Depends(get_db)) -> AlunoOut:
    aluno = db.query(Aluno).filter(Aluno.id == aluno_id).first()
    if not aluno:
        raise HTTPException(status_code=404, detail="Aluno não encontrado.")
    return aluno


@router.put("/alunos/{aluno_id}", response_model=AlunoOut, dependencies=[Depends(require_licenca)])
def atualizar_aluno(aluno_id: int, body: AlunoCreate, db: Session = Depends(get_db)) -> AlunoOut:
    aluno = db.query(Aluno).filter(Aluno.id == aluno_id).first()
    if not aluno:
        raise HTTPException(status_code=404, detail="Aluno não encontrado.")

    aluno.nome_completo = body.nome_completo.strip()
    aluno.turma = body.turma.strip() if body.turma else None
    aluno.matricula = body.matricula.strip() if body.matricula else None

    db.commit()
    db.refresh(aluno)
    return aluno


@router.delete("/alunos/{aluno_id}", status_code=204, dependencies=[Depends(require_licenca)])
def excluir_aluno(aluno_id: int, db: Session = Depends(get_db)) -> None:
    aluno = db.query(Aluno).filter(Aluno.id == aluno_id).first()
    if not aluno:
        raise HTTPException(status_code=404, detail="Aluno não encontrado.")

    # Se houver vínculos, bloqueia para evitar perda de integridade
    vincs = db.query(AlunoResponsavel).filter(AlunoResponsavel.aluno_id == aluno_id).count()
    if vincs > 0:
        raise HTTPException(
            status_code=409,
            detail="Aluno possui vínculos. Remova os vínculos antes de excluir.",
        )

    db.delete(aluno)
    db.commit()
    return None


# =========================================================
# VÍNCULOS (AlunoResponsavel)
# =========================================================

@router.post("/vinculos", response_model=VinculoOut, status_code=201, dependencies=[Depends(require_licenca)])
def criar_vinculo(body: VinculoCreate, db: Session = Depends(get_db)) -> VinculoOut:
    aluno = db.query(Aluno).filter(Aluno.id == body.aluno_id).first()
    if not aluno:
        raise HTTPException(status_code=404, detail="Aluno não encontrado.")

    contrib = db.query(Contribuinte).filter(Contribuinte.id == body.contribuinte_id).first()
    if not contrib:
        raise HTTPException(status_code=404, detail="Contribuinte não encontrado.")

    vinc = AlunoResponsavel(
        aluno_id=body.aluno_id,
        contribuinte_id=body.contribuinte_id,
        parentesco=(body.parentesco.strip() if body.parentesco else None),
    )
    db.add(vinc)
    try:
        db.commit()
    except IntegrityError:
        db.rollback()
        raise HTTPException(status_code=409, detail="Vínculo já existe para este aluno e contribuinte.")
    db.refresh(vinc)
    return vinc


@router.get("/vinculos/aluno/{aluno_id}", response_model=List[VinculoOut], dependencies=[Depends(require_licenca)])
def listar_vinculos_por_aluno(aluno_id: int, db: Session = Depends(get_db)) -> List[VinculoOut]:
    # valida existência do aluno
    if not db.query(Aluno).filter(Aluno.id == aluno_id).first():
        raise HTTPException(status_code=404, detail="Aluno não encontrado.")
    return (
        db.query(AlunoResponsavel)
        .filter(AlunoResponsavel.aluno_id == aluno_id)
        .order_by(AlunoResponsavel.id.asc())
        .all()
    )


@router.get("/vinculos/contribuinte/{contribuinte_id}", response_model=List[VinculoOut], dependencies=[Depends(require_licenca)])
def listar_vinculos_por_contribuinte(contribuinte_id: int, db: Session = Depends(get_db)) -> List[VinculoOut]:
    if not db.query(Contribuinte).filter(Contribuinte.id == contribuinte_id).first():
        raise HTTPException(status_code=404, detail="Contribuinte não encontrado.")
    return (
        db.query(AlunoResponsavel)
        .filter(AlunoResponsavel.contribuinte_id == contribuinte_id)
        .order_by(AlunoResponsavel.id.asc())
        .all()
    )


@router.delete("/vinculos/{vinculo_id}", status_code=204, dependencies=[Depends(require_licenca)])
def remover_vinculo(vinculo_id: int, db: Session = Depends(get_db)) -> None:
    vinc = db.query(AlunoResponsavel).filter(AlunoResponsavel.id == vinculo_id).first()
    if not vinc:
        raise HTTPException(status_code=404, detail="Vínculo não encontrado.")
    db.delete(vinc)
    db.commit()
    return None


# =========================================================
# RECIBOS / CONTRIBUIÇÕES
# =========================================================

@router.post("/contribricoes", response_model=ReciboOut, status_code=201, dependencies=[Depends(require_licenca)])
def registrar_contribuicao(
    body: ReciboCreate,
    db: Session = Depends(get_db),
    operador: str = Depends(get_current_username),
) -> ReciboOut:
    contribuinte = db.query(Contribuinte).filter(Contribuinte.id == body.contribuinte_id).first()
    if not contribuinte:
        raise HTTPException(status_code=404, detail="Contribuinte não encontrado.")

    cfg = _obter_config_appf(db)

    numero = _proximo_numero_recibo(db)  # transação IMMEDIATE

    texto_legal = _gerar_texto_legal(cfg)

    r = Recibo(
        numero=numero,
        contribuinte_id=contribuinte.id,
        valor=float(body.valor),
        data_contribuicao=datetime.utcnow(),
        forma_pagamento=(body.forma_pagamento.strip() if body.forma_pagamento else None),
        descricao=(body.descricao.strip() if body.descricao else None),
        nome_presidente=cfg.nome_presidente,
        nome_tesoureiro=cfg.nome_tesoureiro,
        caminho_assinatura_presidente=cfg.caminho_assinatura_presidente,
        caminho_assinatura_tesoureiro=cfg.caminho_assinatura_tesoureiro,
        texto_legal_recibo=texto_legal,
        usuario_emissor=operador,
        cancelado=False,
    )
    db.add(r)

    try:
        db.commit()
    except Exception:
        db.rollback()
        raise HTTPException(status_code=409, detail="Falha ao emitir recibo. Tente novamente.")
    db.refresh(r)
    return r


@router.post("/contribricoes/{recibo_id}/cancelar", response_model=ReciboOut, dependencies=[Depends(require_licenca)])
def cancelar_recibo(
    recibo_id: int,
    body: ReciboCancelamentoIn,
    db: Session = Depends(get_db),
    operador: str = Depends(get_current_username),
) -> ReciboOut:
    r = db.query(Recibo).filter(Recibo.id == recibo_id).first()
    if not r:
        raise HTTPException(status_code=404, detail="Recibo não encontrado.")
    if r.cancelado:
        return r

    motivo = body.motivo.strip()
    if len(motivo) < 10:
        raise HTTPException(status_code=400, detail="Justificativa mínima de 10 caracteres.")

    r.cancelado = True
    r.motivo_cancelamento = motivo
    r.usuario_cancelador = operador
    r.data_cancelamento = datetime.utcnow()

    db.commit()
    db.refresh(r)
    return r


@router.post("/relatorios/contribuinte/enviar-email", dependencies=[Depends(require_licenca)])
def enviar_email_relatorio_contribuinte(
    body: EmailRelatorioIn,
    smtp: SMTPConfigIn,
    bg: BackgroundTasks,
    db: Session = Depends(get_db),
    operador: str = Depends(get_current_username),
):
    contrib = db.query(Contribuinte).filter(Contribuinte.id == body.contribuinte_id).first()
    if not contrib:
        raise HTTPException(status_code=404, detail="Contribuinte não encontrado.")

    cfg = _obter_config_appf(db)

    recibos = (
        db.query(Recibo)
        .filter(Recibo.contribuinte_id == contrib.id)
        .order_by(Recibo.data_contribuicao.asc())
        .all()
    )

    linhas = []
    for rr in recibos:
        linhas.append(
            {
                "numero": rr.numero,
                "data": rr.data_contribuicao.strftime("%d/%m/%Y %H:%M"),
                "valor": f"R$ {float(rr.valor):,.2f}".replace(",", "X").replace(".", ",").replace("X", "."),
                "descricao": (rr.descricao or "") + (" (CANCELADO)" if rr.cancelado else ""),
            }
        )

    html = construir_tabela_html(cfg.razao_social, cfg.cnpj, contrib.nome_completo, linhas)

    disparar_email_background(
        bg,
        host=smtp.host,
        porta=smtp.porta,
        usuario=smtp.usuario,
        senha=smtp.senha,
        usar_starttls=smtp.usar_starttls,
        remetente=smtp.remetente,
        destinatario=body.destinatario_email,
        assunto=body.assunto,
        html=html,
    )

    return {"mensagem": "E-mail enfileirado para envio via SMTP local."}

from typing import List, Optional

