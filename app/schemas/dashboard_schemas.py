from __future__ import annotations

from typing import Optional

from pydantic import BaseModel, Field


class DashboardMesContribOut(BaseModel):
    """Totais de recibos ativos no mês (ano de referência do dashboard)."""

    mes: int = Field(..., ge=1, le=12)
    mes_label: str
    valor_total: float
    quantidade: int
    variacao_percentual_mes_anterior: Optional[float] = None


class DashboardResumoOut(BaseModel):
    """Métricas agregadas para a tela inicial."""

    contribuintes_ativos: int
    contribuintes_excluidos: int
    recibos_ativos_total: int
    recibos_cancelados_total: int

    mes_referencia_numero: int = Field(..., ge=1, le=12)
    mes_referencia_ano: int
    mes_referencia_label: str
    recibos_emitidos_mes_ativos: int
    valor_total_mes_ativos: float

    ano_referencia: int
    recibos_emitidos_ano_ativos: int
    valor_total_ano_ativos: float

    licenca_ativa: bool
    smtp_configurado: bool
    razao_social: str

    valor_dezembro_ano_anterior: float = 0.0
    quantidade_dezembro_ano_anterior: int = 0
    contribuicoes_mes_a_mes: list[DashboardMesContribOut] = Field(default_factory=list)
