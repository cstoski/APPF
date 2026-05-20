import { useState, useEffect } from 'react'
import { authService } from '../services/api'
import '../styles/dashboard.css'

export default function DashboardPage() {
  const [serverStatus, setServerStatus] = useState('checking')
  const [stats, setStats] = useState({
    contribuintes: 0,
    importacoes: 0,
    usuarios: 0
  })

  useEffect(() => {
    const checkServer = async () => {
      try {
        await authService.ping()
        setServerStatus('online')
      } catch {
        setServerStatus('offline')
      }
    }

    checkServer()
    const interval = setInterval(checkServer, 30000) // A cada 30s
    return () => clearInterval(interval)
  }, [])

  return (
    <div className="dashboard">
      <div className="dashboard-header">
        <h2>Dashboard</h2>
        <p>Status e estatísticas da aplicação</p>
      </div>

      <div className="status-bar">
        <div className={`status-indicator ${serverStatus}`}>
          <span className="dot"></span>
          Servidor: {serverStatus === 'online' ? '🟢 Online' : '🔴 Offline'}
        </div>
      </div>

      <div className="stats-grid">
        <div className="stat-card">
          <div className="stat-icon">👥</div>
          <div className="stat-content">
            <h3>Contribuintes</h3>
            <p className="stat-value">{stats.contribuintes}</p>
          </div>
        </div>

        <div className="stat-card">
          <div className="stat-icon">📥</div>
          <div className="stat-content">
            <h3>Importações</h3>
            <p className="stat-value">{stats.importacoes}</p>
          </div>
        </div>

        <div className="stat-card">
          <div className="stat-icon">🔐</div>
          <div className="stat-content">
            <h3>Usuários</h3>
            <p className="stat-value">{stats.usuarios}</p>
          </div>
        </div>
      </div>

      <div className="info-panel">
        <h3>ℹ️ Informações</h3>
        <ul>
          <li>✅ FastAPI + SQLAlchemy</li>
          <li>✅ React + Vite</li>
          <li>✅ Autenticação JWT</li>
          <li>✅ Criptografia de dados LGPD</li>
          <li>✅ Importação de contribuintes</li>
        </ul>
      </div>
    </div>
  )
}
