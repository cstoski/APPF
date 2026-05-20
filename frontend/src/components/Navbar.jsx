import { NavLink } from 'react-router-dom'
import '../styles/navbar.css'

export default function Navbar({ username, onLogout }) {
  return (
    <nav className="navbar">
      <div className="navbar-brand">
        <div className="brand-icon">APPF</div>
        <div>
          <h1>Importação com Aprovação</h1>
          <p>LGPD + Licença + JWT</p>
        </div>
      </div>

      <div className="navbar-links">
        <NavLink to="/dashboard" className={({ isActive }) => isActive ? 'active' : ''}>
          Dashboard
        </NavLink>
        <NavLink to="/importacao" className={({ isActive }) => isActive ? 'active' : ''}>
          Importação
        </NavLink>
      </div>

      <div className="navbar-user">
        <div className="username">Olá, {username}</div>
        <button className="btn btn-logout" onClick={onLogout}>
          Sair
        </button>
      </div>
    </nav>
  )
}
