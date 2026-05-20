import { useState } from 'react'
import { relatorioService } from '../services/api'
import ContribuinteSearch from '../components/ContribuinteSearch'
import { useAuth } from '../hooks/useAuth.jsx'
import { formatApiError } from '../utils/formatApiError'
import { formatCpfDisplay } from '../utils/masks'
import { exportarRelatorioExcel } from '../utils/relatorioExcel'
import {
  formatDataGeracao,
  formatDataRecebimento,
  imprimirRelatorioPdf,
  ordenarLinhasRelatorio,
} from '../utils/relatorioPdf'
import '../styles/operacional.css'

function hojeISO() {
  return new Date().toISOString().slice(0, 10)
}

function inicioAnoISO() {
  return `${new Date().getFullYear()}-01-01`
}

function formatValor(valor) {
  return `R$ ${Number(valor).toFixed(2).replace('.', ',')}`
}

function instituicaoDe(dados) {
  return (
    dados?.instituicao || {
      razao_social: dados?.razao_social || 'APPF',
      cnpj: dados?.cnpj || '',
    }
  )
}

function ResumoCards({ resumo, mostrarValorMedio = false }) {
  if (!resumo) return null
  return (
    <div className="relatorio-resumo-grid">
      <div className="relatorio-resumo-card">
        <span className="relatorio-resumo-label">Quantidade</span>
        <strong>{resumo.quantidade}</strong>
      </div>
      <div className="relatorio-resumo-card">
        <span className="relatorio-resumo-label">Valor total</span>
        <strong>{formatValor(resumo.valor_total)}</strong>
      </div>
      {mostrarValorMedio && (
        <div className="relatorio-resumo-card">
          <span className="relatorio-resumo-label">Valor médio</span>
          <strong>{formatValor(resumo.valor_medio)}</strong>
        </div>
      )}
      {resumo.quantidade_cancelados > 0 && (
        <div className="relatorio-resumo-card relatorio-resumo-card-muted">
          <span className="relatorio-resumo-label">Cancelados (fora do total)</span>
          <strong>{resumo.quantidade_cancelados}</strong>
        </div>
      )}
    </div>
  )
}

function TabelaMensalAnual({ totaisMensais }) {
  if (!totaisMensais?.length) return null

  const totalQtd = totaisMensais.reduce((s, m) => s + m.quantidade, 0)
  const totalVal = totaisMensais.reduce((s, m) => s + m.valor_total, 0)

  return (
    <div className="relatorio-mensal-section">
      <h4>Resumo mensal de contribuições</h4>
      <div className="data-table-wrap">
        <table className="table table-contribuintes relatorio-table">
          <thead>
            <tr>
              <th>Mês</th>
              <th>Quantidade</th>
              <th>Valor total</th>
            </tr>
          </thead>
          <tbody>
            {totaisMensais.map((m) => (
              <tr key={m.mes}>
                <td>{m.mes_label}</td>
                <td>{m.quantidade}</td>
                <td>{formatValor(m.valor_total)}</td>
              </tr>
            ))}
            <tr className="relatorio-mensal-total">
              <td>
                <strong>Total do ano</strong>
              </td>
              <td>
                <strong>{totalQtd}</strong>
              </td>
              <td>
                <strong>{formatValor(totalVal)}</strong>
              </td>
            </tr>
          </tbody>
        </table>
      </div>
    </div>
  )
}

function TabelaLinhas({ linhas, mostrarContribuinte }) {
  const ordenadas = ordenarLinhasRelatorio(linhas)
  if (!ordenadas.length) {
    return <p className="text-muted">Nenhuma contribuição encontrada no período.</p>
  }

  return (
    <div className="data-table-wrap">
      <table className="table table-contribuintes relatorio-table">
        <thead>
          <tr>
            <th>Data</th>
            <th>Nº recibo</th>
            {mostrarContribuinte && <th>Contribuinte</th>}
            <th>Valor</th>
            <th>Forma</th>
            <th>Status</th>
          </tr>
        </thead>
        <tbody>
          {ordenadas.map((l) => (
            <tr key={l.id} className={l.cancelado ? 'linha-cancelada' : ''}>
              <td>{formatDataRecebimento(l.data_contribuicao)}</td>
              <td className="cell-mono">{l.numero}</td>
              {mostrarContribuinte && <td>{l.contribuinte_nome || '—'}</td>}
              <td>{formatValor(l.valor)}</td>
              <td>{l.forma_pagamento || '—'}</td>
              <td>{l.cancelado ? 'Cancelado' : 'Ativo'}</td>
            </tr>
          ))}
        </tbody>
      </table>
    </div>
  )
}

function RelatorioResultado({ dados, tipo, username, onImprimir, onExportarExcel, imprimindo, exportando }) {
  if (!dados) return null

  const financeiro = tipo === 'financeiro'
  const inst = instituicaoDe(dados)

  return (
    <section className="card card-strong relatorio-print-area">
      <div className="relatorio-cabecalho">
        <div>
          <h3>{dados.titulo}</h3>
          <p className="text-muted">
            <strong>{inst.razao_social}</strong>
            {inst.cnpj ? ` — CNPJ ${inst.cnpj}` : ''}
          </p>
          {financeiro ? (
            <p>
              <strong>Período:</strong> {dados.periodo_label}
            </p>
          ) : (
            <>
              <p>
                <strong>Contribuinte:</strong> {dados.contribuinte_nome}
              </p>
              {dados.contribuinte_cpf && (
                <p>
                  <strong>CPF:</strong> {formatCpfDisplay(dados.contribuinte_cpf)}
                </p>
              )}
              <p>
                <strong>Período:</strong> {dados.periodo_label}
              </p>
            </>
          )}
        </div>
        <div className="relatorio-acoes no-print">
          <button
            type="button"
            className="btn btn-outline"
            onClick={onExportarExcel}
            disabled={imprimindo || exportando}
          >
            {exportando ? 'Exportando...' : 'Exportar Excel'}
          </button>
          <button
            type="button"
            className="btn btn-outline"
            onClick={onImprimir}
            disabled={imprimindo || exportando}
          >
            {imprimindo ? 'Gerando PDF...' : 'Imprimir PDF'}
          </button>
        </div>
      </div>

      <TabelaLinhas linhas={dados.linhas} mostrarContribuinte={financeiro} />

      {financeiro && dados.periodo === 'anual' && (
        <TabelaMensalAnual totaisMensais={dados.totais_mensais} />
      )}

      <ResumoCards resumo={dados.resumo} mostrarValorMedio={financeiro} />
      <p className="text-muted relatorio-gerado-em">
        Gerado em: {formatDataGeracao()}
        {username ? ` — por ${username}` : ''}
      </p>
    </section>
  )
}

export default function RelatoriosPage() {
  const { username } = useAuth()
  const [tab, setTab] = useState('contribuinte')

  const [contribuinte, setContribuinte] = useState(null)
  const [dataInicio, setDataInicio] = useState(inicioAnoISO())
  const [dataFim, setDataFim] = useState(hojeISO())
  const [incluirCanceladosContrib, setIncluirCanceladosContrib] = useState(false)

  const [periodo, setPeriodo] = useState('mensal')
  const [ano, setAno] = useState(new Date().getFullYear())
  const [mes, setMes] = useState(new Date().getMonth() + 1)
  const [semestre, setSemestre] = useState(new Date().getMonth() < 6 ? 1 : 2)
  const [incluirCanceladosFin, setIncluirCanceladosFin] = useState(false)

  const [relatorio, setRelatorio] = useState(null)
  const [tipoRelatorio, setTipoRelatorio] = useState(null)
  const [loading, setLoading] = useState(false)
  const [imprimindo, setImprimindo] = useState(false)
  const [exportando, setExportando] = useState(false)
  const [error, setError] = useState('')

  const gerarContribuinte = async (e) => {
    e.preventDefault()
    if (!contribuinte?.id) {
      setError('Selecione um contribuinte.')
      return
    }
    if (dataFim < dataInicio) {
      setError('A data final deve ser igual ou posterior à data inicial.')
      return
    }
    setLoading(true)
    setError('')
    setRelatorio(null)
    try {
      const { data } = await relatorioService.contribuinte({
        contribuinte_id: contribuinte.id,
        data_inicio: dataInicio,
        data_fim: dataFim,
        incluir_cancelados: incluirCanceladosContrib,
      })
      setRelatorio(data)
      setTipoRelatorio('contribuinte')
    } catch (err) {
      setError(formatApiError(err, 'Erro ao gerar relatório do contribuinte.'))
    } finally {
      setLoading(false)
    }
  }

  const gerarFinanceiro = async (e) => {
    e.preventDefault()
    setLoading(true)
    setError('')
    setRelatorio(null)
    try {
      const params = {
        periodo,
        ano,
        incluir_cancelados: incluirCanceladosFin,
      }
      if (periodo === 'mensal') params.mes = mes
      if (periodo === 'semestral') params.semestre = semestre

      const { data } = await relatorioService.financeiro(params)
      setRelatorio(data)
      setTipoRelatorio('financeiro')
    } catch (err) {
      setError(formatApiError(err, 'Erro ao gerar relatório financeiro.'))
    } finally {
      setLoading(false)
    }
  }

  const handleImprimir = async () => {
    if (!relatorio || !tipoRelatorio) return
    setImprimindo(true)
    setError('')
    try {
      await imprimirRelatorioPdf(relatorio, tipoRelatorio, username)
    } catch (err) {
      setError(err?.message || 'Não foi possível gerar o PDF do relatório.')
    } finally {
      setImprimindo(false)
    }
  }

  const handleExportarExcel = () => {
    if (!relatorio || !tipoRelatorio) return
    setExportando(true)
    setError('')
    try {
      exportarRelatorioExcel(relatorio, tipoRelatorio, username)
    } catch (err) {
      setError(err?.message || 'Não foi possível exportar para Excel.')
    } finally {
      setExportando(false)
    }
  }

  const meses = [
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

  return (
    <div className="page-grid relatorios-page">
      <div className="section-header no-print">
        <div>
          <h2 className="page-title">Relatórios</h2>
          <p className="page-description">
            Informe de contribuições por contribuinte ou consolidado financeiro da APPF.
          </p>
        </div>
      </div>

      <div className="tabs no-print">
        <button
          type="button"
          className={`tab-btn ${tab === 'contribuinte' ? 'active' : ''}`}
          onClick={() => setTab('contribuinte')}
        >
          Por contribuinte
        </button>
        <button
          type="button"
          className={`tab-btn ${tab === 'financeiro' ? 'active' : ''}`}
          onClick={() => setTab('financeiro')}
        >
          Financeiro APPF
        </button>
      </div>

      {error && <div className="alert alert-error no-print">{error}</div>}

      {tab === 'contribuinte' && (
        <section className="card card-strong no-print">
          <h3>Informe de contribuições (por período)</h3>
          <p className="text-muted">
            Relatório de todas as contribuições de um contribuinte no intervalo informado.
          </p>
          <form onSubmit={gerarContribuinte} className="relatorio-form">
            <ContribuinteSearch selectedId={contribuinte?.id} onSelect={setContribuinte} />
            {contribuinte && (
              <p className="text-muted">
                Selecionado: <strong>{contribuinte.nome_completo}</strong>
              </p>
            )}
            <div className="form-grid">
              <label>
                Data inicial
                <input
                  type="date"
                  value={dataInicio}
                  onChange={(e) => setDataInicio(e.target.value)}
                  required
                />
              </label>
              <label>
                Data final
                <input
                  type="date"
                  value={dataFim}
                  onChange={(e) => setDataFim(e.target.value)}
                  required
                />
              </label>
            </div>
            <label className="checkbox-inline">
              <input
                type="checkbox"
                checked={incluirCanceladosContrib}
                onChange={(e) => setIncluirCanceladosContrib(e.target.checked)}
              />
              Incluir recibos cancelados na listagem
            </label>
            <div className="form-actions">
              <button type="submit" className="btn btn-primary" disabled={loading}>
                {loading ? 'Gerando...' : 'Gerar relatório'}
              </button>
            </div>
          </form>
        </section>
      )}

      {tab === 'financeiro' && (
        <section className="card card-strong no-print">
          <h3>Relatório financeiro da APPF</h3>
          <p className="text-muted">
            Consolidado de todas as contribuições no período, com quantidade, valor total e valor médio.
          </p>
          <form onSubmit={gerarFinanceiro} className="relatorio-form">
            <div className="form-grid">
              <label>
                Período
                <select value={periodo} onChange={(e) => setPeriodo(e.target.value)}>
                  <option value="mensal">Mensal</option>
                  <option value="semestral">Semestral</option>
                  <option value="anual">Anual</option>
                </select>
              </label>
              <label>
                Ano
                <input
                  type="number"
                  min={2000}
                  max={2100}
                  value={ano}
                  onChange={(e) => setAno(Number(e.target.value))}
                  required
                />
              </label>
              {periodo === 'mensal' && (
                <label>
                  Mês
                  <select value={mes} onChange={(e) => setMes(Number(e.target.value))}>
                    {meses.map((m) => (
                      <option key={m.v} value={m.v}>
                        {m.l}
                      </option>
                    ))}
                  </select>
                </label>
              )}
              {periodo === 'semestral' && (
                <label>
                  Semestre
                  <select value={semestre} onChange={(e) => setSemestre(Number(e.target.value))}>
                    <option value={1}>1º semestre (jan–jun)</option>
                    <option value={2}>2º semestre (jul–dez)</option>
                  </select>
                </label>
              )}
            </div>
            <label className="checkbox-inline">
              <input
                type="checkbox"
                checked={incluirCanceladosFin}
                onChange={(e) => setIncluirCanceladosFin(e.target.checked)}
              />
              Incluir recibos cancelados na listagem
            </label>
            <div className="form-actions">
              <button type="submit" className="btn btn-primary" disabled={loading}>
                {loading ? 'Gerando...' : 'Gerar relatório'}
              </button>
            </div>
          </form>
        </section>
      )}

      <RelatorioResultado
        dados={relatorio}
        tipo={tipoRelatorio}
        username={username}
        onImprimir={handleImprimir}
        onExportarExcel={handleExportarExcel}
        imprimindo={imprimindo}
        exportando={exportando}
      />
    </div>
  )
}
