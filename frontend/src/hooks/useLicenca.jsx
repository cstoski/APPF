import { createContext, useCallback, useContext, useEffect, useState } from 'react'
import { sistemaService } from '../services/api'
import { useAuth } from './useAuth.jsx'

const LicencaContext = createContext(null)

export function LicencaProvider({ children }) {
  const { token } = useAuth()
  const [licenca, setLicenca] = useState(null)
  const [loading, setLoading] = useState(true)

  const refreshLicenca = useCallback(async () => {
    if (!token) {
      setLicenca(null)
      setLoading(false)
      return
    }
    setLoading(true)
    try {
      const { data } = await sistemaService.licencaStatus()
      setLicenca(data)
    } catch {
      setLicenca(null)
    } finally {
      setLoading(false)
    }
  }, [token])

  useEffect(() => {
    refreshLicenca()
  }, [refreshLicenca])

  return (
    <LicencaContext.Provider value={{ licenca, loading, refreshLicenca }}>
      {children}
    </LicencaContext.Provider>
  )
}

export function useLicenca() {
  const ctx = useContext(LicencaContext)
  if (!ctx) {
    throw new Error('useLicenca deve ser usado dentro de LicencaProvider')
  }
  return ctx
}
