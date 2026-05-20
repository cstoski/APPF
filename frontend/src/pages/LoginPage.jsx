import { useState } from 'react'
import { useNavigate } from 'react-router-dom'
import { useAuth } from '../hooks/useAuth'
import { authService } from '../services/api'
import '../styles/login.css'

export default function LoginPage() {
  const [username, setUsername] = useState('admin')
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
      navigate('/dashboard')
    } catch (err) {
      setError(err.response?.data?.detail || 'Erro ao fazer login')
    } finally {
      setLoading(false)
    }
  }

  return (
    <div className="login-page">
      <div className="login-panel card card-strong">
        <div className="login-banner">
          <div>
            <h1>APPF</h1>
            <p>Login seguro para gerenciar importações aprovadas.</p>
          </div>
        </div>

        <div className="login-body">
          <div className="login-title">
            <h2>Bem-vindo de volta</h2>
            <p>Entre para continuar e acessar o painel de importação.</p>
          </div>

          <form onSubmit={handleSubmit} className="login-form">
            <label htmlFor="username">Usuário</label>
            <input
              id="username"
              type="text"
              value={username}
              onChange={(e) => setUsername(e.target.value)}
              placeholder="admin"
              disabled={loading}
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

          <div className="login-tips">
            <p>Use o usuário `admin` com a senha cadastrada no sistema.</p>
            <p>O token é armazenado apenas nesta sessão.</p>
          </div>
        </div>
      </div>
    </div>
  )
}
