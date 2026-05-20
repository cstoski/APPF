from __future__ import annotations

from io import BytesIO
from typing import List
import json

import pandas as pd
from fastapi import APIRouter, Depends, UploadFile, File, HTTPException
from sqlalchemy.orm import Session
from starlette.responses import StreamingResponse

from app.config.database import get_db
from app.models.core_models import Contribuinte, Aluno, AlunoResponsavel, Recibo
from app.models.sys_models import LogsAuditoriaLGPD
from app.schemas.core_schemas import ImportacaoPreviewOut, ExportacaoOut, ImportacaoPreviewDetalhadoOut
from app.services.importacao_service import ler_planilha, gerar_preview, gerar_preview_detalhado
from app.services.seguranca_service import (
    decifrar,
    normalizar_cpf,
    mascarar_cpf,
    get_current_username,
    cifrar,
)
from app.services.licenca_service import require_licenca

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
@router.post("/importar/preview", response_model=ImportacaoPreviewOut, dependencies=[Depends(require_licenca)])
def importar_preview(
    arquivo: UploadFile = File(...),
    db: Session = Depends(get_db),
    operador: str = Depends(get_current_username),
) -> ImportacaoPreviewOut:
    b = arquivo.file.read()
    df = ler_planilha(b, arquivo.filename or "arquivo.xlsx")

    existentes = db.query(Contribuinte).all()

    cpfs_exist = []
    nomes_exist = []

    for c in existentes:
        cpfs_exist.append(normalizar_cpf(decifrar(c.cpf_cifrado) or ""))
        nomes_exist.append(c.nome_completo.strip().lower())

    prev = gerar_preview(df, cpfs_exist, nomes_exist)

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
@router.post("/importar/aplicar", dependencies=[Depends(require_licenca)])
def importar_aplicar(
    arquivo: UploadFile = File(...),
    modo_duplicados: str = "PULAR",  # PULAR | ATUALIZAR
    decisoes_json: str | None = None,
    db: Session = Depends(get_db),
    operador: str = Depends(get_current_username),
):
    b = arquivo.file.read()
    df = ler_planilha(b, arquivo.filename or "arquivo.xlsx")

    existentes = db.query(Contribuinte).all()

    mapa_cpf = {}
    mapa_nome = {}

    for c in existentes:
        cpf_dec = normalizar_cpf(decifrar(c.cpf_cifrado) or "")
        if cpf_dec:
            mapa_cpf[cpf_dec] = c

        nome_norm = c.nome_completo.strip().lower()
        mapa_nome[nome_norm] = c

    decisoes = {}
    if decisoes_json:
        try:
            raw = json.loads(decisoes_json)
            for d in raw:
                linha = int(d["linha"])
                decisoes[linha] = d["acao"]
        except Exception:
            raise HTTPException(status_code=400, detail="decisoes_json inválido")

    importados = 0
    atualizados = 0
    pulados = 0
    sem_consentimento = 0

    for idx, row in df.iterrows():
        linha = idx + 2

        nome = str(row.get("nome_completo", "")).strip()
        cpf = normalizar_cpf(str(row.get("cpf", "")))
        email = str(row.get("email", "")).strip()
        telefone = str(row.get("telefone", "")).strip()
        observacoes = str(row.get("observacoes", "")).strip()
        consentimento = bool(row.get("consentimento_lgpd", False))

        if not consentimento:
            sem_consentimento += 1
            continue

        existente = None

        if cpf and cpf in mapa_cpf:
            existente = mapa_cpf[cpf]
            status = "DUP_CPF"
        elif nome.lower() in mapa_nome:
            existente = mapa_nome[nome.lower()]
            status = "DUP_NOME"
        else:
            status = "NOVO"

        acao = decisoes.get(linha)

        if not acao:
            if status == "NOVO":
                acao = "IMPORTAR"
            else:
                acao = "ATUALIZAR" if modo_duplicados == "ATUALIZAR" else "PULAR"

        # ===== EXECUÇÃO =====

        if acao == "PULAR":
            pulados += 1
            continue

        if acao == "IMPORTAR":
            if existente:
                pulados += 1
                continue

            novo = Contribuinte(
                nome_completo=nome,
                cpf_cifrado=cifrar(cpf),
                email_cifrado=cifrar(email) if email else None,
                telefone_cifrado=cifrar(telefone) if telefone else None,
                consentimento_lgpd=True,
                observacoes=observacoes or None,
            )
            db.add(novo)
            importados += 1
            continue

        if acao == "ATUALIZAR":
            if not existente:
                novo = Contribuinte(
                    nome_completo=nome,
                    cpf_cifrado=cifrar(cpf),
                    email_cifrado=cifrar(email) if email else None,
                    telefone_cifrado=cifrar(telefone) if telefone else None,
                    consentimento_lgpd=True,
                )
                db.add(novo)
                importados += 1
                continue

            existente.nome_completo = nome

            if email:
                existente.email_cifrado = cifrar(email)
            if telefone:
                existente.telefone_cifrado = cifrar(telefone)
            if observacoes:
                existente.observacoes = observacoes

            existente.consentimento_lgpd = True
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
        "sem_consentimento": sem_consentimento,
    }


@router.post(
    "/importar/preview-detalhado",
    response_model=ImportacaoPreviewDetalhadoOut,
    dependencies=[Depends(require_licenca)],
)
def importar_preview_detalhado(
    arquivo: UploadFile = File(...),
    db: Session = Depends(get_db),
    operador: str = Depends(get_current_username),
) -> ImportacaoPreviewDetalhadoOut:
    b = arquivo.file.read()
    df = ler_planilha(b, arquivo.filename or "arquivo.xlsx")

    existentes = db.query(Contribuinte).all()
    cpfs_exist = []
    nomes_exist = []

    for c in existentes:
        cpfs_exist.append(normalizar_cpf(decifrar(c.cpf_cifrado) or ""))
        nomes_exist.append(c.nome_completo.strip().lower())

    payload = gerar_preview_detalhado(df, cpfs_exist, nomes_exist)

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
    contribs = db.query(Contribuinte).order_by(Contribuinte.id.asc()).all()

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