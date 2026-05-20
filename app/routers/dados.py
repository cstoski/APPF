from __future__ import annotations

from io import BytesIO
from typing import List
import json

import pandas as pd
from fastapi import APIRouter, Depends, UploadFile, File, Form, HTTPException
from sqlalchemy.orm import Session
from starlette.responses import StreamingResponse

from app.config.database import get_db
from app.models.core_models import Contribuinte, Recibo
from app.models.sys_models import LogsAuditoriaLGPD
from app.schemas.core_schemas import ImportacaoPreviewOut, ExportacaoOut, ImportacaoPreviewDetalhadoOut
from app.services.contribuinte_busca_service import hash_cpf_busca, normalizar_nome_busca
from app.services.importacao_service import (
    ler_planilha,
    gerar_preview,
    gerar_preview_detalhado,
    normalizar_nome,
)
from app.services.contribuinte_log_service import log_inclusao, log_alteracao
from app.services.seguranca_service import (
    decifrar,
    normalizar_cpf,
    mascarar_cpf,
    get_current_username,
    cifrar,
)
from app.services.licenca_service import require_licenca, require_licenca_escrita

router = APIRouter(prefix="/api/v1/dados", tags=["Importação/Exportação"])


def _log_lgpd(
    db: Session,
    operador: str,
    acao: str,
    entidade: str,
    detalhes: str,
    quantidade: int | None = None,
) -> None:
    log = LogsAuditoriaLGPD(
        operador_username=operador,
        acao=acao,
        entidade=entidade,
        detalhes=detalhes,
        quantidade_registros=quantidade,
    )
    db.add(log)
    db.commit()


# ==========================================================
# PREVIEW
# ==========================================================
@router.post("/importar/preview", response_model=ImportacaoPreviewOut, dependencies=[Depends(require_licenca_escrita)])
def importar_preview(
    arquivo: UploadFile = File(...),
    db: Session = Depends(get_db),
    operador: str = Depends(get_current_username),
) -> ImportacaoPreviewOut:
    b = arquivo.file.read()
    df = ler_planilha(b, arquivo.filename or "arquivo.xlsx")

    existentes = db.query(Contribuinte).filter(Contribuinte.excluido.is_(False)).all()

    cpfs_exist = [c.cpf_busca_hash or "" for c in existentes if c.cpf_busca_hash]

    prev = gerar_preview(df, cpfs_exist, usar_hash_cpf=True)

    _log_lgpd(
        db,
        operador,
        acao="LEITURA_LOTE_IMPORTACAO_PREVIEW",
        entidade="Contribuintes",
        detalhes=f"Preview importação arquivo={arquivo.filename}",
        quantidade=prev.total_linhas,
    )

    return ImportacaoPreviewOut(
        total_linhas=prev.total_linhas,
        novos=prev.novos,
        duplicados=prev.duplicados,
        exemplos_duplicados=prev.exemplos_duplicados,
    )


# ==========================================================
# ✅ APLICAR (PASSO 2 COMPLETO)
# ==========================================================
@router.post("/importar/aplicar", dependencies=[Depends(require_licenca_escrita)])
def importar_aplicar(
    arquivo: UploadFile = File(...),
    modo_duplicados: str = Form(default="PULAR"),
    decisoes_json: str | None = Form(default=None),
    db: Session = Depends(get_db),
    operador: str = Depends(get_current_username),
):
    b = arquivo.file.read()
    df = ler_planilha(b, arquivo.filename or "arquivo.xlsx")

    existentes = db.query(Contribuinte).filter(Contribuinte.excluido.is_(False)).all()

    mapa_cpf = {}

    for c in existentes:
        if c.cpf_busca_hash:
            mapa_cpf[c.cpf_busca_hash] = c

    decisoes: dict[int, str] = {}
    if decisoes_json and decisoes_json.strip():
        try:
            raw = json.loads(decisoes_json)
            if not isinstance(raw, list):
                raise ValueError("decisoes_json deve ser uma lista")
            for d in raw:
                linha = int(d["linha"])
                acao = str(d.get("acao", "")).strip().upper()
                if acao in ("INCLUIR",):
                    acao = "IMPORTAR"
                if acao in ("IGNORAR",):
                    acao = "PULAR"
                decisoes[linha] = acao
        except Exception as exc:
            raise HTTPException(
                status_code=400,
                detail=f"decisoes_json inválido: {exc}",
            ) from exc

    importados = 0
    atualizados = 0
    pulados = 0

    for offset, (_, row) in enumerate(df.iterrows()):
        linha = offset + 2

        nome = str(row.get("nome_completo", "")).strip()
        cpf = normalizar_cpf(str(row.get("cpf", "")))
        email = str(row.get("email", "")).strip()
        telefone = str(row.get("telefone", "")).strip()

        if len(nome) < 3:
            pulados += 1
            continue
        if cpf and len(cpf) != 11:
            pulados += 1
            continue

        nome_norm = normalizar_nome_busca(nome)
        existente = None
        cpf_hash = hash_cpf_busca(cpf) if cpf else None

        if cpf_hash and cpf_hash in mapa_cpf:
            existente = mapa_cpf[cpf_hash]

        acao = decisoes.get(linha)

        if not acao:
            acao = "IMPORTAR" if not existente else (
                "ATUALIZAR" if modo_duplicados == "ATUALIZAR" else "PULAR"
            )

        if acao == "PULAR":
            pulados += 1
            continue

        if acao == "IMPORTAR":
            if existente:
                pulados += 1
                continue

            novo = Contribuinte(
                nome_completo=nome,
                nome_normalizado=nome_norm,
                cpf_cifrado=cifrar(cpf) if cpf else None,
                cpf_busca_hash=cpf_hash,
                email_cifrado=cifrar(email) if email else None,
                telefone_cifrado=cifrar(telefone) if telefone else None,
                consentimento_lgpd=True,
                excluido=False,
            )
            db.add(novo)
            db.flush()
            log_inclusao(operador, novo)
            if cpf_hash:
                mapa_cpf[cpf_hash] = novo
            importados += 1
            continue

        if acao == "ATUALIZAR":
            if not existente:
                novo = Contribuinte(
                    nome_completo=nome,
                    nome_normalizado=nome_norm,
                    cpf_cifrado=cifrar(cpf) if cpf else None,
                    cpf_busca_hash=cpf_hash,
                    email_cifrado=cifrar(email) if email else None,
                    telefone_cifrado=cifrar(telefone) if telefone else None,
                    consentimento_lgpd=True,
                    excluido=False,
                )
                db.add(novo)
                db.flush()
                log_inclusao(operador, novo)
                if cpf_hash:
                    mapa_cpf[cpf_hash] = novo
                importados += 1
                continue

            existente.nome_completo = nome
            existente.nome_normalizado = nome_norm
            if cpf:
                existente.cpf_cifrado = cifrar(cpf)
                existente.cpf_busca_hash = cpf_hash
            if email:
                existente.email_cifrado = cifrar(email)
            elif email == "":
                existente.email_cifrado = None
            if telefone:
                existente.telefone_cifrado = cifrar(telefone)
            elif telefone == "":
                existente.telefone_cifrado = None

            db.flush()
            log_alteracao(operador, existente)
            atualizados += 1
            continue

    db.commit()

    _log_lgpd(
        db,
        operador,
        acao="IMPORTACAO_CONTRIBUINTES_APLICADA",
        entidade="Contribuintes",
        detalhes=f"Importação arquivo={arquivo.filename} modo={modo_duplicados}",
        quantidade=importados + atualizados,
    )

    return {
        "importados": importados,
        "atualizados": atualizados,
        "pulados": pulados,
        "sem_consentimento": 0,
    }


@router.post(
    "/importar/preview-detalhado",
    response_model=ImportacaoPreviewDetalhadoOut,
    dependencies=[Depends(require_licenca_escrita)],
)
def importar_preview_detalhado(
    arquivo: UploadFile = File(...),
    db: Session = Depends(get_db),
    operador: str = Depends(get_current_username),
) -> ImportacaoPreviewDetalhadoOut:
    b = arquivo.file.read()
    df = ler_planilha(b, arquivo.filename or "arquivo.xlsx")

    existentes = db.query(Contribuinte).filter(Contribuinte.excluido.is_(False)).all()
    cpfs_exist = [c.cpf_busca_hash or "" for c in existentes if c.cpf_busca_hash]

    payload = gerar_preview_detalhado(df, cpfs_exist, usar_hash_cpf=True)

    _log_lgpd(
        db,
        operador,
        acao="LEITURA_LOTE_IMPORTACAO_PREVIEW_DETALHADO",
        entidade="Contribuintes",
        detalhes="Preview detalhado importação",
        quantidade=payload["total_linhas"],
    )

    return ImportacaoPreviewDetalhadoOut(**payload)


# ==========================================================
# EXPORTAÇÕES
# ==========================================================
@router.get("/exportar/contribuintes", dependencies=[Depends(require_licenca)])
def exportar_contribuintes(
    db: Session = Depends(get_db),
    operador: str = Depends(get_current_username),
):
    contribs = (
        db.query(Contribuinte)
        .filter(Contribuinte.excluido.is_(False))
        .order_by(Contribuinte.id.asc())
        .all()
    )

    _log_lgpd(
        db,
        operador,
        acao="EXPORTACAO_CONTRIBUINTES",
        entidade="Contribuintes",
        detalhes="Exportação de contribuintes",
        quantidade=len(contribs),
    )

    rows = []
    for c in contribs:
        rows.append(
            {
                "id": c.id,
                "nome_completo": c.nome_completo,
                "cpf": decifrar(c.cpf_cifrado) or "",
                "email": decifrar(c.email_cifrado) if c.email_cifrado else "",
                "telefone": decifrar(c.telefone_cifrado) if c.telefone_cifrado else "",
                "consentimento_lgpd": c.consentimento_lgpd,
                "observacoes": c.observacoes or "",
                "data_criacao": c.data_criacao.strftime("%d/%m/%Y %H:%M:%S"),
                "data_alteracao": c.data_alteracao.strftime("%d/%m/%Y %H:%M:%S"),
            }
        )

    df = pd.DataFrame(rows)
    output = BytesIO()
    with pd.ExcelWriter(output, engine="openpyxl") as writer:
        df.to_excel(writer, index=False, sheet_name="Contribuintes")
    output.seek(0)

    headers = {"Content-Disposition": 'attachment; filename="contribuintes.xlsx"'}

    return StreamingResponse(
        output,
        media_type="application/vnd.openxmlformats-officedocument.spreadsheetml.sheet",
        headers=headers,
    )