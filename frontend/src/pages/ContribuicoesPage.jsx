import { useCallback, useEffect, useState } from 'react'
import { appfService, contribuinteService, contribuicaoService } from '../services/api'
import { formatApiError } from '../utils/formatApiError'
import ContribuinteSearch from '../components/ContribuinteSearch'
import ContribuinteFormModal from '../components/ContribuinteFormModal'
import ReciboViewCard from '../components/ReciboViewCard'
import { inferirCadastroDoTermo } from '../utils/masks'
import '../styles/operacional.css'

function dataLocalIso() {
  const d = new Date()
  const y = d.getFullYear()
  const m = String(d.getMonth() + 1).padStart(2, '0')
  const day = String(d.getDate()).padStart(2, '0')
  return `${y}-${m}-${day}`
}

export default function ContribuicoesPage() {
  const [contribuinte, setContribuinte] = useState(null)
  const [valor, setValor] = useState('')
  const [dataContribuicao, setDataContribuicao] = useState(dataLocalIso)
  const [formaPagamento, setFormaPagamento] = useState('Dinheiro')
  const [descricao, setDescricao] = useState('')
  const [recibo, setRecibo] = useState(null)
  const [recibos, setRecibos] = useState([])
  const [loadingLista, setLoadingLista] = useState(false)
  const [cancelTarget, setCancelTarget] = useState(null)
  const [motivoCancelamento, setMotivoCancelamento] = useState('')
  const [loading, setLoading] = useState(false)
  const [error, setError] = useState('')
  const [success, setSuccess] = useState('')
  const [modalCadastro, setModalCadastro] = useState(false)
  const [formInicialCadastro, setFormInicialCadastro] = useState(null)
  const [configAppf, setConfigAppf] = useState(null)

  useEffect(() => {
    appfService
      .obterConfig()
      .then(({ data }) => setConfigAppf(data))
      .catch(() => {})
  }, [])

  const carregarRecibos = useCallback(async (contribuinteId) => {
    if (!contribuinteId) {
      setRecibos([])
      return
    }
    setLoadingLista(true)
    try {
      const { data } = await contribuicaoService.listar(contribuinteId)
      setRecibos(data)
    } catch (err) {
      setError(formatApiError(err, 'Erro ao carregar recibos.'))
    } finally {
      setLoadingLista(false)
    }
  }, [])

  const contribuinteId = contribuinte?.id ?? null

  useEffect(() => {
    setRecibo(null)
    setCancelTarget(null)
    setMotivoCancelamento('')
    if (contribuinteId) {
      carregarRecibos(contribuinteId)
    } else {
      setRecibos([])
    }
  }, [contribuinteId, carregarRecibos])

  const gerarContribuicao = async (e) => {
    e.preventDefault()
    if (!contribuinte) {
      setError('Selecione um contribuinte.')
      return
    }
    setLoading(true)
    setError('')
    setSuccess('')
    try {
      const { data } = await contribuicaoService.emitir({
        contribuinte_id: contribuinte.id,
        valor: parseFloat(valor),
        data_contribuicao: dataContribuicao,
        forma_pagamento: formaPagamento || null,
        descricao: descricao || null,
      })
      setRecibo(data)
      setSuccess(`Contribuição registrada. Recibo ${data.numero} gerado com sucesso.`)
      setValor('')
      setDescricao('')
      setDataContribuicao(dataLocalIso())
      await carregarRecibos(contribuinte.id)
    } catch (err) {
      setError(formatApiError(err, 'Erro ao gerar contribuição.'))
    } finally {
      setLoading(false)
    }
  }

  const abrirCancelamento = (r) => {
    setCancelTarget(r)
    setMotivoCancelamento('')
    setError('')
  }

  const fecharCancelamento = () => {
    setCancelTarget(null)
    setMotivoCancelamento('')
  }

  const abrirCadastroContribuinte = (termoBusca) => {
    setFormInicialCadastro(inferirCadastroDoTermo(termoBusca))
    setModalCadastro(true)
    setError('')
  }

  const fecharCadastroContribuinte = () => {
    setModalCadastro(false)
    setFormInicialCadastro(null)
  }

  const handleContribuinteCadastrado = (message, criado) => {
    setSuccess(message)
    if (criado) {
      setContribuinte(criado)
    }
    fecharCadastroContribuinte()
  }

  const verRecibo = async (r) => {
    setSuccess('')
    setError('')
    try {
      const [reciboRes, detRes] = await Promise.all([
        contribuicaoService.obter(r.id),
        contribuinteId ? contribuinteService.obter(contribuinteId) : Promise.resolve(null),
      ])
      setRecibo(reciboRes.data)
      if (detRes?.data) {
        setContribuinte((prev) =>
          prev?.id === detRes.data.id
            ? { ...prev, nome_completo: detRes.data.nome_completo, cpf: detRes.data.cpf || prev.cpf }
            : prev,
        )
      }
    } catch (err) {
      setError(formatApiError(err, 'Erro ao carregar recibo.'))
    }
  }

  const confirmarCancelamento = async () => {
    if (!cancelTarget) return
    if (motivoCancelamento.trim().length < 10) {
      setError('Informe o motivo do cancelamento (mín. 10 caracteres).')
      return
    }
    setLoading(true)
    setError('')
    setSuccess('')
    try {
      const { data } = await contribuicaoService.cancelar(cancelTarget.id, motivoCancelamento.trim())
      setRecibo(data)
      setSuccess(`Recibo ${data.numero} cancelado.`)
      fecharCancelamento()
      await carregarRecibos(contribuinte.id)
    } catch (err) {
      setError(formatApiError(err, 'Erro ao cancelar recibo.'))
    } finally {
      setLoading(false)
    }
  }

  return (
    <div className="page-grid">
      <div className="section-header">
        <div>
          <h2 className="page-title">Contribuições / Recibos</h2>
          <p className="page-description">
            Registre contribuições e gerencie o histórico do contribuinte selecionado.
          </p>
        </div>
      </div>

      {error && <div className="alert alert-error">{error}</div>}
      {success && <div className="alert alert-success">{success}</div>}

      <section className="card card-strong">
        <h3>Gerar contribuição</h3>
        <ContribuinteSearch
          selectedId={contribuinte?.id}
          onSelect={setContribuinte}
          onCadastrarNovo={abrirCadastroContribuinte}
        />
        {contribuinte && (
          <p className="mt-2">
            Selecionado: <strong>{contribuinte.nome_completo}</strong>
          </p>
        )}
        <form onSubmit={gerarContribuicao} className="mt-3">
          <div className="form-grid">
            <label>
              Data da contribuição
              <input
                type="date"
                value={dataContribuicao}
                max={dataLocalIso()}
                onChange={(e) => setDataContribuicao(e.target.value)}
                required
                disabled={!contribuinte}
              />
            </label>
            <label>
              Valor (R$)
              <input
                type="number"
                step="0.01"
                min="0.01"
                value={valor}
                onChange={(e) => setValor(e.target.value)}
                required
                disabled={!contribuinte}
              />
            </label>
            <label>
              Forma de pagamento
              <select
                value={formaPagamento}
                onChange={(e) => setFormaPagamento(e.target.value)}
                disabled={!contribuinte}
              >
                <option>Dinheiro</option>
                <option>PIX</option>
                <option>Cartão</option>
                <option>Transferência</option>
              </select>
            </label>
            <label>
              Descrição
              <input
                value={descricao}
                onChange={(e) => setDescricao(e.target.value)}
                disabled={!contribuinte}
              />
            </label>
          </div>
          <div className="form-actions">
            <button type="submit" className="btn btn-primary" disabled={loading || !contribuinte}>
              {loading ? 'Gerando...' : 'Gerar contribuição'}
            </button>
          </div>
        </form>
      </section>

      {contribuinte && (
        <section className="card card-strong data-table-wrap">
          <h3>Recibos do contribuinte</h3>
          {loadingLista ? (
            <p className="text-muted">Carregando recibos...</p>
          ) : recibos.length === 0 ? (
            <p className="text-muted">Nenhum recibo emitido para este contribuinte.</p>
          ) : (
            <table className="table table-contribuintes">
              <thead>
                <tr>
                  <th>Número</th>
                  <th>Data</th>
                  <th>Valor</th>
                  <th>Forma</th>
                  <th>Status</th>
                  <th className="col-acoes">Ações</th>
                </tr>
              </thead>
              <tbody>
                {recibos.map((r) => (
                  <tr key={r.id} className={r.cancelado ? 'row-excluido' : undefined}>
                    <td className="cell-mono">{r.numero}</td>
                    <td>{new Date(r.data_contribuicao).toLocaleDateString('pt-BR')}</td>
                    <td>R$ {Number(r.valor).toFixed(2)}</td>
                    <td>{r.forma_pagamento || '—'}</td>
                    <td>{r.cancelado ? 'Cancelado' : 'Ativo'}</td>
                    <td className="col-acoes">
                      <div className="table-actions">
                        <button
                          type="button"
                          className="btn btn-sm btn-outline"
                          onClick={() => verRecibo(r)}
                        >
                          Ver
                        </button>
                        {!r.cancelado && (
                          <button
                            type="button"
                            className="btn btn-sm btn-danger"
                            onClick={() => abrirCancelamento(r)}
                            disabled={loading}
                          >
                            Cancelar
                          </button>
                        )}
                      </div>
                    </td>
                  </tr>
                ))}
              </tbody>
            </table>
          )}
        </section>
      )}

      {recibo && (
        <ReciboViewCard recibo={recibo} contribuinte={contribuinte} configAppf={configAppf} />
      )}

      <ContribuinteFormModal
        open={modalCadastro}
        mode="create"
        initialForm={formInicialCadastro}
        onClose={fecharCadastroContribuinte}
        onSaved={handleContribuinteCadastrado}
      />

      {cancelTarget && (
        <div className="modal-overlay" onClick={fecharCancelamento} role="presentation">
          <div
            className="modal-panel card card-strong"
            onClick={(e) => e.stopPropagation()}
            role="dialog"
            aria-modal="true"
          >
            <div className="modal-header">
              <h3>Cancelar recibo {cancelTarget.numero}</h3>
              <button type="button" className="btn btn-outline" onClick={fecharCancelamento}>
                Fechar
              </button>
            </div>
            <div className="form-stack">
              <label>
                Motivo do cancelamento (mín. 10 caracteres)
                <textarea
                  rows={4}
                  value={motivoCancelamento}
                  onChange={(e) => setMotivoCancelamento(e.target.value)}
                  required
                />
              </label>
            </div>
            <div className="form-actions">
              <button type="button" className="btn btn-outline" onClick={fecharCancelamento} disabled={loading}>
                Voltar
              </button>
              <button type="button" className="btn btn-danger" onClick={confirmarCancelamento} disabled={loading}>
                {loading ? 'Cancelando...' : 'Confirmar cancelamento'}
              </button>
            </div>
          </div>
        </div>
      )}
    </div>
  )
}
