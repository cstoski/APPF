import { useEffect, useState } from 'react'
import { contribuinteService } from '../services/api'
import { formatApiError } from '../utils/formatApiError'
import { formatCpfInput, formatTelefoneInput } from '../utils/masks'

const emptyForm = {
  nome_completo: '',
  cpf: '',
  email: '',
  telefone: '',
  observacoes: '',
}

export default function ContribuinteFormModal({
  open,
  mode,
  contribuinteId,
  initialForm = null,
  onClose,
  onSaved,
}) {
  const [form, setForm] = useState(emptyForm)
  const [loading, setLoading] = useState(false)
  const [loadingData, setLoadingData] = useState(false)
  const [error, setError] = useState('')

  const isEdit = mode === 'edit'

  useEffect(() => {
    if (!open) return

    setError('')
    if (!isEdit) {
      setForm(initialForm ? { ...emptyForm, ...initialForm } : emptyForm)
      return
    }

    let cancelled = false
    const carregar = async () => {
      setLoadingData(true)
      try {
        const { data } = await contribuinteService.obter(contribuinteId)
        if (!cancelled) {
          setForm({
            nome_completo: data.nome_completo || '',
            cpf: formatCpfInput(data.cpf || ''),
            email: data.email || '',
            telefone: formatTelefoneInput(data.telefone || ''),
            observacoes: data.observacoes || '',
          })
        }
      } catch (err) {
        if (!cancelled) {
          setError(formatApiError(err, 'Erro ao carregar contribuinte.'))
        }
      } finally {
        if (!cancelled) setLoadingData(false)
      }
    }

    carregar()
    return () => {
      cancelled = true
    }
  }, [open, isEdit, contribuinteId, initialForm])

  if (!open) return null

  const handleChange = (e) => {
    const { name, value } = e.target
    let next = value
    if (name === 'cpf') next = formatCpfInput(value)
    if (name === 'telefone') next = formatTelefoneInput(value)
    setForm((prev) => ({ ...prev, [name]: next }))
  }

  const handleSubmit = async (e) => {
    e.preventDefault()
    setLoading(true)
    setError('')
    const payload = {
      nome_completo: form.nome_completo.trim(),
      cpf: form.cpf.trim() ? form.cpf : null,
      email: form.email || null,
      telefone: form.telefone || null,
      observacoes: form.observacoes || null,
    }
    try {
      if (isEdit) {
        await contribuinteService.atualizar(contribuinteId, payload)
        onSaved(`Contribuinte "${form.nome_completo}" atualizado.`)
      } else {
        const { data } = await contribuinteService.criar({
          ...payload,
          consentimento_lgpd: true,
        })
        onSaved(`Contribuinte "${data.nome_completo}" cadastrado.`, {
          id: data.id,
          nome_completo: data.nome_completo,
          cpf: form.cpf,
        })
      }
      onClose()
    } catch (err) {
      setError(formatApiError(err, isEdit ? 'Erro ao atualizar contribuinte.' : 'Erro ao cadastrar contribuinte.'))
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
        aria-labelledby="contribuinte-modal-title"
      >
        <div className="modal-header">
          <h3 id="contribuinte-modal-title">{isEdit ? 'Editar contribuinte' : 'Novo contribuinte'}</h3>
          <button type="button" className="btn btn-outline" onClick={onClose} aria-label="Fechar">
            Fechar
          </button>
        </div>

        {error && <div className="alert alert-error">{error}</div>}

        {loadingData ? (
          <p className="text-muted">Carregando...</p>
        ) : (
          <form onSubmit={handleSubmit}>
            <div className="form-stack">
              <label>
                Nome completo
                <input name="nome_completo" value={form.nome_completo} onChange={handleChange} required />
              </label>
              <label>
                CPF <span className="label-optional">(opcional)</span>
                <input
                  name="cpf"
                  value={form.cpf}
                  onChange={handleChange}
                  placeholder="000.000.000-00"
                  inputMode="numeric"
                  maxLength={14}
                />
              </label>
              <label>
                E-mail <span className="label-optional">(opcional)</span>
                <input
                  name="email"
                  type="text"
                  value={form.email}
                  onChange={handleChange}
                  autoComplete="email"
                />
              </label>
              <label>
                Telefone
                <input
                  name="telefone"
                  value={form.telefone}
                  onChange={handleChange}
                  placeholder="(00) 00000-0000"
                  inputMode="tel"
                  maxLength={15}
                />
              </label>
              <label>
                Observações
                <textarea name="observacoes" value={form.observacoes} onChange={handleChange} rows={3} />
              </label>
            </div>
            <div className="form-actions">
              <button type="button" className="btn btn-outline" onClick={onClose} disabled={loading}>
                Cancelar
              </button>
              <button type="submit" className="btn btn-primary" disabled={loading || loadingData}>
                {loading ? 'Salvando...' : isEdit ? 'Salvar alterações' : 'Cadastrar'}
              </button>
            </div>
          </form>
        )}
      </div>
    </div>
  )
}
