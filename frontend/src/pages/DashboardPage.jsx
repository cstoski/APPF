import { useEffect, useState } from 'react'

import { dashboardService } from '../services/api'
import { formatApiError } from '../utils/formatApiError'

import '../styles/dashboard.css'
import '../styles/operacional.css'

const brl = (v) =>
  new Intl.NumberFormat('pt-BR', { style: 'currency', currency: 'BRL' }).format(Number(v) || 0)

/** Variação já calculada pela API (Δ % vs mês anterior). */
function formatoVariacaoApi(pct) {
  if (pct == null || Number.isNaN(Number(pct))) {
    return { variant: 'muted', text: '—' }
  }
  const num = Number(pct)
  const rounded = Math.round(num * 10) / 10
  if (Math.abs(rounded) < 0.05) {
    return { variant: 'neutro', text: '0%' }
  }
  if (rounded > 0) {
    return { variant: 'up', text: `+${rounded.toLocaleString('pt-BR')}%` }
  }
  return { variant: 'down', text: `${rounded.toLocaleString('pt-BR')}%` }
}

const MESES_ABREV = [
  '',
  'Jan.',
  'Fev.',
  'Mar.',
  'Abr.',
  'Mai.',
  'Jun.',
  'Jul.',
  'Ago.',
  'Set.',
  'Out.',
  'Nov.',
  'Dez.',
]

const MESES_SELECT = [
  { v: 1, l: 'Janeiro' },
  { v: 2, l: 'Fevereiro' },
  { v: 3, l: 'Março' },
  { v: 4, l: 'Abril' },
  { v: 5, l: 'Maio' },
  { v: 6, l: 'Junho' },
  { v: 7, l: 'Julho' },
  { v: 8, l: 'Agosto' },
  { v: 9, l: 'Setembro' },
  { v: 10, l: 'Outubro' },
  { v: 11, l: 'Novembro' },
  { v: 12, l: 'Dezembro' },
]

const ANO_MIN = 2000
const ANO_MAX = 2100

export default function DashboardPage() {
  const hoje = new Date()
  const [ano, setAno] = useState(hoje.getFullYear())
  const [mes, setMes] = useState(hoje.getMonth() + 1)
  const [loading, setLoading] = useState(true)
  const [error, setError] = useState('')
  const [resumo, setResumo] = useState(null)

  useEffect(() => {
    let ativo = true
    const load = async () => {
      setLoading(true)
      setError('')
      try {
        const { data } = await dashboardService.resumo({ mes, ano })
        if (ativo) setResumo(data)
      } catch (err) {
        if (ativo) {
          setResumo(null)
          setError(formatApiError(err, 'Não foi possível carregar o resumo.'))
        }
      } finally {
        if (ativo) setLoading(false)
      }
    }
    load()
    return () => {
      ativo = false
    }
  }, [mes, ano])

  return (
    <div className="dashboard">
      <div className="dashboard-header section-header">
        <div>
          <h2 className="page-title">Visão geral</h2>
          <p className="page-description text-muted">
            Período de referência para os totais do mês, do ano e da tabela à direita.
          </p>
        </div>
        <div className="dashboard-periodo-filtros">
          <label>
            Mês
            <select value={mes} onChange={(e) => setMes(Number(e.target.value))} disabled={loading}>
              {MESES_SELECT.map((m) => (
                <option key={m.v} value={m.v}>
                  {m.l}
                </option>
              ))}
            </select>
          </label>
          <label>
            Ano
            <input
              type="number"
              min={ANO_MIN}
              max={ANO_MAX}
              value={ano}
              onChange={(e) => setAno(Number(e.target.value))}
              disabled={loading}
            />
          </label>
        </div>
      </div>

      {error && <div className="alert alert-error">{error}</div>}

      {loading && <p className="text-muted">Carregando dados…</p>}

      {!loading && resumo && (
        <div className="dashboard-layout">
          <div className="dashboard-left">
            <div className="dashboard-kpi-row">
              <section className="card card-strong dashboard-finance-card">
                <h3 className="dashboard-section-title">Contribuintes ativos</h3>
                <dl className="dashboard-dl">
                  <div>
                    <dt>Total no cadastro</dt>
                    <dd className="dashboard-dl-strong">{resumo.contribuintes_ativos}</dd>
                  </div>
                </dl>
              </section>

              <section className="card card-strong dashboard-finance-card">
                <h3 className="dashboard-section-title">Recibos ativos no sistema</h3>
                <dl className="dashboard-dl">
                  <div>
                    <dt>Total emitidos (ativos)</dt>
                    <dd className="dashboard-dl-strong">{resumo.recibos_ativos_total}</dd>
                  </div>
                </dl>
              </section>

              <section className="card card-strong dashboard-finance-card dashboard-stat-card-muted">
                <h3 className="dashboard-section-title">Recibos cancelados</h3>
                <dl className="dashboard-dl">
                  <div>
                    <dt>Total cancelados</dt>
                    <dd className="dashboard-dl-strong">{resumo.recibos_cancelados_total}</dd>
                  </div>
                </dl>
              </section>
            </div>

            <div className="dashboard-finance-row">
              <section className="card card-strong dashboard-finance-card">
                <h3 className="dashboard-section-title">{resumo.mes_referencia_label}</h3>
                <dl className="dashboard-dl">
                  <div>
                    <dt>Contribuições registradas</dt>
                    <dd>{resumo.recibos_emitidos_mes_ativos}</dd>
                  </div>
                  <div>
                    <dt>Valor total</dt>
                    <dd className="dashboard-dl-strong">{brl(resumo.valor_total_mes_ativos)}</dd>
                  </div>
                </dl>
              </section>

              <section className="card card-strong dashboard-finance-card">
                <h3 className="dashboard-section-title">Acumulado em {resumo.ano_referencia}</h3>
                <dl className="dashboard-dl">
                  <div>
                    <dt>Contribuições (ativas)</dt>
                    <dd>{resumo.recibos_emitidos_ano_ativos}</dd>
                  </div>
                  <div>
                    <dt>Valor total no ano</dt>
                    <dd className="dashboard-dl-strong">{brl(resumo.valor_total_ano_ativos)}</dd>
                  </div>
                </dl>
              </section>

              <section className="card card-strong dashboard-finance-card dashboard-media-mensal">
                <h3 className="dashboard-section-title">Média mensal</h3>
                <p className="dashboard-media-hint text-muted">
                  Acumulado ÷ {resumo.mes_referencia_numero}{' '}
                  {resumo.mes_referencia_numero === 1 ? 'mês' : 'meses'} (jan. a{' '}
                  {resumo.mes_referencia_label.split(' de ')[0]}).
                </p>
                <dl className="dashboard-dl">
                  <div>
                    <dt>Valor médio por mês</dt>
                    <dd className="dashboard-dl-strong">
                      {brl(
                        resumo.mes_referencia_numero > 0
                          ? resumo.valor_total_ano_ativos / resumo.mes_referencia_numero
                          : 0,
                      )}
                    </dd>
                  </div>
                  <div>
                    <dt>Recibos por mês (média)</dt>
                    <dd>
                      {resumo.mes_referencia_numero > 0
                        ? (resumo.recibos_emitidos_ano_ativos / resumo.mes_referencia_numero).toLocaleString(
                            'pt-BR',
                            { maximumFractionDigits: 1, minimumFractionDigits: 0 },
                          )
                        : '—'}
                    </dd>
                  </div>
                </dl>
              </section>
            </div>
          </div>

          <aside className="dashboard-mes-sidebar" aria-label="Contribuições mês a mês">
            <section className="card card-strong dashboard-mes-box">
              <h3 className="dashboard-section-title">Mês a mês · {resumo.ano_referencia}</h3>
              <p className="dashboard-mes-lead text-muted">
                Ativos. Jan. vs dez. {resumo.ano_referencia - 1}. Verde sobe, vermelho cai.
              </p>
              <div className="data-table-wrap dashboard-mes-table-wrap">
                <table className="table table-contribuintes dashboard-mes-table">
                  <thead>
                    <tr>
                      <th>Mês</th>
                      <th className="cell-num">Valor</th>
                      <th className="cell-num">Δ %</th>
                    </tr>
                  </thead>
                  <tbody>
                    {(resumo.contribuicoes_mes_a_mes || []).map((linha) => {
                      const variacao =
                        linha.mes > resumo.mes_referencia_numero
                          ? { variant: 'muted', text: '—' }
                          : formatoVariacaoApi(linha.variacao_percentual_mes_anterior)
                      const isFuturo = linha.mes > resumo.mes_referencia_numero
                      return (
                        <tr key={linha.mes} className={isFuturo ? 'dashboard-mes-row-futuro' : undefined}>
                          <td>{MESES_ABREV[linha.mes] || linha.mes_label}</td>
                          <td className="cell-num cell-mono">{brl(linha.valor_total)}</td>
                          <td className="cell-num">
                            <span
                              className={
                                variacao.variant === 'up'
                                  ? 'dashboard-var dashboard-var-up'
                                  : variacao.variant === 'down'
                                    ? 'dashboard-var dashboard-var-down'
                                    : 'dashboard-var dashboard-var-muted'
                              }
                            >
                              {variacao.text}
                            </span>
                          </td>
                        </tr>
                      )
                    })}
                  </tbody>
                </table>
              </div>
            </section>
          </aside>
        </div>
      )}
    </div>
  )
}
