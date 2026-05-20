import { Outlet, useNavigate } from 'react-router-dom'
import { useAuth } from '../hooks/useAuth.jsx'
import Navbar from './Navbar'
import LicencaBanner from './LicencaBanner'
import LicencaBloqueioModal from './LicencaBloqueioModal'
import '../styles/layout.css'

export default function Layout() {
  const { username, logout } = useAuth()
  const navigate = useNavigate()

  const handleLogout = async () => {
    await logout()
    navigate('/login')
  }

  return (
    <div className="layout">
      <Navbar username={username} onLogout={handleLogout} />
      <LicencaBanner />
      <LicencaBloqueioModal />
      <main className="main-content">
        <div className="content-wrapper">
          <Outlet />
        </div>
      </main>
    </div>
  )
}
