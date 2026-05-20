import { useEffect, useState } from 'react'
import { authService } from '../services/api'

const LABELS = {
  checking: 'Verificando API…',
  online: 'Servidor API online',
  offline: 'Servidor API offline',
}

export default function ApiServerStatus() {
  const [status, setStatus] = useState('checking')

  useEffect(() => {
    let ativo = true

    const verificar = async () => {
      try {
        await authService.ping()
        if (ativo) setStatus('online')
      } catch {
        if (ativo) setStatus('offline')
      }
    }

    verificar()
    const interval = setInterval(verificar, 30000)
    return () => {
      ativo = false
      clearInterval(interval)
    }
  }, [])

  return (
    <div
      className="navbar-api-status"
      title={LABELS[status]}
      aria-live="polite"
      aria-label={LABELS[status]}
    >
      <span className={`navbar-status-dot ${status}`} aria-hidden="true" />
      <span className="navbar-api-status-label">Servidor API</span>
      <span className="navbar-api-status-value">
        {status === 'checking' ? '…' : status === 'online' ? 'Online' : 'Offline'}
      </span>
    </div>
  )
}
