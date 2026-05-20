import { useEffect, useState } from 'react'
import { Link } from 'react-router-dom'
import { contribuinteService } from '../services/api'
import { formatApiError } from '../utils/formatApiError'
import { enviarReciboEmailComPdf, prepararEnvioReciboEmail } from '../utils/reciboShare'

export default function EnviarReciboEmailModal({
  open,
  recibo,
  contribuinte,
  configAppf,
  opcoesPdf = {},
  onClose,
  onEnviado,
}) {
  const [form, setForm] = useState({
    destinatario_email: '',
    assunto: '',
    corpo_texto: '',
    nome_anexo: '',
  })
  const [loading, setLoading] = useState(false)
  const [loadingData, setLoadingData] = useState(false)
  const [error, setError] = useState('')

  useEffect(() => {
    if (!open || !recibo) return

    let cancelled = false
    const carregar = async () => {
      setLoadingData(true)
      setError('')
      try {
        let contrib = contribuinte
        if (contribuinte?.id) {
          try {
            const { data } = await contribuinteService.obter(contribuinte.id)
            contrib = { ...contribuinte, ...data }
          } catch {
            /* usa dados parciais */
          }
        }
        if (!cancelled) {
          const preparado = await prepararEnvioReciboEmail(recibo, contrib, configAppf)
          setForm(preparado)
        }
      } catch (err) {
        if (!cancelled) {
          setError(err?.message || 'Não foi possível preparar o e-mail.')
        }
      } finally {
        if (!cancelled) setLoadingData(false)
      }
    }

    carregar()
    return () => {
      cancelled = true
    }
  }, [open, recibo, contribuinte, configAppf])

  if (!open || !recibo) return null

  const handleChange = (e) => {
    const { name, value } = e.target
    setForm((prev) => ({ ...prev, [name]: value }))
  }

  const handleSubmit = async (e) => {
    e.preventDefault()
    if (!form.destinatario_email.trim()) {
      setError('Informe o e-mail do destinatário.')
      return
    }
    setLoading(true)
    setError('')
    try {
      const data = await enviarReciboEmailComPdf(recibo, contribuinte, configAppf, form, opcoesPdf)
      onEnviado?.(data?.mensagem || 'E-mail enfileirado para envio.')
      onClose()
    } catch (err) {
      setError(formatApiError(err, 'Não foi possível enviar o e-mail.'))
    } finally {
      setLoading(false)
    }
  }

  const smtpNaoConfigurado =
    error && /configuração\s*>\s*e-mail|servidor smtp/i.test(error)

  return (
    <div className="modal-overlay" onClick={onClose} role="presentation">
      <div
        className="modal-panel card card-strong"
        onClick={(e) => e.stopPropagation()}
        role="dialog"
        aria-modal="true"
        aria-labelledby="recibo-email-modal-title"
      >
        <div className="modal-header">
          <h3 id="recibo-email-modal-title">Enviar recibo por e-mail</h3>
          <button type="button" className="btn btn-outline" onClick={onClose} aria-label="Fechar">
            Fechar
          </button>
        </div>

        {error && (
          <div className="alert alert-error">
            {error}
            {smtpNaoConfigurado && (
              <p className="mt-2">
                <Link to="/configuracao?tab=email" onClick={onClose}>
                  Ir para Configuração &gt; E-mail
                </Link>
              </p>
            )}
          </div>
        )}

        {loadingData ? (
          <p className="text-muted">Preparando e-mail e PDF...</p>
        ) : (
          <form onSubmit={handleSubmit}>
            <div className="form-stack">
              <label>
                Destinatário
                <input
                  name="destinatario_email"
                  type="email"
                  value={form.destinatario_email}
                  onChange={handleChange}
                  required
                  autoComplete="email"
                  placeholder="e-mail do contribuinte"
                />
              </label>
              <label>
                Assunto
                <input name="assunto" value={form.assunto} onChange={handleChange} required maxLength={200} />
              </label>
              <label>
                Mensagem
                <textarea
                  name="corpo_texto"
                  value={form.corpo_texto}
                  onChange={handleChange}
                  rows={8}
                  required
                />
              </label>
              <p className="text-muted recibo-email-anexo-info">
                Anexo: <strong>{form.nome_anexo || 'PDF do recibo'}</strong> (gerado automaticamente)
              </p>
            </div>

            <div className="form-actions">
              <button type="button" className="btn btn-outline" onClick={onClose} disabled={loading}>
                Cancelar
              </button>
              <button type="submit" className="btn btn-primary" disabled={loading || loadingData}>
                {loading ? 'Enviando...' : 'Enviar e-mail'}
              </button>
            </div>
          </form>
        )}
      </div>
    </div>
  )
}
