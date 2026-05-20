import { Link } from 'react-router-dom'
import '../styles/navbar.css'

export default function Navbar({ username, onLogout }) {
  return (
    <nav className="navbar">
      <div className="navbar-brand">
        <h1>📋 APPF</h1>
        <p>Importação com Aprovação</p>
      </div>
      
      <div className="navbar-links">
        <Link to="/dashboard">Dashboard</Link>
        <Link to="/importacao">Importação</Link>
      </div>

      <div className="navbar-user">
        <span className="username">Olá, {username}</span>
        <button className="btn btn-logout" onClick={onLogout}>
          Sair
        </button>
      </div>
    </nav>
  )
}
