import axios from 'axios'

const API_BASE_URL = import.meta.env.VITE_API_URL || 'http://127.0.0.1:8000'

const api = axios.create({
  baseURL: API_BASE_URL,
  headers: {
    'Content-Type': 'application/json'
  }
})

// Interceptor para adicionar token
api.interceptors.request.use((config) => {
  const token = sessionStorage.getItem('appf_token')
  if (token) {
    config.headers.Authorization = `Bearer ${token}`
  }
  return config
})

// Interceptor para erro de autenticação
api.interceptors.response.use(
  (response) => response,
  (error) => {
    if (error.response?.status === 401) {
      sessionStorage.removeItem('appf_token')
      window.location.href = '/login'
    }
    return Promise.reject(error)
  }
)

export const authService = {
  login: (username, password) => api.post('/api/v1/auth/login', { username, password }),
  ping: () => api.get('/ping'),
}

export const importService = {
  uploadFile: (file, modo_duplicados = 'ATUALIZAR') => {
    const formData = new FormData()
    formData.append('arquivo', file)
    formData.append('modo_duplicados', modo_duplicados)
    return api.post('/api/v1/dados/importar', formData, {
      headers: { 'Content-Type': 'multipart/form-data' }
    })
  },
  getPreview: (file) => {
    const formData = new FormData()
    formData.append('arquivo', file)
    return api.post('/api/v1/dados/importar/preview-detalhado', formData, {
      headers: { 'Content-Type': 'multipart/form-data' }
    })
  },
  aplicarDecisoes: (file, decisoes, modo_duplicados = 'ATUALIZAR') => {
    const formData = new FormData()
    formData.append('arquivo', file)
    formData.append('modo_duplicados', modo_duplicados)
    formData.append('decisoes_json', JSON.stringify(decisoes))
    return api.post('/api/v1/dados/importar/aplicar', formData, {
      headers: { 'Content-Type': 'multipart/form-data' }
    })
  },
}

export const exportService = {
  exportarContribuintes: () => api.get('/api/v1/dados/exportar/contribuintes'),
}

export default api
