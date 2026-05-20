from __future__ import annotations

from datetime import datetime

from fastapi import APIRouter, Depends, Query
from sqlalchemy import func, text
from sqlalchemy.orm import Session

from app.config.database import get_db
from app.models.core_models import Contribuinte, Recibo
from app.routers.contribricoes import _obter_config_appf
from app.schemas.dashboard_schemas import DashboardMesContribOut, DashboardResumoOut
from app.services.licenca_service import require_licenca, licenca_operacional

_MESES_PT = (
    "",
    "janeiro",
    "fevereiro",
    "março",
    "abril",
    "maio",
    "junho",
    "julho",
    "agosto",
    "setembro",
    "outubro",
    "novembro",
    "dezembro",
)

router = APIRouter(prefix="/api/v1/dashboard", tags=["Dashboard"])


def _inicio_mes_utc(ano: int, mes: int) -> datetime:
    return datetime(ano, mes, 1)


def _inicio_proximo_mes_utc(ano: int, mes: int) -> datetime:
    if mes == 12:
        return datetime(ano + 1, 1, 1)
    return datetime(ano, mes + 1, 1)


def _inicio_proximo_ano_utc(ano: int) -> datetime:
    return datetime(ano + 1, 1, 1)


def _totais_recibos_ano_agrupado(db: Session, ano: int) -> dict[int, tuple[float, int]]:
    """Uma consulta SQL para os 12 meses do ano (em vez de 12 idas ao banco)."""
    ini = _inicio_mes_utc(ano, 1)
    fim = _inicio_proximo_ano_utc(ano)
    rows = db.execute(
        text(
            """
            SELECT CAST(strftime('%m', data_contribuicao) AS INTEGER) AS mes,
                   COUNT(id),
                   COALESCE(SUM(valor), 0)
            FROM recibos
            WHERE cancelado = 0
              AND data_contribuicao >= :ini
              AND data_contribuicao < :fim
            GROUP BY mes
            """
        ),
        {"ini": ini, "fim": fim},
    ).fetchall()
    out: dict[int, tuple[float, int]] = {}
    for mes, qtd, val in rows:
        out[int(mes)] = (float(val or 0), int(qtd or 0))
    return out


def _totais_recibos_mes(db: Session, a: int, m: int) -> tuple[float, int]:
    ini = _inicio_mes_utc(a, m)
    fim = _inicio_proximo_mes_utc(a, m)
    row = (
        db.query(func.count(Recibo.id), func.coalesce(func.sum(Recibo.valor), 0.0))
        .filter(
            Recibo.cancelado.is_(False),
            Recibo.data_contribuicao >= ini,
            Recibo.data_contribuicao < fim,
        )
        .one()
    )
    return float(row[1] or 0.0), int(row[0] or 0)


def _montar_resumo_dashboard(db: Session, ano: int, mes: int) -> DashboardResumoOut:
    inicio_mes = _inicio_mes_utc(ano, mes)
    fim_mes = _inicio_proximo_mes_utc(ano, mes)
    inicio_ano = datetime(ano, 1, 1)
    fim_ano = _inicio_proximo_ano_utc(ano)

    nome_mes = _MESES_PT[mes]
    nome_mes_fmt = nome_mes[0].upper() + nome_mes[1:] if nome_mes else ""
    mes_label = f"{nome_mes_fmt} de {ano}"

    contrib_ativos = (
        db.query(func.count(Contribuinte.id))
        .filter(Contribuinte.excluido.is_(False))
        .scalar()
        or 0
    )
    contrib_excl = (
        db.query(func.count(Contribuinte.id))
        .filter(Contribuinte.excluido.is_(True))
        .scalar()
        or 0
    )

    rec_ativos = db.query(func.count(Recibo.id)).filter(Recibo.cancelado.is_(False)).scalar() or 0
    rec_cancel = db.query(func.count(Recibo.id)).filter(Recibo.cancelado.is_(True)).scalar() or 0

    q_mes = (
        db.query(func.count(Recibo.id), func.coalesce(func.sum(Recibo.valor), 0.0))
        .filter(
            Recibo.cancelado.is_(False),
            Recibo.data_contribuicao >= inicio_mes,
            Recibo.data_contribuicao < fim_mes,
        )
    )
    row_mes = q_mes.one()
    qtd_mes = int(row_mes[0] or 0)
    valor_mes = float(row_mes[1] or 0.0)

    q_ano = (
        db.query(func.count(Recibo.id), func.coalesce(func.sum(Recibo.valor), 0.0))
        .filter(
            Recibo.cancelado.is_(False),
            Recibo.data_contribuicao >= inicio_ano,
            Recibo.data_contribuicao < fim_ano,
        )
    )
    row_ano = q_ano.one()
    qtd_ano = int(row_ano[0] or 0)
    valor_ano = float(row_ano[1] or 0.0)

    v_dec_ant, q_dec_ant = _totais_recibos_mes(db, ano - 1, 12)
    por_mes = _totais_recibos_ano_agrupado(db, ano)
    mes_a_mes: list[DashboardMesContribOut] = []
    for mnum in range(1, 13):
        val_m, qtd_m = por_mes.get(mnum, (0.0, 0))
        nome = _MESES_PT[mnum]
        label_fmt = nome[0].upper() + nome[1:] if nome else ""
        mes_a_mes.append(
            DashboardMesContribOut(
                mes=mnum,
                mes_label=label_fmt,
                valor_total=round(float(val_m), 2),
                quantidade=qtd_m,
            )
        )

    mes_a_mes_enriquecido: list[DashboardMesContribOut] = []
    for i, row in enumerate(mes_a_mes):
        mnum = i + 1
        var_pct: float | None = None
        if mnum <= mes:
            if mnum == 1:
                prev_v = float(v_dec_ant)
            else:
                prev_v = float(mes_a_mes[i - 1].valor_total)
            cur_v = float(row.valor_total)
            if prev_v > 0:
                var_pct = round((cur_v - prev_v) / prev_v * 100.0, 1)
            elif abs(cur_v) < 1e-9 and abs(prev_v) < 1e-9:
                var_pct = 0.0
        mes_a_mes_enriquecido.append(
            row.model_copy(update={"variacao_percentual_mes_anterior": var_pct})
        )
    mes_a_mes = mes_a_mes_enriquecido
    cfg = _obter_config_appf(db)
    licenca_ativa = licenca_operacional(db)

    smtp_ok = bool(
        (cfg.smtp_host or "").strip()
        and (cfg.smtp_remetente or "").strip()
        and (cfg.smtp_usuario or "").strip()
        and bool(cfg.smtp_senha_cifrada)
    )

    return DashboardResumoOut(
        contribuintes_ativos=int(contrib_ativos),
        contribuintes_excluidos=int(contrib_excl),
        recibos_ativos_total=int(rec_ativos),
        recibos_cancelados_total=int(rec_cancel),
        mes_referencia_numero=mes,
        mes_referencia_ano=ano,
        mes_referencia_label=mes_label,
        recibos_emitidos_mes_ativos=qtd_mes,
        valor_total_mes_ativos=valor_mes,
        ano_referencia=ano,
        recibos_emitidos_ano_ativos=qtd_ano,
        valor_total_ano_ativos=valor_ano,
        licenca_ativa=licenca_ativa,
        smtp_configurado=smtp_ok,
        razao_social=(cfg.razao_social or "").strip() or "Instituição não informada",
        valor_dezembro_ano_anterior=round(v_dec_ant, 2),
        quantidade_dezembro_ano_anterior=q_dec_ant,
        contribuicoes_mes_a_mes=mes_a_mes,
    )


@router.get("/resumo", response_model=DashboardResumoOut, dependencies=[Depends(require_licenca)])
def obter_resumo_dashboard(
    db: Session = Depends(get_db),
    mes: int | None = Query(None, ge=1, le=12, description="Mês de referência (1–12)"),
    ano: int | None = Query(None, ge=2000, le=2100, description="Ano de referência"),
) -> DashboardResumoOut:
    agora = datetime.utcnow()
    ano_ref = ano if ano is not None else agora.year
    mes_ref = mes if mes is not None else agora.month
    return _montar_resumo_dashboard(db, ano_ref, mes_ref)
