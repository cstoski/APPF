import { useState } from 'react'
import { importService } from '../services/api'
import ImportPreview from '../components/ImportPreview'
import '../styles/importacao.css'

export default function ImportacaoPage() {
  const [file, setFile] = useState(null)
  const [preview, setPreview] = useState(null)
  const [loading, setLoading] = useState(false)
  const [error, setError] = useState('')
  const [modo, setModo] = useState('ATUALIZAR')

  const handleFileSelect = (e) => {
    const selected = e.target.files?.[0]
    if (selected) {
      setFile(selected)
      setPreview(null)
      setError('')
    }
  }

  const handlePreview = async () => {
    if (!file) {
      setError('Selecione um arquivo')
      return
    }

    setLoading(true)
    setError('')

    try {
      const response = await importService.getPreview(file)
      setPreview(response.data)
    } catch (err) {
      setError(err.response?.data?.detail || 'Erro ao gerar preview')
    } finally {
      setLoading(false)
    }
  }

  const handleApply = async (decisoes) => {
    if (!file) {
      setError('Arquivo não encontrado para aplicar a importação')
      return
    }

    setLoading(true)
    setError('')

    try {
      const response = await importService.aplicarDecisoes(file, decisoes, modo)
      alert(`✅ Importação concluída:\n${JSON.stringify(response.data, null, 2)}`)
      setFile(null)
      setPreview(null)
    } catch (err) {
      setError(err.response?.data?.detail || 'Erro ao aplicar importação')
    } finally {
      setLoading(false)
    }
  }

  return (
    <div className="importacao">
      <div className="importacao-header section-header">
        <div>
          <h2 className="page-title">Importação de Contribuintes</h2>
          <p className="page-description">Carregue seu arquivo para gerar preview, revisar por linha e aplicar a importação com segurança.</p>
        </div>

        <div className="import-summary-tags">
          <span className="tag">LGPD</span>
          <span className="tag">Preview</span>
          <span className="tag">Decisão por linha</span>
        </div>
      </div>

      <div className="importacao-section card card-strong">
        <div className="file-upload-box">
          <label htmlFor="file-input" className="file-label">
            <span>📁 Arraste ou selecione o arquivo</span>
            <small>.xlsx, .xls ou .csv</small>
          </label>
          <input
            id="file-input"
            type="file"
            onChange={handleFileSelect}
            accept=".xlsx,.xls,.csv"
            disabled={loading}
          />
        </div>

        {file && (
          <div className="file-selected card-strong">
            <div>
              <strong>Arquivo selecionado:</strong>
              <p>{file.name}</p>
            </div>
          </div>
        )}

        {error && <div className="alert alert-error">{error}</div>}

        <div className="import-controls">
          <div className="control-group">
            <label htmlFor="modo">Modo de importação</label>
            <select
              id="modo"
              value={modo}
              onChange={(e) => setModo(e.target.value)}
              disabled={loading}
            >
              <option value="ATUALIZAR">Atualizar duplicatas</option>
              <option value="PULAR">Pular duplicatas</option>
              <option value="REJEITAR">Rejeitar duplicatas</option>
            </select>
          </div>

          <button
            className="btn btn-primary btn-lg"
            onClick={handlePreview}
            disabled={!file || loading}
          >
            {loading ? '⏳ Gerando preview...' : '👁️ Gerar preview'}
          </button>
        </div>

        <div className="import-guidelines">
          <p><strong>Dica:</strong> revise o preview antes de aplicar. Linhas sem LGPD serão destacadas.</p>
        </div>
      </div>

      {preview && (
        <ImportPreview
          preview={preview}
          onApply={handleApply}
          loading={loading}
        />
      )}
    </div>
  )
}
