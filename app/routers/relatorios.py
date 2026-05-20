from __future__ import annotations

from datetime import date

from fastapi import APIRouter, Depends, HTTPException, Query
from sqlalchemy.orm import Session

from app.config.database import get_db
from app.models.core_models import Contribuinte
from app.models.sys_models import ConfigAPPF
from app.routers.contribricoes import _apenas_ativos, _contribuinte_para_detalhe, _obter_config_appf
from app.schemas.core_schemas import (
    RelatorioContribuinteOut,
    RelatorioFinanceiroOut,
    RelatorioInstituicaoOut,
)
from app.services.licenca_service import require_licenca
from app.services.relatorio_service import (
    agregar_totais_mensais,
    buscar_recibos_contribuinte,
    buscar_recibos_financeiro,
    calcular_resumo,
    intervalo_financeiro,
    parse_data_fim,
    parse_data_inicio,
    rotulo_periodo_contribuinte,
)

router = APIRouter(prefix="/api/v1/relatorios", tags=["Relatórios"])


def _instituicao_relatorio(cfg: ConfigAPPF) -> RelatorioInstituicaoOut:
    return RelatorioInstituicaoOut(
        razao_social=cfg.razao_social or "",
        cnpj=cfg.cnpj or "",
        nome_presidente=cfg.nome_presidente or "",
        nome_tesoureiro=cfg.nome_tesoureiro or "",
        caminho_assinatura_presidente=cfg.caminho_assinatura_presidente or "",
        caminho_assinatura_tesoureiro=cfg.caminho_assinatura_tesoureiro or "",
    )


@router.get("/contribuinte", response_model=RelatorioContribuinteOut, dependencies=[Depends(require_licenca)])
def relatorio_contribuinte(
    contribuinte_id: int = Query(..., description="ID do contribuinte"),
    data_inicio: date = Query(..., description="Início do período (AAAA-MM-DD)"),
    data_fim: date = Query(..., description="Fim do período (AAAA-MM-DD)"),
    incluir_cancelados: bool = Query(False, description="Incluir recibos cancelados na listagem"),
    db: Session = Depends(get_db),
) -> RelatorioContribuinteOut:
    if data_fim < data_inicio:
        raise HTTPException(status_code=400, detail="A data final deve ser igual ou posterior à data inicial.")

    contribuinte = (
        _apenas_ativos(db.query(Contribuinte))
        .filter(Contribuinte.id == contribuinte_id)
        .first()
    )
    if not contribuinte:
        raise HTTPException(status_code=404, detail="Contribuinte não encontrado.")

    inicio = parse_data_inicio(data_inicio)
    fim = parse_data_fim(data_fim)
    detalhe = _contribuinte_para_detalhe(contribuinte)
    cfg = _obter_config_appf(db)

    linhas = buscar_recibos_contribuinte(db, contribuinte_id, inicio, fim, incluir_cancelados)
    resumo = calcular_resumo(linhas)

    return RelatorioContribuinteOut(
        titulo="Informe de contribuições voluntárias",
        contribuinte_id=contribuinte.id,
        contribuinte_nome=contribuinte.nome_completo,
        contribuinte_cpf=detalhe.cpf,
        periodo_label=rotulo_periodo_contribuinte(inicio, fim),
        data_inicio=inicio,
        data_fim=fim,
        instituicao=_instituicao_relatorio(cfg),
        linhas=linhas,
        resumo=resumo,
    )


@router.get("/financeiro", response_model=RelatorioFinanceiroOut, dependencies=[Depends(require_licenca)])
def relatorio_financeiro(
    periodo: str = Query(..., pattern="^(mensal|semestral|anual)$"),
    ano: int = Query(..., ge=2000, le=2100),
    mes: int | None = Query(None, ge=1, le=12, description="Obrigatório para período mensal"),
    semestre: int | None = Query(None, ge=1, le=2, description="Obrigatório para período semestral"),
    incluir_cancelados: bool = Query(False),
    db: Session = Depends(get_db),
) -> RelatorioFinanceiroOut:
    try:
        if periodo == "mensal" and mes is None:
            raise ValueError("Informe o mês para relatório mensal.")
        if periodo == "semestral" and semestre is None:
            raise ValueError("Informe o semestre (1 ou 2) para relatório semestral.")
        inicio, fim, rotulo = intervalo_financeiro(periodo, ano, mes=mes, semestre=semestre)
    except ValueError as exc:
        raise HTTPException(status_code=400, detail=str(exc)) from exc

    cfg = _obter_config_appf(db)
    linhas = buscar_recibos_financeiro(db, inicio, fim, incluir_cancelados)
    resumo = calcular_resumo(linhas)

    titulos = {
        "mensal": "Relatório financeiro mensal",
        "semestral": "Relatório financeiro semestral",
        "anual": "Relatório financeiro anual",
    }

    totais_mensais = agregar_totais_mensais(linhas, ano) if periodo == "anual" else None

    return RelatorioFinanceiroOut(
        titulo=titulos.get(periodo, "Relatório financeiro"),
        periodo=periodo,
        periodo_label=rotulo,
        data_inicio=inicio,
        data_fim=fim,
        instituicao=_instituicao_relatorio(cfg),
        linhas=linhas,
        resumo=resumo,
        totais_mensais=totais_mensais,
    )
