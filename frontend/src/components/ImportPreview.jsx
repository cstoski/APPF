import { useMemo, useState } from 'react'
import '../styles/import-preview.css'

function acaoPadrao(item) {
  if (item.sugestao_acao) return item.sugestao_acao
  if (item.status === 'NOVO') return 'IMPORTAR'
  return 'PULAR'
}

export default function ImportPreview({ preview, onApply, loading }) {
  const [decisoes, setDecisoes] = useState({})
  const [filterText, setFilterText] = useState('')

  const handleDecisao = (linha, acao) => {
    setDecisoes((prev) => ({ ...prev, [linha]: acao }))
  }

  const handleMarcarTodos = (acao) => {
    const novas = {}
    preview.itens?.forEach((item) => {
      novas[item.linha] = acao
    })
    setDecisoes(novas)
  }

  const handleApply = () => {
    const decisoesArray = (preview.itens || []).map((item) => ({
      linha: item.linha,
      acao: decisoes[item.linha] || acaoPadrao(item),
    }))
    onApply(decisoesArray)
  }

  const filteredItems = useMemo(() => {
    const t = filterText.trim().toLowerCase()
    if (!t) return preview.itens || []
    return (preview.itens || []).filter((item) => {
      const haystack = `${item.nome_completo} ${item.cpf} ${item.email || ''} ${item.telefone || ''}`
      return haystack.toLowerCase().includes(t)
    })
  }, [preview.itens, filterText])

  return (
    <div className="import-preview">
      <div className="preview-header">
        <h3>Preview de Importação</h3>
        <div className="preview-stats">
          <span className="stat">Total: {preview.total_linhas}</span>
          <span className="stat">Novos: {preview.novos}</span>
          <span className="stat">Duplicados: {preview.duplicados}</span>
          <span className="stat">Inválidos: {preview.invalidos}</span>
        </div>
      </div>

      <p className="text-muted import-hint">
        Colunas: nome_completo (obrigatório), cpf, e-mail e telefone (opcionais). Linhas novas são
        importadas quando não houver nome nem CPF igual a um contribuinte ativo.
      </p>

      <div className="preview-controls">
        <input
          type="text"
          placeholder="Filtrar por nome, CPF, e-mail ou telefone..."
          value={filterText}
          onChange={(e) => setFilterText(e.target.value)}
          className="filter-input"
        />

        <div className="action-buttons">
          <button
            type="button"
            className="btn btn-outline"
            onClick={() => handleMarcarTodos('IMPORTAR')}
            disabled={loading}
          >
            Importar todos
          </button>
          <button
            type="button"
            className="btn btn-outline"
            onClick={() => handleMarcarTodos('PULAR')}
            disabled={loading}
          >
            Pular todos
          </button>
        </div>
      </div>

      <div className="preview-table">
        <table>
          <thead>
            <tr>
              <th>#</th>
              <th>Nome</th>
              <th>CPF</th>
              <th>E-mail</th>
              <th>Telefone</th>
              <th>Status</th>
              <th>Ação</th>
            </tr>
          </thead>
          <tbody>
            {filteredItems.map((item) => (
              <tr key={item.linha} className={`status-${item.status}`}>
                <td>{item.linha}</td>
                <td>{item.nome_completo}</td>
                <td>{item.cpf || '—'}</td>
                <td>{item.email || '—'}</td>
                <td>{item.telefone || '—'}</td>
                <td>
                  <span className={`badge badge-${item.status}`}>{item.status}</span>
                  {item.erros?.length > 0 && (
                    <small className="import-erros">{item.erros.join('; ')}</small>
                  )}
                </td>
                <td>
                  <select
                    value={decisoes[item.linha] || acaoPadrao(item)}
                    onChange={(e) => handleDecisao(item.linha, e.target.value)}
                    disabled={loading || item.status === 'INVALIDO'}
                    className="action-select"
                  >
                    <option value="IMPORTAR">Importar</option>
                    <option value="PULAR">Pular</option>
                    <option value="ATUALIZAR">Atualizar existente</option>
                  </select>
                </td>
              </tr>
            ))}
          </tbody>
        </table>
      </div>

      <div className="preview-footer">
        <button
          type="button"
          className="btn btn-primary btn-lg"
          onClick={handleApply}
          disabled={loading || filteredItems.length === 0}
        >
          {loading ? 'Processando...' : 'Aplicar importação'}
        </button>
      </div>
    </div>
  )
}
