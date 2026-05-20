import { useState, useEffect } from 'react'
import { Link } from 'react-router-dom'
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
    const interval = setInterval(checkServer, 30000)
    return () => clearInterval(interval)
  }, [])

  return (
    <div className="dashboard">
      <div className="dashboard-header section-header">
        <div>
          <h2 className="page-title">Resumo do Sistema</h2>
          <p className="page-description">Acompanhe o status do servidor, importações e principais informações do APPF.</p>
        </div>
        <Link to="/importacao" className="btn btn-primary">
          Ir para importação
        </Link>
      </div>

      <div className="dashboard-grid">
        <section className="card card-strong">
          <div className="status-block">
            <span className={`status-badge ${serverStatus}`}></span>
            <div>
              <p className="text-muted">Servidor</p>
              <h3>{serverStatus === 'online' ? 'Online' : 'Offline'}</h3>
            </div>
          </div>
          <p className="text-muted">Verificação automática a cada 30 segundos.</p>
        </section>

        <section className="card stats-card">
          <div className="stat-item">
            <p className="text-muted">Contribuintes</p>
            <h3>{stats.contribuintes}</h3>
          </div>
          <div className="stat-item">
            <p className="text-muted">Importações</p>
            <h3>{stats.importacoes}</h3>
          </div>
          <div className="stat-item">
            <p className="text-muted">Usuários</p>
            <h3>{stats.usuarios}</h3>
          </div>
        </section>

        <section className="card card-strong info-panel">
          <h3>Visão Geral</h3>
          <ul>
            <li>Controle de importação com aprovação por linha.</li>
            <li>Dados criptografados conforme LGPD.</li>
            <li>Autenticação JWT para rotas seguras.</li>
            <li>Fluxo de preview antes de aplicar</li>
          </ul>
        </section>
      </div>
    </div>
  )
}
