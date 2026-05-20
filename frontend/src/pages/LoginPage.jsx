import { useState } from 'react'
import { useNavigate } from 'react-router-dom'
import { useAuth } from '../hooks/useAuth.jsx'
import { authService } from '../services/api'
import { formatApiError } from '../utils/formatApiError'
import '../styles/login.css'

export default function LoginPage() {
  const [username, setUsername] = useState('')
  const [password, setPassword] = useState('')
  const [error, setError] = useState('')
  const [loading, setLoading] = useState(false)
  const { login } = useAuth()
  const navigate = useNavigate()

  const handleSubmit = async (e) => {
    e.preventDefault()
    setError('')
    setLoading(true)

    try {
      const response = await authService.login(username, password)
      const token = response.data.access_token
      login(token, username)
      navigate('/dashboard', { replace: true })
    } catch (err) {
      setError(formatApiError(err, 'Erro ao fazer login. Verifique se o backend está rodando.'))
    } finally {
      setLoading(false)
    }
  }

  return (
    <div className="login-page">
      <div className="login-panel card card-strong">
        <div className="login-brand">
          <div className="login-logo-frame">
            <img src="/images/zelo-appf.png" alt="Zelo APPF" className="login-logo" />
          </div>
          <p className="login-brand-lead">
            Sistema de Gestão de Contribuições Voluntárias APPF
          </p>
        </div>

        <div className="login-body">
          <div className="login-title">
            <h2>Acesso ao sistema</h2>
          </div>

          <form onSubmit={handleSubmit} className="login-form">
            <label htmlFor="username">Usuário</label>
            <input
              id="username"
              type="text"
              value={username}
              onChange={(e) => setUsername(e.target.value)}
              placeholder="Informe seu usuário"
              disabled={loading}
              autoComplete="username"
            />

            <label htmlFor="password">Senha</label>
            <input
              id="password"
              type="password"
              value={password}
              onChange={(e) => setPassword(e.target.value)}
              placeholder="••••••••"
              disabled={loading}
            />

            {error && <div className="alert alert-error">{error}</div>}

            <button
              type="submit"
              className="btn btn-primary btn-block"
              disabled={loading}
            >
              {loading ? 'Autenticando...' : 'Entrar'}
            </button>
          </form>
        </div>
      </div>
    </div>
  )
}
