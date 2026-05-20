import { useState, useEffect } from 'react'

export function useAuth() {
  const [token, setToken] = useState(null)
  const [username, setUsername] = useState(null)
  const [loading, setLoading] = useState(true)

  useEffect(() => {
    const savedToken = sessionStorage.getItem('appf_token')
    const savedUsername = sessionStorage.getItem('appf_username')
    if (savedToken) {
      setToken(savedToken)
      setUsername(savedUsername)
    }
    setLoading(false)
  }, [])

  const login = (newToken, newUsername) => {
    setToken(newToken)
    setUsername(newUsername)
    sessionStorage.setItem('appf_token', newToken)
    sessionStorage.setItem('appf_username', newUsername)
  }

  const logout = () => {
    setToken(null)
    setUsername(null)
    sessionStorage.removeItem('appf_token')
    sessionStorage.removeItem('appf_username')
  }

  return { token, username, loading, login, logout }
}
