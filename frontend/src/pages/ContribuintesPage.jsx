import { useCallback, useEffect, useMemo, useState } from 'react'
import { IconEdit, IconRestore, IconTrash } from '../components/ActionIcons'
import ContribuinteFormModal from '../components/ContribuinteFormModal'
import ContribuintesImportPanel from '../components/ContribuintesImportPanel'
import { contribuinteService, exportService, downloadBlobResponse } from '../services/api'
import { formatApiError } from '../utils/formatApiError'
import { formatCpfDisplay, formatTelefoneDisplay } from '../utils/masks'
import '../styles/operacional.css'

export default function ContribuintesPage() {
  const [contribuintes, setContribuintes] = useState([])
  const [filtro, setFiltro] = useState('')
  const [loadingLista, setLoadingLista] = useState(true)
  const [success, setSuccess] = useState('')
  const [error, setError] = useState('')
  const [modalOpen, setModalOpen] = useState(false)
  const [modalMode, setModalMode] = useState('create')
  const [editingId, setEditingId] = useState(null)
  const [deletingId, setDeletingId] = useState(null)
  const [reativandoId, setReativandoId] = useState(null)
  const [showImport, setShowImport] = useState(false)
  const [loadingExport, setLoadingExport] = useState(false)
  const [mostrarExcluidos, setMostrarExcluidos] = useState(false)

  const carregarLista = useCallback(async () => {
    setLoadingLista(true)
    try {
      const { data } = await contribuinteService.listar(mostrarExcluidos)
      setContribuintes(data)
    } catch (err) {
      setError(formatApiError(err, 'Erro ao carregar contribuintes.'))
    } finally {
      setLoadingLista(false)
    }
  }, [mostrarExcluidos])

  useEffect(() => {
    carregarLista()
  }, [carregarLista])

  const listaFiltrada = useMemo(() => {
    const t = filtro.trim().toLowerCase()
    if (!t) return contribuintes
    return contribuintes.filter((c) => {
      const email = (c.email || '').toLowerCase()
      const tel = (c.telefone || '').toLowerCase()
      return (
        c.nome_completo.toLowerCase().includes(t) ||
        (c.cpf || '').toLowerCase().includes(t) ||
        email.includes(t) ||
        tel.includes(t)
      )
    })
  }, [contribuintes, filtro])

  const abrirNovo = () => {
    setModalMode('create')
    setEditingId(null)
    setModalOpen(true)
  }

  const abrirEdicao = (id) => {
    setModalMode('edit')
    setEditingId(id)
    setModalOpen(true)
  }

  const fecharModal = () => {
    setModalOpen(false)
    setEditingId(null)
  }

  const handleSaved = async (mensagem) => {
    setSuccess(mensagem)
    setError('')
    await carregarLista()
  }

  const handleExport = async () => {
    setLoadingExport(true)
    setError('')
    try {
      const response = await exportService.exportarContribuintes()
      downloadBlobResponse(response, 'contribuintes.xlsx')
      setSuccess('Planilha de contribuintes exportada.')
    } catch (err) {
      setError(formatApiError(err, 'Erro ao exportar contribuintes.'))
    } finally {
      setLoadingExport(false)
    }
  }

  const handleImportApplied = async (data) => {
    setShowImport(false)
    setSuccess(
      `Importação concluída: ${data.importados} novo(s), ${data.atualizados} atualizado(s), ${data.pulados} pulado(s).`
    )
    setError('')
    await carregarLista()
  }

  const handleReativar = async (c) => {
    const ok = window.confirm(`Reativar o contribuinte "${c.nome_completo}"?`)
    if (!ok) return

    setReativandoId(c.id)
    setError('')
    setSuccess('')
    try {
      await contribuinteService.reativar(c.id)
      setSuccess(`Contribuinte "${c.nome_completo}" reativado.`)
      await carregarLista()
    } catch (err) {
      setError(formatApiError(err, 'Erro ao reativar contribuinte.'))
    } finally {
      setReativandoId(null)
    }
  }

  const handleExcluir = async (c) => {
    const ok = window.confirm(
      `Excluir o contribuinte "${c.nome_completo}"?\n\nO cadastro ficará na lista de excluídos.`
    )
    if (!ok) return

    setDeletingId(c.id)
    setError('')
    setSuccess('')
    try {
      await contribuinteService.excluir(c.id)
      setSuccess(`Contribuinte "${c.nome_completo}" excluído.`)
      await carregarLista()
    } catch (err) {
      setError(formatApiError(err, 'Erro ao excluir contribuinte.'))
    } finally {
      setDeletingId(null)
    }
  }

  return (
    <div className="page-grid">
      <div className="section-header">
        <div>
          <h2 className="page-title">Contribuintes</h2>
          <p className="page-description">
            {loadingLista
              ? 'Carregando cadastros...'
              : mostrarExcluidos
                ? `${contribuintes.length} contribuinte(s) excluído(s)`
                : `${contribuintes.length} contribuinte(s) ativo(s)`}
          </p>
        </div>
        <div className="page-header-actions">
          <button
            type="button"
            className={`btn ${mostrarExcluidos ? 'btn-primary' : 'btn-outline'}`}
            onClick={() => {
              setMostrarExcluidos((v) => !v)
              setFiltro('')
              setShowImport(false)
            }}
          >
            {mostrarExcluidos ? 'Ver ativos' : 'Ver excluídos'}
          </button>
          {!mostrarExcluidos && (
          <>
          <button
            type="button"
            className="btn btn-outline"
            onClick={handleExport}
            disabled={loadingExport}
          >
            {loadingExport ? 'Exportando...' : 'Exportar Excel'}
          </button>
          <button
            type="button"
            className="btn btn-outline"
            onClick={() => setShowImport((v) => !v)}
          >
            {showImport ? 'Ocultar importação' : 'Importar'}
          </button>
          <button type="button" className="btn btn-primary" onClick={abrirNovo}>
            Novo contribuinte
          </button>
          </>
          )}
        </div>
      </div>

      {showImport && !mostrarExcluidos && (
        <section className="card card-strong">
          <ContribuintesImportPanel
            onApplied={handleImportApplied}
            onClose={() => setShowImport(false)}
          />
        </section>
      )}

      {error && <div className="alert alert-error">{error}</div>}
      {success && <div className="alert alert-success">{success}</div>}

      <section className="card card-strong data-table-wrap">
        <div className="search-row lista-filtro-row">
          <label className="lista-filtro-field">
            Filtrar lista
            <input
              type="text"
              placeholder="Nome, CPF, e-mail ou telefone"
              value={filtro}
              onChange={(e) => setFiltro(e.target.value)}
            />
          </label>
          <button type="button" className="btn btn-outline" onClick={carregarLista} disabled={loadingLista}>
            Atualizar lista
          </button>
        </div>

        {loadingLista ? (
          <p className="text-muted">Carregando...</p>
        ) : listaFiltrada.length === 0 ? (
          <p className="text-muted">
            {mostrarExcluidos
              ? 'Nenhum contribuinte excluído encontrado.'
              : 'Nenhum contribuinte encontrado.'}
          </p>
        ) : (
          <table className="table table-contribuintes">
            <thead>
              <tr>
                <th>Nome</th>
                <th>CPF</th>
                <th>E-mail</th>
                <th>Telefone</th>
                <th className="col-acoes">Ações</th>
              </tr>
            </thead>
            <tbody>
              {listaFiltrada.map((c) => (
                <tr key={c.id} className={mostrarExcluidos ? 'row-excluido' : undefined}>
                  <td>
                    {c.nome_completo}
                    {mostrarExcluidos && <span className="badge-excluido">Excluído</span>}
                  </td>
                  <td className="cell-mono">{formatCpfDisplay(c.cpf)}</td>
                  <td>{c.email || '—'}</td>
                  <td className="cell-mono">{formatTelefoneDisplay(c.telefone)}</td>
                  <td className="col-acoes">
                    <div className="table-actions">
                      {mostrarExcluidos ? (
                        <button
                          type="button"
                          className="btn btn-icon btn-success"
                          onClick={() => handleReativar(c)}
                          disabled={reativandoId === c.id}
                          aria-label={`Reativar ${c.nome_completo}`}
                          title="Reativar"
                        >
                          <IconRestore />
                        </button>
                      ) : (
                        <>
                          <button
                            type="button"
                            className="btn btn-icon btn-outline"
                            onClick={() => abrirEdicao(c.id)}
                            aria-label={`Editar ${c.nome_completo}`}
                            title="Editar"
                          >
                            <IconEdit />
                          </button>
                          <button
                            type="button"
                            className="btn btn-icon btn-danger"
                            onClick={() => handleExcluir(c)}
                            disabled={deletingId === c.id}
                            aria-label={`Excluir ${c.nome_completo}`}
                            title="Excluir"
                          >
                            <IconTrash />
                          </button>
                        </>
                      )}
                    </div>
                  </td>
                </tr>
              ))}
            </tbody>
          </table>
        )}
        {!loadingLista && filtro.trim() && (
          <p className="text-muted mt-2">
            Exibindo {listaFiltrada.length} de {contribuintes.length} contribuinte(s).
          </p>
        )}
      </section>

      <ContribuinteFormModal
        open={modalOpen}
        mode={modalMode}
        contribuinteId={editingId}
        onClose={fecharModal}
        onSaved={handleSaved}
      />
    </div>
  )
}
