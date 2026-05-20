import { useState } from 'react'
import { exportService, downloadBlobResponse } from '../services/api'
import { formatApiError } from '../utils/formatApiError'
import ContribuintesImportPanel from '../components/ContribuintesImportPanel'
import '../styles/importacao.css'

export default function ImportacaoPage() {
  const [loading, setLoading] = useState(false)
  const [error, setError] = useState('')
  const [success, setSuccess] = useState('')

  const handleExport = async () => {
    setLoading(true)
    setError('')
    try {
      const response = await exportService.exportarContribuintes()
      downloadBlobResponse(response, 'contribuintes.xlsx')
    } catch (err) {
      setError(formatApiError(err, 'Erro ao exportar contribuintes.'))
    } finally {
      setLoading(false)
    }
  }

  const handleApplied = (data) => {
    setSuccess(
      `Importação concluída: ${data.importados} novo(s), ${data.atualizados} atualizado(s), ${data.pulados} pulado(s).`
    )
    setError('')
  }

  return (
    <div className="importacao">
      <div className="importacao-header section-header">
        <div>
          <h2 className="page-title">Importação de Contribuintes</h2>
          <p className="page-description">
            Carregue seu arquivo para gerar preview, revisar por linha e aplicar a importação com segurança.
          </p>
        </div>

        <div className="import-summary-tags">
          <span className="tag">LGPD</span>
          <span className="tag">Preview</span>
          <span className="tag">Decisão por linha</span>
          <button type="button" className="btn btn-outline" onClick={handleExport} disabled={loading}>
            Exportar Excel
          </button>
        </div>
      </div>

      {error && <div className="alert alert-error">{error}</div>}
      {success && <div className="alert alert-success">{success}</div>}

      <ContribuintesImportPanel onApplied={handleApplied} />
    </div>
  )
}
