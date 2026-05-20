import { useState } from 'react'
import { authService } from '../services/api'
import { formatApiError } from '../utils/formatApiError'

export default function TrocarMinhaSenhaForm({ username, onSucesso, onErro }) {
  const [senhaAtual, setSenhaAtual] = useState('')
  const [novaSenha, setNovaSenha] = useState('')
  const [confirmarSenha, setConfirmarSenha] = useState('')
  const [loading, setLoading] = useState(false)

  const handleSubmit = async (e) => {
    e.preventDefault()
    if (novaSenha !== confirmarSenha) {
      onErro('A confirmação da nova senha não confere.')
      return
    }
    if (novaSenha.length < 6) {
      onErro('A nova senha deve ter no mínimo 6 caracteres.')
      return
    }

    setLoading(true)
    onErro('')
    try {
      const { data } = await authService.trocarSenha(senhaAtual, novaSenha)
      setSenhaAtual('')
      setNovaSenha('')
      setConfirmarSenha('')
      onSucesso(data.mensagem || 'Senha alterada com sucesso.')
    } catch (err) {
      onErro(formatApiError(err, 'Não foi possível alterar a senha.'))
    } finally {
      setLoading(false)
    }
  }

  return (
    <form onSubmit={handleSubmit} className="form-stack trocar-senha-form">
      <p className="text-muted">
        Usuário: <strong>{username}</strong>
      </p>
      <label>
        Senha atual
        <input
          type="password"
          value={senhaAtual}
          onChange={(e) => setSenhaAtual(e.target.value)}
          required
          autoComplete="current-password"
        />
      </label>
      <label>
        Nova senha
        <input
          type="password"
          value={novaSenha}
          onChange={(e) => setNovaSenha(e.target.value)}
          required
          minLength={6}
          autoComplete="new-password"
        />
      </label>
      <label>
        Confirmar nova senha
        <input
          type="password"
          value={confirmarSenha}
          onChange={(e) => setConfirmarSenha(e.target.value)}
          required
          minLength={6}
          autoComplete="new-password"
        />
      </label>
      <div className="form-actions">
        <button type="submit" className="btn btn-primary" disabled={loading}>
          {loading ? 'Salvando...' : 'Alterar senha'}
        </button>
      </div>
    </form>
  )
}
