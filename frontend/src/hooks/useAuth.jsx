import { createContext, useContext, useState, useEffect, useMemo } from 'react'
import { authService } from '../services/api'
import { parseJwtPayload } from '../utils/jwt.js'

const AuthContext = createContext(null)

function readPerfilFromToken(token) {
  const payload = parseJwtPayload(token)
  return payload?.perfil || null
}

export function AuthProvider({ children }) {
  const [token, setToken] = useState(null)
  const [username, setUsername] = useState(null)
  const [perfil, setPerfil] = useState(null)
  const [loading, setLoading] = useState(true)

  useEffect(() => {
    const savedToken = sessionStorage.getItem('appf_token')
    const savedUsername = sessionStorage.getItem('appf_username')
    if (savedToken) {
      setToken(savedToken)
      setUsername(savedUsername)
      setPerfil(readPerfilFromToken(savedToken))
    }
    setLoading(false)
  }, [])

  const login = (newToken, newUsername) => {
    setToken(newToken)
    setUsername(newUsername)
    setPerfil(readPerfilFromToken(newToken))
    sessionStorage.setItem('appf_token', newToken)
    sessionStorage.setItem('appf_username', newUsername)
  }

  const logout = async () => {
    try {
      if (sessionStorage.getItem('appf_token')) {
        await authService.logout()
      }
    } catch {
      /* registra logout quando possível; não impede sair da sessão local */
    }
    setToken(null)
    setUsername(null)
    setPerfil(null)
    sessionStorage.removeItem('appf_token')
    sessionStorage.removeItem('appf_username')
  }

  const isAdmin = useMemo(() => perfil === 'MASTER' || perfil === 'DEV', [perfil])

  return (
    <AuthContext.Provider value={{ token, username, perfil, isAdmin, loading, login, logout }}>
      {children}
    </AuthContext.Provider>
  )
}

export function useAuth() {
  const ctx = useContext(AuthContext)
  if (!ctx) {
    throw new Error('useAuth deve ser usado dentro de AuthProvider')
  }
  return ctx
}
