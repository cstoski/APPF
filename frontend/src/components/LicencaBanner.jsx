import { Link } from 'react-router-dom'
import { useLicenca } from '../hooks/useLicenca.jsx'
import { useAuth } from '../hooks/useAuth.jsx'

export default function LicencaBanner() {
  const { licenca, loading } = useLicenca()
  const { perfil } = useAuth()

  if (loading || !licenca) return null

  if (licenca.modo === 'GRACE') {
    return (
      <div className="licenca-banner licenca-banner-warning" role="status">
        Licença expirada — modo somente leitura por mais{' '}
        <strong>{licenca.grace_dias_restantes ?? 0}</strong> dia(s).{' '}
        {perfil === 'MASTER' ? (
          <Link to="/configuracao?tab=licenca">Renovar licença</Link>
        ) : (
          'Peça ao usuário MASTER para renovar.'
        )}
      </div>
    )
  }

  if (licenca.aviso_expiracao && licenca.dias_restantes != null) {
    return (
      <div className="licenca-banner licenca-banner-info" role="status">
        A licença deste computador expira em <strong>{licenca.dias_restantes}</strong> dia(s).{' '}
        {perfil === 'MASTER' ? (
          <Link to="/configuracao?tab=licenca">Ver licença</Link>
        ) : (
          'Solicite renovação ao MASTER.'
        )}
      </div>
    )
  }

  return null
}
