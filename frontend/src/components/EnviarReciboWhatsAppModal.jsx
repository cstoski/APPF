import { useEffect, useState } from 'react'
import { contribuinteService } from '../services/api'
import { formatApiError } from '../utils/formatApiError'
import { formatTelefoneInput } from '../utils/masks'
import { enviarReciboWhatsAppComPdf, prepararEnvioReciboWhatsApp } from '../utils/reciboShare'

export default function EnviarReciboWhatsAppModal({
  open,
  recibo,
  contribuinte,
  configAppf,
  onClose,
  onEnviado,
}) {
  const [form, setForm] = useState({
    telefone: '',
    mensagem: '',
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
          const preparado = await prepararEnvioReciboWhatsApp(recibo, contrib, configAppf)
          setForm(preparado)
        }
      } catch (err) {
        if (!cancelled) {
          setError(err?.message || 'Não foi possível preparar o envio.')
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
    if (name === 'telefone') {
      setForm((prev) => ({ ...prev, telefone: formatTelefoneInput(value) }))
      return
    }
    setForm((prev) => ({ ...prev, [name]: value }))
  }

  const handleSubmit = async (e) => {
    e.preventDefault()
    if (!form.telefone.trim()) {
      setError('Informe o telefone do destinatário.')
      return
    }
    setLoading(true)
    setError('')
    try {
      const data = await enviarReciboWhatsAppComPdf(recibo, contribuinte, configAppf, form)
      if (data?.modo === 'cancelado') {
        onClose()
        return
      }
      if (data?.mensagem) {
        onEnviado?.(data.mensagem, form.telefone.trim())
      }
      onClose()
    } catch (err) {
      setError(formatApiError(err, 'Não foi possível abrir o WhatsApp.'))
    } finally {
      setLoading(false)
    }
  }

  return (
    <div className="modal-overlay" onClick={onClose} role="presentation">
      <div
        className="modal-panel card card-strong"
        onClick={(e) => e.stopPropagation()}
        role="dialog"
        aria-modal="true"
        aria-labelledby="recibo-whatsapp-modal-title"
      >
        <div className="modal-header">
          <h3 id="recibo-whatsapp-modal-title">Enviar recibo por WhatsApp</h3>
          <button type="button" className="btn btn-outline" onClick={onClose} aria-label="Fechar">
            Fechar
          </button>
        </div>

        {error && <div className="alert alert-error">{error}</div>}

        {loadingData ? (
          <p className="text-muted">Preparando mensagem...</p>
        ) : (
          <form onSubmit={handleSubmit}>
            <div className="form-stack">
              <label>
                Telefone (WhatsApp)
                <input
                  name="telefone"
                  type="tel"
                  value={form.telefone}
                  onChange={handleChange}
                  required
                  autoComplete="tel"
                  placeholder="(00) 00000-0000"
                  inputMode="tel"
                  maxLength={15}
                />
              </label>
              <label>
                Mensagem
                <textarea
                  name="mensagem"
                  value={form.mensagem}
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
              <button type="submit" className="btn btn-whatsapp" disabled={loading || loadingData}>
                {loading ? 'Abrindo...' : 'Abrir WhatsApp'}
              </button>
            </div>
          </form>
        )}
      </div>
    </div>
  )
}
