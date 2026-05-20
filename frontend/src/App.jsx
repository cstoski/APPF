import { Routes, Route, Navigate } from 'react-router-dom'
import { useAuth } from './hooks/useAuth.jsx'
import Layout from './components/Layout'
import LoginPage from './pages/LoginPage'
import DashboardPage from './pages/DashboardPage'
import ImportacaoPage from './pages/ImportacaoPage'
import ContribuintesPage from './pages/ContribuintesPage'
import ContribuicoesPage from './pages/ContribuicoesPage'
import RelatoriosPage from './pages/RelatoriosPage'
import ConfiguracaoPage from './pages/ConfiguracaoPage'
import UsuariosPage from './pages/UsuariosPage'

function ProtectedLayout() {
  const { token } = useAuth()
  if (!token) {
    return <Navigate to="/login" replace />
  }
  return <Layout />
}

export default function App() {
  const { token, loading } = useAuth()

  if (loading) {
    return (
      <div className="app-loading" style={{ padding: '2rem', textAlign: 'center' }}>
        Carregando...
      </div>
    )
  }

  return (
    <Routes>
      <Route
        path="/login"
        element={token ? <Navigate to="/dashboard" replace /> : <LoginPage />}
      />
      <Route element={<ProtectedLayout />}>
        <Route path="/dashboard" element={<DashboardPage />} />
        <Route path="/contribuintes" element={<ContribuintesPage />} />
        <Route path="/contribuicoes" element={<ContribuicoesPage />} />
        <Route path="/relatorios" element={<RelatoriosPage />} />
        <Route path="/importacao" element={<ImportacaoPage />} />
        <Route path="/configuracao" element={<ConfiguracaoPage />} />
        <Route path="/usuarios" element={<UsuariosPage />} />
      </Route>
      <Route path="/" element={<Navigate to={token ? '/dashboard' : '/login'} replace />} />
      <Route path="*" element={<Navigate to={token ? '/dashboard' : '/login'} replace />} />
    </Routes>
  )
}
