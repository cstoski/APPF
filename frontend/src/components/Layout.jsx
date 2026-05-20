import { Outlet, useNavigate } from 'react-router-dom'
import { useAuth } from '../hooks/useAuth'
import Navbar from './Navbar'
import '../styles/layout.css'

export default function Layout() {
  const { username, logout } = useAuth()
  const navigate = useNavigate()

  const handleLogout = () => {
    logout()
    navigate('/login')
  }

  return (
    <div className="layout">
      <Navbar username={username} onLogout={handleLogout} />
      <main className="main-content">
        <div className="content-wrapper">
          <Outlet />
        </div>
      </main>
    </div>
  )
}
