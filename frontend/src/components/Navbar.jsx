import { useEffect, useState } from 'react'

import { NavLink, useLocation } from 'react-router-dom'

import { useAuth } from '../hooks/useAuth.jsx'

import ApiServerStatus from './ApiServerStatus'

import SobreMenu from './SobreMenu'

import '../styles/navbar.css'



const NAV_ITEMS = [

  { to: '/dashboard', label: 'Dashboard' },

  { to: '/contribuintes', label: 'Contribuintes' },

  { to: '/contribuicoes', label: 'Recibos' },

  { to: '/relatorios', label: 'Relatórios' },

  { to: '/configuracao', label: 'Configuração' },

  { to: '/usuarios', label: 'Usuários', adminOnly: true },

]



export default function Navbar({ username, onLogout }) {

  const { isAdmin } = useAuth()

  const location = useLocation()

  const [menuOpen, setMenuOpen] = useState(false)



  useEffect(() => {

    setMenuOpen(false)

  }, [location.pathname])



  return (

    <nav className={`navbar ${menuOpen ? 'navbar-menu-open' : ''}`}>

      <div className="navbar-bar">

        <div className="navbar-brand">

          <img src="/images/zelo-appf-navbar.png" alt="Zelo APPF" className="brand-logo-img" />

        </div>



        <div className="navbar-mobile-tools">

          <ApiServerStatus />

          <SobreMenu />

        </div>



        <button

          type="button"

          className="navbar-menu-toggle"

          onClick={() => setMenuOpen((open) => !open)}

          aria-expanded={menuOpen}

          aria-controls="navbar-panel"

          aria-label={menuOpen ? 'Fechar menu' : 'Abrir menu'}

        >

          <span className="navbar-menu-toggle-bars" aria-hidden="true" />

        </button>

      </div>



      <div id="navbar-panel" className="navbar-panel">

        <div className="navbar-links">

          {NAV_ITEMS.filter((item) => !item.adminOnly || isAdmin).map((item) => (

            <NavLink

              key={item.to}

              to={item.to}

              className={({ isActive }) => (isActive ? 'active' : '')}

              onClick={() => setMenuOpen(false)}

            >

              {item.label}

            </NavLink>

          ))}

        </div>



        <div className="navbar-user">

          <div className="navbar-user-tools">

            <ApiServerStatus />

            <SobreMenu />

          </div>

          <div className="username">Olá, {username}</div>

          <button type="button" className="btn btn-logout" onClick={onLogout}>

            Sair

          </button>

        </div>

      </div>

    </nav>

  )

}


