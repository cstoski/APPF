import { useState } from 'react'
import '../styles/import-preview.css'

export default function ImportPreview({ preview, onApply, loading }) {
  const [decisoes, setDecisoes] = useState({})
  const [filterText, setFilterText] = useState('')

  const handleDecisao = (linha, acao) => {
    setDecisoes((prev) => ({
      ...prev,
      [linha]: acao
    }))
  }

  const handleMarcarTodos = (acao) => {
    const novasDecisoes = {}
    preview.itens?.forEach((item, idx) => {
      novasDecisoes[idx] = acao
    })
    setDecisoes(novasDecisoes)
  }

  const handleApply = () => {
    const decisoesArray = Object.entries(decisoes).map(([linha, acao]) => ({
      linha: parseInt(linha),
      acao
    }))
    onApply(decisoesArray)
  }

  const filteredItems = preview.itens?.filter((item) => {
    const haystack = `${item.nome_completo} ${item.cpf} ${item.email}`
      .toLowerCase()
    return haystack.includes(filterText.toLowerCase())
  }) || []

  return (
    <div className="import-preview">
      <div className="preview-header">
        <h3>Preview de Importação</h3>
        <div className="preview-stats">
          <span className="stat">📊 Total: {preview.total_linhas}</span>
          <span className="stat">🆕 Novos: {preview.novos}</span>
          <span className="stat">🔄 Duplicados: {preview.duplicados}</span>
          <span className="stat">❌ Inválidos: {preview.invalidos}</span>
          <span className="stat">🚫 Sem LGPD: {preview.sem_consentimento}</span>
        </div>
      </div>

      <div className="preview-controls">
        <input
          type="text"
          placeholder="🔍 Filtrar por nome, CPF ou email..."
          value={filterText}
          onChange={(e) => setFilterText(e.target.value)}
          className="filter-input"
        />

        <div className="action-buttons">
          <button
            className="btn btn-outline"
            onClick={() => handleMarcarTodos('INCLUIR')}
            disabled={loading}
          >
            ✓ Marcar Todos
          </button>
          <button
            className="btn btn-outline"
            onClick={() => handleMarcarTodos('IGNORAR')}
            disabled={loading}
          >
            ✗ Ignorar Todos
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
              <th>Email</th>
              <th>Status</th>
              <th>Ação</th>
            </tr>
          </thead>
          <tbody>
            {filteredItems.map((item, idx) => (
              <tr key={idx} className={`status-${item.status}`}>
                <td>{item.linha}</td>
                <td>{item.nome_completo}</td>
                <td>{item.cpf}</td>
                <td>{item.email}</td>
                <td>
                  <span className={`badge badge-${item.status}`}>
                    {item.status}
                  </span>
                </td>
                <td>
                  <select
                    value={decisoes[idx] || 'INCLUIR'}
                    onChange={(e) => handleDecisao(idx, e.target.value)}
                    disabled={loading}
                    className="action-select"
                  >
                    <option value="INCLUIR">✓ Incluir</option>
                    <option value="IGNORAR">✗ Ignorar</option>
                  </select>
                </td>
              </tr>
            ))}
          </tbody>
        </table>
      </div>

      <div className="preview-footer">
        <button
          className="btn btn-primary btn-lg"
          onClick={handleApply}
          disabled={loading || filteredItems.length === 0}
        >
          {loading ? '⏳ Processando...' : '✓ Aplicar Importação'}
        </button>
      </div>
    </div>
  )
}
