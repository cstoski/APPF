import { useState } from 'react'
import { importService } from '../services/api'
import { formatApiError } from '../utils/formatApiError'
import ImportPreview from './ImportPreview'
import '../styles/importacao.css'

export default function ContribuintesImportPanel({ onApplied, onClose }) {
  const [file, setFile] = useState(null)
  const [preview, setPreview] = useState(null)
  const [loading, setLoading] = useState(false)
  const [error, setError] = useState('')
  const [modo] = useState('PULAR')

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
      setError('Selecione um arquivo.')
      return
    }

    setLoading(true)
    setError('')
    try {
      const response = await importService.getPreview(file)
      setPreview(response.data)
    } catch (err) {
      setError(formatApiError(err, 'Erro ao gerar preview.'))
    } finally {
      setLoading(false)
    }
  }

  const handleApply = async (decisoes) => {
    if (!file) {
      setError('Arquivo não encontrado para aplicar a importação.')
      return
    }

    setLoading(true)
    setError('')
    try {
      const response = await importService.aplicarDecisoes(file, decisoes, modo)
      setFile(null)
      setPreview(null)
      onApplied?.(response.data)
    } catch (err) {
      setError(formatApiError(err, 'Erro ao aplicar importação.'))
    } finally {
      setLoading(false)
    }
  }

  return (
    <div className="contribuintes-import-panel">
      <div className="import-panel-toolbar">
        <h3>Importar contribuintes</h3>
        {onClose && (
          <button type="button" className="btn btn-outline" onClick={onClose} disabled={loading}>
            Fechar
          </button>
        )}
      </div>

      <section className="importacao-section card-strong">
        <div className="file-upload-box">
          <label htmlFor="contrib-import-file" className="file-label">
            <span>Arraste ou selecione o arquivo</span>
            <small>.xlsx, .xls ou .csv</small>
          </label>
          <input
            id="contrib-import-file"
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
          <button
            type="button"
            className="btn btn-primary"
            onClick={handlePreview}
            disabled={!file || loading}
          >
            {loading ? 'Gerando preview...' : 'Gerar preview'}
          </button>
        </div>

        <p className="text-muted import-guidelines">
          Planilha com colunas: nome_completo (obrigatório), cpf, e-mail e telefone (opcionais).
          Permite nomes iguais com CPF diferente. Bloqueia quando o CPF já existir (mesmo nome e mesmo CPF).
        </p>
      </section>

      {preview && <ImportPreview preview={preview} onApply={handleApply} loading={loading} />}
    </div>
  )
}
