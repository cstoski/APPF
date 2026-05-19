from __future__ import annotations

from io import BytesIO
from typing import List

import pandas as pd
from fastapi import APIRouter, Depends, UploadFile, File, HTTPException
from sqlalchemy.orm import Session
from starlette.responses import StreamingResponse

from app.config.database import get_db
from app.models.core_models import Contribuinte, Aluno, AlunoResponsavel, Recibo
from app.models.sys_models import LogsAuditoriaLGPD
from app.schemas.core_schemas import ImportacaoPreviewOut, ExportacaoOut
from app.services.importacao_service import ler_planilha, gerar_preview
from app.services.seguranca_service import decifrar, normalizar_cpf, get_current_username
from app.services.licenca_service import require_licenca

router = APIRouter(prefix="/api/v1/dados", tags=["Importação/Exportação"])


def _log_lgpd(db: Session, operador: str, acao: str, entidade: str, detalhes: str, quantidade: int | None = None) -> None:
    log = LogsAuditoriaLGPD(
        operador_username=operador,
        acao=acao,
        entidade=entidade,
        detalhes=detalhes,
        quantidade_registros=quantidade,
    )
    db.add(log)
    db.commit()


@router.post("/importar/preview", response_model=ImportacaoPreviewOut, dependencies=[Depends(require_licenca)])
def importar_preview(
    arquivo: UploadFile = File(...),
    db: Session = Depends(get_db),
    operador: str = Depends(get_current_username),
) -> ImportacaoPreviewOut:
    b = arquivo.file.read()
    df = ler_planilha(b, arquivo.filename or "arquivo.xlsx")

    # CPFs existentes (decifrados)
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


@router.get("/exportar/contribuintes", dependencies=[Depends(require_licenca)])
def exportar_contribuintes(
    db: Session = Depends(get_db),
    operador: str = Depends(get_current_username),
):
    contribs = db.query(Contribuinte).order_by(Contribuinte.id.asc()).all()

    # LOG LGPD
    _log_lgpd(
        db,
        operador,
        acao="EXPORTACAO_CONTRIBUINTES",
        entidade="Contribuintes",
        detalhes="Exportação de contribuintes (decifrando CPF/email/telefone em tempo real)",
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
    return StreamingResponse(output, media_type="application/vnd.openxmlformats-officedocument.spreadsheetml.sheet", headers=headers)


@router.get("/exportar/vinculos", dependencies=[Depends(require_licenca)])
def exportar_vinculos(
    db: Session = Depends(get_db),
    operador: str = Depends(get_current_username),
):
    vincs = db.query(AlunoResponsavel).order_by(AlunoResponsavel.id.asc()).all()

    _log_lgpd(
        db,
        operador,
        acao="EXPORTACAO_VINCULOS",
        entidade="AlunosResponsaveis",
        detalhes="Exportação de vínculos aluno-responsável",
        quantidade=len(vincs),
    )

    rows = []
    for v in vincs:
        aluno = db.query(Aluno).filter(Aluno.id == v.aluno_id).first()
        resp = db.query(Contribuinte).filter(Contribuinte.id == v.contribuinte_id).first()
        rows.append(
            {
                "vinculo_id": v.id,
                "aluno_id": v.aluno_id,
                "aluno_nome": aluno.nome_completo if aluno else "",
                "matricula": aluno.matricula if aluno else "",
                "turma": aluno.turma if aluno else "",
                "contribuinte_id": v.contribuinte_id,
                "contribuinte_nome": resp.nome_completo if resp else "",
                "cpf_responsavel": (decifrar(resp.cpf_cifrado) if resp else ""),
                "parentesco": v.parentesco or "",
                "data_criacao": v.data_criacao.strftime("%d/%m/%Y %H:%M:%S"),
                "data_alteracao": v.data_alteracao.strftime("%d/%m/%Y %H:%M:%S"),
            }
        )

    df = pd.DataFrame(rows)
    output = BytesIO()
    with pd.ExcelWriter(output, engine="openpyxl") as writer:
        df.to_excel(writer, index=False, sheet_name="Vinculos")
    output.seek(0)

    headers = {"Content-Disposition": 'attachment; filename="vinculos.xlsx"'}
    return StreamingResponse(output, media_type="application/vnd.openxmlformats-officedocument.spreadsheetml.sheet", headers=headers)