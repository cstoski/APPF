from __future__ import annotations

from calendar import monthrange
from datetime import date, datetime
from typing import List, Literal, Tuple

from sqlalchemy.orm import Session

from app.models.core_models import Contribuinte, Recibo
from app.models.sys_models import ConfigAPPF
from app.schemas.core_schemas import RelatorioLinhaOut, RelatorioMesTotalOut, RelatorioResumoOut

PeriodoFinanceiro = Literal["mensal", "semestral", "anual"]

MESES_PT = (
    "",
    "Janeiro",
    "Fevereiro",
    "Março",
    "Abril",
    "Maio",
    "Junho",
    "Julho",
    "Agosto",
    "Setembro",
    "Outubro",
    "Novembro",
    "Dezembro",
)


def parse_data_inicio(value: date) -> datetime:
    return datetime(value.year, value.month, value.day, 0, 0, 0)


def parse_data_fim(value: date) -> datetime:
    return datetime(value.year, value.month, value.day, 23, 59, 59)


def intervalo_financeiro(
    periodo: PeriodoFinanceiro,
    ano: int,
    mes: int | None = None,
    semestre: int | None = None,
) -> Tuple[datetime, datetime, str]:
    if periodo == "mensal":
        if not mes or mes < 1 or mes > 12:
            raise ValueError("Mês inválido para relatório mensal.")
        ultimo_dia = monthrange(ano, mes)[1]
        inicio = datetime(ano, mes, 1, 0, 0, 0)
        fim = datetime(ano, mes, ultimo_dia, 23, 59, 59)
        rotulo = f"{MESES_PT[mes]}/{ano}"
        return inicio, fim, rotulo

    if periodo == "semestral":
        if semestre not in (1, 2):
            raise ValueError("Semestre inválido (use 1 ou 2).")
        if semestre == 1:
            inicio = datetime(ano, 1, 1, 0, 0, 0)
            fim = datetime(ano, 6, 30, 23, 59, 59)
            rotulo = f"1º semestre/{ano}"
        else:
            inicio = datetime(ano, 7, 1, 0, 0, 0)
            fim = datetime(ano, 12, 31, 23, 59, 59)
            rotulo = f"2º semestre/{ano}"
        return inicio, fim, rotulo

    inicio = datetime(ano, 1, 1, 0, 0, 0)
    fim = datetime(ano, 12, 31, 23, 59, 59)
    return inicio, fim, str(ano)


def calcular_resumo(linhas: List[RelatorioLinhaOut]) -> RelatorioResumoOut:
    validas = [l for l in linhas if not l.cancelado]
    quantidade = len(validas)
    valor_total = round(sum(l.valor for l in validas), 2)
    valor_medio = round(valor_total / quantidade, 2) if quantidade else 0.0
    cancelados = sum(1 for l in linhas if l.cancelado)
    return RelatorioResumoOut(
        quantidade=quantidade,
        valor_total=valor_total,
        valor_medio=valor_medio,
        quantidade_cancelados=cancelados,
    )


def _linha_recibo(
    r: Recibo,
    contribuinte_nome: str | None = None,
    contribuinte_id: int | None = None,
) -> RelatorioLinhaOut:
    return RelatorioLinhaOut(
        id=r.id,
        numero=r.numero,
        data_contribuicao=r.data_contribuicao,
        valor=float(r.valor),
        forma_pagamento=r.forma_pagamento,
        descricao=r.descricao,
        cancelado=bool(r.cancelado),
        contribuinte_nome=contribuinte_nome,
        contribuinte_id=contribuinte_id or r.contribuinte_id,
    )


def buscar_recibos_contribuinte(
    db: Session,
    contribuinte_id: int,
    inicio: datetime,
    fim: datetime,
    incluir_cancelados: bool,
) -> List[RelatorioLinhaOut]:
    q = db.query(Recibo).filter(
        Recibo.contribuinte_id == contribuinte_id,
        Recibo.data_contribuicao >= inicio,
        Recibo.data_contribuicao <= fim,
    )
    if not incluir_cancelados:
        q = q.filter(Recibo.cancelado.is_(False))
    rows = q.order_by(Recibo.data_contribuicao.asc()).all()
    return [_linha_recibo(r) for r in rows]


def buscar_recibos_financeiro(
    db: Session,
    inicio: datetime,
    fim: datetime,
    incluir_cancelados: bool,
) -> List[RelatorioLinhaOut]:
    q = (
        db.query(Recibo, Contribuinte.nome_completo)
        .join(Contribuinte, Contribuinte.id == Recibo.contribuinte_id)
        .filter(
            Recibo.data_contribuicao >= inicio,
            Recibo.data_contribuicao <= fim,
        )
    )
    if not incluir_cancelados:
        q = q.filter(Recibo.cancelado.is_(False))
    rows = q.order_by(Recibo.data_contribuicao.asc(), Recibo.numero.asc()).all()
    return [
        _linha_recibo(r, contribuinte_nome=nome, contribuinte_id=r.contribuinte_id)
        for r, nome in rows
    ]


def rotulo_periodo_contribuinte(inicio: datetime, fim: datetime) -> str:
    di = inicio.strftime("%d/%m/%Y")
    df = fim.strftime("%d/%m/%Y")
    return f"{di} a {df}"


def agregar_totais_mensais(linhas: List[RelatorioLinhaOut], ano: int) -> List[RelatorioMesTotalOut]:
    """Soma contribuições não canceladas por mês do ano."""
    buckets: dict[int, dict[str, float | int]] = {
        m: {"quantidade": 0, "valor_total": 0.0} for m in range(1, 13)
    }
    for linha in linhas:
        if linha.cancelado:
            continue
        dt = linha.data_contribuicao
        if dt.year != ano:
            continue
        m = dt.month
        buckets[m]["quantidade"] = int(buckets[m]["quantidade"]) + 1
        buckets[m]["valor_total"] = float(buckets[m]["valor_total"]) + float(linha.valor)

    resultado: List[RelatorioMesTotalOut] = []
    for m in range(1, 13):
        resultado.append(
            RelatorioMesTotalOut(
                mes=m,
                mes_label=f"{MESES_PT[m]}/{ano}",
                quantidade=int(buckets[m]["quantidade"]),
                valor_total=round(float(buckets[m]["valor_total"]), 2),
            )
        )
    return resultado
