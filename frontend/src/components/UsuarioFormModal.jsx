import { useEffect, useState } from 'react'
import { PERFIS_CADASTRO, descricaoPerfil } from '../config/usuarioPerfis'
import { usuariosService } from '../services/api'
import { formatApiError } from '../utils/formatApiError'

const emptyForm = { username: '', password: '', perfil: 'OPERADOR' }

export default function UsuarioFormModal({ open, mode, usuario, onClose, onSaved }) {
  const [form, setForm] = useState(emptyForm)
  const [loading, setLoading] = useState(false)
  const [error, setError] = useState('')

  const isEdit = mode === 'edit'

  useEffect(() => {
    if (!open) return
    setError('')
    if (isEdit && usuario) {
      setForm({
        username: usuario.username || '',
        password: '',
        perfil: usuario.perfil === 'MASTER' ? 'MASTER' : 'OPERADOR',
      })
    } else {
      setForm(emptyForm)
    }
  }, [open, isEdit, usuario])

  if (!open) return null

  const handleSubmit = async (e) => {
    e.preventDefault()
    setLoading(true)
    setError('')
    const username = form.username.trim()
    try {
      if (isEdit) {
        const payload = { username, perfil: form.perfil }
        if (form.password.trim()) {
          payload.password = form.password
        }
        await usuariosService.atualizar(usuario.id, payload)
        onSaved(`Usuário "${username}" atualizado.`)
      } else {
        await usuariosService.criar({
          username,
          password: form.password,
          perfil: form.perfil,
          ativo: true,
        })
        onSaved(`Usuário "${username}" criado.`)
      }
      onClose()
    } catch (err) {
      setError(formatApiError(err, isEdit ? 'Erro ao atualizar usuário.' : 'Erro ao criar usuário.'))
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
        aria-labelledby="usuario-modal-title"
      >
        <div className="modal-header">
          <h3 id="usuario-modal-title">{isEdit ? 'Editar usuário' : 'Novo usuário'}</h3>
          <button type="button" className="btn btn-outline" onClick={onClose} aria-label="Fechar">
            Fechar
          </button>
        </div>

        {error && <div className="alert alert-error">{error}</div>}

        <form onSubmit={handleSubmit}>
          <div className="form-stack">
            <label>
              Nome de usuário
              <input
                value={form.username}
                onChange={(e) => setForm((prev) => ({ ...prev, username: e.target.value }))}
                required
                minLength={3}
                maxLength={80}
                autoComplete="username"
              />
            </label>
            <label>
              {isEdit ? (
                <>
                  Nova senha <span className="label-optional">(deixe em branco para manter)</span>
                </>
              ) : (
                'Senha'
              )}
              <input
                type="password"
                value={form.password}
                onChange={(e) => setForm((prev) => ({ ...prev, password: e.target.value }))}
                required={!isEdit}
                minLength={isEdit ? undefined : 6}
                autoComplete="new-password"
              />
            </label>
            <label>
              Nível de permissão
              <select
                value={form.perfil}
                onChange={(e) => setForm((prev) => ({ ...prev, perfil: e.target.value }))}
              >
                {PERFIS_CADASTRO.map((perfil) => (
                  <option key={perfil.value} value={perfil.value}>
                    {perfil.label}
                  </option>
                ))}
              </select>
            </label>
            <p className="form-field-hint">{descricaoPerfil(form.perfil)}</p>
            <details className="form-perfil-help">
              <summary>O que cada nível faz?</summary>
              <ul>
                {PERFIS_CADASTRO.map((perfil) => (
                  <li key={perfil.value}>
                    <strong>{perfil.label}</strong> — {perfil.descricao}
                  </li>
                ))}
              </ul>
            </details>
          </div>
          <div className="form-actions">
            <button type="button" className="btn btn-outline" onClick={onClose} disabled={loading}>
              Cancelar
            </button>
            <button type="submit" className="btn btn-primary" disabled={loading}>
              {loading ? 'Salvando...' : isEdit ? 'Salvar alterações' : 'Criar usuário'}
            </button>
          </div>
        </form>
      </div>
    </div>
  )
}
