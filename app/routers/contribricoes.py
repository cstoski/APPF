from __future__ import annotations

import base64
import binascii
from datetime import date, datetime
from typing import List

from fastapi import APIRouter, Depends, HTTPException, status, BackgroundTasks, Response, Query
from sqlalchemy import select, func, text
from sqlalchemy.orm import Session

from app.config.database import get_db
from app.models.core_models import Contribuinte, Recibo
from app.models.sys_models import ConfigAPPF
from app.schemas.core_schemas import (
    ContribuinteCreate,
    ContribuinteOut,
    ContribuinteBuscaOut,
    ContribuinteUpdate,
    ContribuinteDetalheOut,
    ReciboCreate,
    ReciboOut,
    ReciboListOut,
    ReciboCancelamentoIn,
    EmailRelatorioIn,
    ReciboEmailIn,
    ReciboLogAcaoIn,
)
from app.services.licenca_service import require_licenca, require_licenca_escrita
from app.services.seguranca_service import (
    cifrar,
    decifrar,
    normalizar_cpf,
    mascarar_cpf,
    get_current_username,
)
from app.services.email_log_service import log_email_enfileirado
from app.services.email_service import (
    construir_tabela_html,
    disparar_email_background,
    disparar_email_com_anexo_background,
)
from app.services.recibo_texto_service import gerar_texto_corpo_recibo
from app.services.smtp_config_service import obter_smtp_da_config, validar_smtp_configurado
from app.services.contribuinte_busca_service import hash_cpf_busca, normalizar_nome_busca
from app.services.contribuinte_log_service import (
    log_inclusao,
    log_alteracao,
    log_exclusao,
    log_reativacao,
    cpf_plain_para_validacao,
)
from app.services.recibo_log_service import (
    ACOES_CLIENTE,
    log_acao_cliente,
    log_cancelamento,
    log_emissao,
    log_enviar_email,
    log_visualizacao,
)

router = APIRouter(prefix="/api/v1", tags=["ContribuiÃ§Ãµes e Recibos"])


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


def _proximo_numero_recibo(db: Session) -> str:
    hoje = datetime.utcnow().strftime("%Y%m%d")
    prefixo = hoje

    # lock de escrita cedo (SQLite) para reduzir colisÃµes
    db.execute(text("BEGIN IMMEDIATE"))

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


def _contribuinte_para_detalhe(c: Contribuinte) -> ContribuinteDetalheOut:
    cpf_real = decifrar(c.cpf_cifrado) if c.cpf_cifrado else None
    return ContribuinteDetalheOut(
        id=c.id,
        nome_completo=c.nome_completo,
        cpf=cpf_real or None,
        email=decifrar(c.email_cifrado) if c.email_cifrado else None,
        telefone=decifrar(c.telefone_cifrado) if c.telefone_cifrado else None,
        observacoes=c.observacoes,
    )


def _normalizar_nome(nome: str) -> str:
    return " ".join(nome.strip().split()).casefold()


def _apenas_ativos(q):
    return q.filter(Contribuinte.excluido.is_(False))


def _nome_contribuinte(db: Session, contribuinte_id: int) -> str:
    c = db.query(Contribuinte).filter(Contribuinte.id == contribuinte_id).first()
    return c.nome_completo if c else "?"


def _datetime_da_data_contribuicao(d: date) -> datetime:
    """Data informada pelo operador (meio-dia UTC, sem usar hora do cadastro)."""
    return datetime(d.year, d.month, d.day, 12, 0, 0)


def _validar_data_contribuicao(d: date) -> None:
    if d > datetime.utcnow().date():
        raise HTTPException(
            status_code=400,
            detail="A data da contribuição não pode ser posterior à data atual.",
        )


def _validar_cpf_unico(db: Session, cpf_norm: str, ignorar_id: int | None = None) -> None:
    if not cpf_norm:
        return
    h = hash_cpf_busca(cpf_norm)
    if not h:
        return
    q = _apenas_ativos(db.query(Contribuinte)).filter(Contribuinte.cpf_busca_hash == h)
    if ignorar_id is not None:
        q = q.filter(Contribuinte.id != ignorar_id)
    if q.first():
        raise HTTPException(
            status_code=400,
            detail="Já existe contribuinte ativo com este CPF. Não é permitido cadastrar nome e CPF iguais.",
        )


def _validar_duplicatas_contribuinte(
    db: Session,
    cpf: str | None,
    ignorar_id: int | None = None,
) -> None:
    cpf_norm = normalizar_cpf(cpf or "")
    if cpf_norm:
        if len(cpf_norm) != 11:
            raise HTTPException(
                status_code=400,
                detail="CPF inválido. Informe 11 dígitos ou deixe em branco.",
            )
        _validar_cpf_unico(db, cpf_norm, ignorar_id=ignorar_id)


def _contribuinte_para_busca(c: Contribuinte) -> ContribuinteBuscaOut:
    cpf_real = decifrar(c.cpf_cifrado) if c.cpf_cifrado else ""
    cpf_exib = mascarar_cpf(cpf_real) if cpf_real else ""
    return ContribuinteBuscaOut(
        id=c.id,
        nome_completo=c.nome_completo,
        cpf=cpf_exib,
        email=decifrar(c.email_cifrado) if c.email_cifrado else None,
        telefone=decifrar(c.telefone_cifrado) if c.telefone_cifrado else None,
        excluido=bool(c.excluido),
    )


def _aplicar_dados_contribuinte(c: Contribuinte, data: ContribuinteCreate | ContribuinteUpdate) -> None:
    cpf_norm = normalizar_cpf(data.cpf or "")
    if cpf_norm and len(cpf_norm) != 11:
        raise HTTPException(
            status_code=400,
            detail="CPF inválido. Informe 11 dígitos ou deixe em branco.",
        )
    c.nome_completo = data.nome_completo.strip()
    c.nome_normalizado = normalizar_nome_busca(c.nome_completo)
    c.cpf_cifrado = cifrar(cpf_norm) if cpf_norm else None
    c.cpf_busca_hash = hash_cpf_busca(cpf_norm)
    c.email_cifrado = cifrar(data.email) if data.email else None
    c.telefone_cifrado = cifrar(data.telefone) if data.telefone else None
    c.observacoes = data.observacoes.strip() if data.observacoes else None


@router.get("/contribuintes", response_model=List[ContribuinteBuscaOut], dependencies=[Depends(require_licenca)])
def listar_contribuintes(
    excluidos: bool = Query(False, description="Se true, lista apenas contribuintes excluídos."),
    db: Session = Depends(get_db),
) -> List[ContribuinteBuscaOut]:
    rows = (
        db.query(Contribuinte)
        .filter(Contribuinte.excluido.is_(excluidos))
        .order_by(Contribuinte.nome_completo.asc())
        .limit(5000)
        .all()
    )
    return [_contribuinte_para_busca(c) for c in rows]


@router.get("/contribuintes/buscar", response_model=List[ContribuinteBuscaOut], dependencies=[Depends(require_licenca)])
def buscar_contribuintes(termo: str, db: Session = Depends(get_db)) -> List[ContribuinteBuscaOut]:
    t = termo.strip()
    if not t:
        return []

    candidatos = (
        _apenas_ativos(db.query(Contribuinte))
        .filter(Contribuinte.nome_completo.ilike(f"%{t}%"))
        .limit(30)
        .all()
    )

    digits = normalizar_cpf(t)

    if not candidatos and digits and len(digits) == 11:
        h = hash_cpf_busca(digits)
        if h:
            candidatos = (
                _apenas_ativos(db.query(Contribuinte))
                .filter(Contribuinte.cpf_busca_hash == h)
                .limit(5)
                .all()
            )

    return [_contribuinte_para_busca(c) for c in candidatos[:30]]


@router.get(
    "/contribuintes/{contribuinte_id}",
    response_model=ContribuinteDetalheOut,
    dependencies=[Depends(require_licenca_escrita)],
)
def obter_contribuinte(contribuinte_id: int, db: Session = Depends(get_db)) -> ContribuinteDetalheOut:
    c = (
        _apenas_ativos(db.query(Contribuinte))
        .filter(Contribuinte.id == contribuinte_id)
        .first()
    )
    if not c:
        raise HTTPException(status_code=404, detail="Contribuinte não encontrado.")
    return _contribuinte_para_detalhe(c)


@router.post("/contribuintes", response_model=ContribuinteOut, status_code=201, dependencies=[Depends(require_licenca_escrita)])
def criar_contribuinte(
    data: ContribuinteCreate,
    db: Session = Depends(get_db),
    operador: str = Depends(get_current_username),
) -> ContribuinteOut:
    if data.consentimento_lgpd is False:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail="O cadastro exige o consentimento do contribuinte conforme LGPD.",
        )

    _validar_duplicatas_contribuinte(db, data.cpf)

    c = Contribuinte(consentimento_lgpd=bool(data.consentimento_lgpd), excluido=False)
    _aplicar_dados_contribuinte(c, data)
    db.add(c)
    db.commit()
    db.refresh(c)
    log_inclusao(operador, c)
    return c


@router.put(
    "/contribuintes/{contribuinte_id}",
    response_model=ContribuinteDetalheOut,
    dependencies=[Depends(require_licenca_escrita)],
)
def atualizar_contribuinte(
    contribuinte_id: int,
    data: ContribuinteUpdate,
    db: Session = Depends(get_db),
    operador: str = Depends(get_current_username),
) -> ContribuinteDetalheOut:
    c = (
        _apenas_ativos(db.query(Contribuinte))
        .filter(Contribuinte.id == contribuinte_id)
        .first()
    )
    if not c:
        raise HTTPException(status_code=404, detail="Contribuinte não encontrado.")

    _validar_duplicatas_contribuinte(db, data.cpf, ignorar_id=contribuinte_id)
    _aplicar_dados_contribuinte(c, data)
    db.commit()
    db.refresh(c)
    log_alteracao(operador, c)
    return _contribuinte_para_detalhe(c)


@router.post(
    "/contribuintes/{contribuinte_id}/reativar",
    response_model=ContribuinteDetalheOut,
    dependencies=[Depends(require_licenca_escrita)],
)
def reativar_contribuinte(
    contribuinte_id: int,
    db: Session = Depends(get_db),
    operador: str = Depends(get_current_username),
) -> ContribuinteDetalheOut:
    c = (
        db.query(Contribuinte)
        .filter(Contribuinte.id == contribuinte_id, Contribuinte.excluido.is_(True))
        .first()
    )
    if not c:
        raise HTTPException(status_code=404, detail="Contribuinte excluído não encontrado.")

    _validar_duplicatas_contribuinte(
        db,
        c.nome_completo,
        cpf_plain_para_validacao(c),
        ignorar_id=contribuinte_id,
    )
    c.excluido = False
    db.commit()
    db.refresh(c)
    log_reativacao(operador, c)
    return _contribuinte_para_detalhe(c)


@router.delete(
    "/contribuintes/{contribuinte_id}",
    status_code=204,
    response_class=Response,
    dependencies=[Depends(require_licenca_escrita)],
)
def excluir_contribuinte(
    contribuinte_id: int,
    db: Session = Depends(get_db),
    operador: str = Depends(get_current_username),
) -> Response:
    c = (
        _apenas_ativos(db.query(Contribuinte))
        .filter(Contribuinte.id == contribuinte_id)
        .first()
    )
    if not c:
        raise HTTPException(status_code=404, detail="Contribuinte não encontrado.")

    c.excluido = True
    db.commit()
    log_exclusao(operador, c)
    return Response(status_code=204)


# =========================================================
# RECIBOS / CONTRIBUIÃ‡Ã•ES
# =========================================================

@router.get("/contribricoes", response_model=List[ReciboListOut], dependencies=[Depends(require_licenca)])
def listar_recibos(
    contribuinte_id: int = Query(..., description="ID do contribuinte"),
    db: Session = Depends(get_db),
) -> List[ReciboListOut]:
    contribuinte = db.query(Contribuinte).filter(Contribuinte.id == contribuinte_id).first()
    if not contribuinte:
        raise HTTPException(status_code=404, detail="Contribuinte não encontrado.")

    rows = (
        db.query(Recibo)
        .filter(Recibo.contribuinte_id == contribuinte_id)
        .order_by(Recibo.data_contribuicao.desc())
        .limit(500)
        .all()
    )
    return rows


@router.get("/contribricoes/{recibo_id}", response_model=ReciboOut, dependencies=[Depends(require_licenca)])
def obter_recibo(
    recibo_id: int,
    db: Session = Depends(get_db),
    operador: str = Depends(get_current_username),
) -> ReciboOut:
    r = db.query(Recibo).filter(Recibo.id == recibo_id).first()
    if not r:
        raise HTTPException(status_code=404, detail="Recibo não encontrado.")
    log_visualizacao(operador, r, _nome_contribuinte(db, r.contribuinte_id))
    return r


@router.post("/contribricoes", response_model=ReciboOut, status_code=201, dependencies=[Depends(require_licenca_escrita)])
def registrar_contribuicao(
    body: ReciboCreate,
    db: Session = Depends(get_db),
    operador: str = Depends(get_current_username),
) -> ReciboOut:
    contribuinte = (
        _apenas_ativos(db.query(Contribuinte))
        .filter(Contribuinte.id == body.contribuinte_id)
        .first()
    )
    if not contribuinte:
        raise HTTPException(status_code=404, detail="Contribuinte nÃ£o encontrado.")

    _validar_data_contribuicao(body.data_contribuicao)

    cfg = _obter_config_appf(db)

    numero = _proximo_numero_recibo(db)  # transaÃ§Ã£o IMMEDIATE

    data_contrib = _datetime_da_data_contribuicao(body.data_contribuicao)
    cpf_real = decifrar(contribuinte.cpf_cifrado) if contribuinte.cpf_cifrado else None
    texto_legal = gerar_texto_corpo_recibo(
        contribuinte.nome_completo, cpf_real, float(body.valor), data_contrib
    )

    r = Recibo(
        numero=numero,
        contribuinte_id=contribuinte.id,
        valor=float(body.valor),
        data_contribuicao=data_contrib,
        forma_pagamento=(body.forma_pagamento.strip() if body.forma_pagamento else None),
        descricao=(body.descricao.strip() if body.descricao else None),
        razao_social=cfg.razao_social or "",
        cnpj=cfg.cnpj or "",
        endereco=cfg.endereco or "",
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
    log_emissao(operador, r, contribuinte.nome_completo)
    return r


@router.post("/contribricoes/{recibo_id}/cancelar", response_model=ReciboOut, dependencies=[Depends(require_licenca_escrita)])
def cancelar_recibo(
    recibo_id: int,
    body: ReciboCancelamentoIn,
    db: Session = Depends(get_db),
    operador: str = Depends(get_current_username),
) -> ReciboOut:
    r = db.query(Recibo).filter(Recibo.id == recibo_id).first()
    if not r:
        raise HTTPException(status_code=404, detail="Recibo nÃ£o encontrado.")
    if r.cancelado:
        return r

    motivo = body.motivo.strip()
    if len(motivo) < 10:
        raise HTTPException(status_code=400, detail="Justificativa mÃ­nima de 10 caracteres.")

    r.cancelado = True
    r.motivo_cancelamento = motivo
    r.usuario_cancelador = operador
    r.data_cancelamento = datetime.utcnow()

    db.commit()
    db.refresh(r)
    log_cancelamento(operador, r, _nome_contribuinte(db, r.contribuinte_id), motivo)
    return r


@router.post("/contribricoes/{recibo_id}/registrar-acao", dependencies=[Depends(require_licenca_escrita)])
def registrar_acao_recibo(
    recibo_id: int,
    body: ReciboLogAcaoIn,
    db: Session = Depends(get_db),
    operador: str = Depends(get_current_username),
):
    acao = body.acao.strip().upper()
    if acao not in ACOES_CLIENTE:
        raise HTTPException(
            status_code=400,
            detail=f"Ação inválida. Permitidas: {', '.join(sorted(ACOES_CLIENTE))}.",
        )

    r = db.query(Recibo).filter(Recibo.id == recibo_id).first()
    if not r:
        raise HTTPException(status_code=404, detail="Recibo não encontrado.")

    detalhes = (body.detalhes or "").strip()
    log_acao_cliente(operador, r, _nome_contribuinte(db, r.contribuinte_id), acao, detalhes)
    return {"mensagem": "Ação registrada no log."}


@router.post("/contribricoes/{recibo_id}/enviar-email", dependencies=[Depends(require_licenca_escrita)])
def enviar_email_recibo(
    recibo_id: int,
    body: ReciboEmailIn,
    bg: BackgroundTasks,
    db: Session = Depends(get_db),
    operador: str = Depends(get_current_username),
):
    recibo = db.query(Recibo).filter(Recibo.id == recibo_id).first()
    if not recibo:
        raise HTTPException(status_code=404, detail="Recibo não encontrado.")
    if recibo.cancelado:
        raise HTTPException(
            status_code=400,
            detail="Recibos cancelados não podem ser enviados por e-mail.",
        )

    try:
        pdf_bytes = base64.b64decode(body.pdf_base64, validate=True)
    except (binascii.Error, ValueError):
        raise HTTPException(status_code=400, detail="PDF inválido.") from None

    if not pdf_bytes.startswith(b"%PDF"):
        raise HTTPException(status_code=400, detail="O anexo não é um PDF válido.")

    cfg = _obter_config_appf(db)
    smtp = obter_smtp_da_config(cfg)
    validar_smtp_configurado(smtp)

    nome_contrib = _nome_contribuinte(db, recibo.contribuinte_id)
    log_ctx = {
        "operador": operador,
        "tipo": "RECIBO",
        "destinatario": body.destinatario_email,
        "remetente": smtp.remetente,
        "assunto": body.assunto,
        "recibo_id": recibo.id,
        "recibo_numero": recibo.numero,
        "contribuinte_id": recibo.contribuinte_id,
        "contribuinte_nome": nome_contrib,
        "smtp_host": smtp.host,
    }
    log_email_enfileirado(**log_ctx)
    disparar_email_com_anexo_background(
        bg,
        log_ctx=log_ctx,
        host=smtp.host,
        porta=smtp.porta,
        usuario=smtp.usuario,
        senha=smtp.senha,
        usar_starttls=smtp.usar_starttls,
        remetente=smtp.remetente,
        destinatario=body.destinatario_email,
        assunto=body.assunto,
        corpo_texto=body.corpo_texto,
        anexo_nome=body.nome_anexo,
        anexo_bytes=pdf_bytes,
    )

    log_enviar_email(operador, recibo, nome_contrib, body.destinatario_email)

    return {"mensagem": "E-mail com recibo em PDF enfileirado para envio."}


@router.post("/relatorios/contribuinte/enviar-email", dependencies=[Depends(require_licenca_escrita)])
def enviar_email_relatorio_contribuinte(
    body: EmailRelatorioIn,
    bg: BackgroundTasks,
    db: Session = Depends(get_db),
    operador: str = Depends(get_current_username),
):
    contrib = (
        _apenas_ativos(db.query(Contribuinte))
        .filter(Contribuinte.id == body.contribuinte_id)
        .first()
    )
    if not contrib:
        raise HTTPException(status_code=404, detail="Contribuinte nÃ£o encontrado.")

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

    smtp = obter_smtp_da_config(cfg)
    validar_smtp_configurado(smtp)

    log_ctx = {
        "operador": operador,
        "tipo": "RELATORIO",
        "destinatario": body.destinatario_email,
        "remetente": smtp.remetente,
        "assunto": body.assunto,
        "contribuinte_id": contrib.id,
        "contribuinte_nome": contrib.nome_completo,
        "smtp_host": smtp.host,
    }
    log_email_enfileirado(**log_ctx)
    disparar_email_background(
        bg,
        log_ctx=log_ctx,
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
