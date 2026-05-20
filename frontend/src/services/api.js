import axios from 'axios'

const API_BASE_URL = import.meta.env.VITE_API_URL ?? ''

const api = axios.create({
  baseURL: API_BASE_URL,
  headers: {
    'Content-Type': 'application/json',
  },
})

api.interceptors.request.use((config) => {
  const token = sessionStorage.getItem('appf_token')
  if (token) {
    config.headers.Authorization = `Bearer ${token}`
  }
  return config
})

api.interceptors.response.use(
  (response) => response,
  (error) => {
    const isLoginRequest = String(error.config?.url || '').includes('/auth/login')
    if (error.response?.status === 401 && !isLoginRequest) {
      sessionStorage.removeItem('appf_token')
      sessionStorage.removeItem('appf_username')
      if (!window.location.pathname.startsWith('/login')) {
        window.location.href = '/login'
      }
    }
    return Promise.reject(error)
  }
)

export function staticAssetUrl(path) {
  if (!path) return ''
  if (path.startsWith('http')) return path
  const origin = API_BASE_URL || window.location.origin
  return `${origin}${path}`
}

export function downloadBlobResponse(response, filename) {
  const url = window.URL.createObjectURL(new Blob([response.data]))
  const link = document.createElement('a')
  link.href = url
  link.setAttribute('download', filename)
  document.body.appendChild(link)
  link.click()
  link.remove()
  window.URL.revokeObjectURL(url)
}

export const authService = {
  login: (username, password) => api.post('/api/v1/auth/login', { username, password }),
  logout: () => api.post('/api/v1/auth/logout'),
  trocarSenha: (senha_atual, nova_senha) =>
    api.post('/api/v1/auth/trocar-senha', { senha_atual, nova_senha }),
  ping: () => api.get('/ping'),
}

export const sistemaService = {
  info: () => api.get('/api/v1/sistema/info'),
  licencaStatus: () => api.get('/api/v1/licenca'),
  ativarLicenca: (serial) => api.post('/api/v1/licenca/ativar', { serial }),
}

export const appfService = {
  obterConfig: () => api.get('/api/v1/appf'),
  salvarConfig: (formData) =>
    api.post('/api/v1/appf', formData, {
      headers: { 'Content-Type': 'multipart/form-data' },
    }),
  validarConfig: (escopo = 'tudo') =>
    api.post('/api/v1/appf/validar', null, { params: { escopo } }),
}

export const usuariosService = {
  listar: () => api.get('/api/v1/usuarios'),
  criar: (data) => api.post('/api/v1/usuarios', data),
  atualizar: (id, data) => api.put(`/api/v1/usuarios/${id}`, data),
  desativar: (id) => api.post(`/api/v1/usuarios/${id}/desativar`),
}

export const contribuinteService = {
  listar: (excluidos = false) =>
    api.get('/api/v1/contribuintes', { params: { excluidos } }),
  buscar: (termo) => api.get('/api/v1/contribuintes/buscar', { params: { termo } }),
  obter: (id) => api.get(`/api/v1/contribuintes/${id}`),
  criar: (data) => api.post('/api/v1/contribuintes', data),
  atualizar: (id, data) => api.put(`/api/v1/contribuintes/${id}`, data),
  excluir: (id) => api.delete(`/api/v1/contribuintes/${id}`),
  reativar: (id) => api.post(`/api/v1/contribuintes/${id}/reativar`),
}

export const contribuicaoService = {
  listar: (contribuinteId) =>
    api.get('/api/v1/contribricoes', { params: { contribuinte_id: contribuinteId } }),
  obter: (reciboId) => api.get(`/api/v1/contribricoes/${reciboId}`),
  emitir: (data) => api.post('/api/v1/contribricoes', data),
  cancelar: (reciboId, motivo) =>
    api.post(`/api/v1/contribricoes/${reciboId}/cancelar`, { motivo }),
  enviarEmail: (payload) => api.post('/api/v1/relatorios/contribuinte/enviar-email', payload),
  enviarReciboEmail: (reciboId, payload) =>
    api.post(`/api/v1/contribricoes/${reciboId}/enviar-email`, payload),
  registrarAcao: (reciboId, payload) =>
    api.post(`/api/v1/contribricoes/${reciboId}/registrar-acao`, payload),
}

export const dashboardService = {
  resumo: (params) => api.get('/api/v1/dashboard/resumo', { params }),
}

export const relatorioService = {
  contribuinte: (params) => api.get('/api/v1/relatorios/contribuinte', { params }),
  financeiro: (params) => api.get('/api/v1/relatorios/financeiro', { params }),
}

export const importService = {
  getPreview: (file) => {
    const formData = new FormData()
    formData.append('arquivo', file)
    return api.post('/api/v1/dados/importar/preview-detalhado', formData, {
      headers: { 'Content-Type': 'multipart/form-data' },
    })
  },
  aplicarDecisoes: (file, decisoes, modo_duplicados = 'PULAR') => {
    const formData = new FormData()
    formData.append('arquivo', file)
    formData.append('modo_duplicados', modo_duplicados)
    formData.append('decisoes_json', JSON.stringify(decisoes))
    return api.post('/api/v1/dados/importar/aplicar', formData, {
      headers: { 'Content-Type': 'multipart/form-data' },
    })
  },
}

export const exportService = {
  exportarContribuintes: () =>
    api.get('/api/v1/dados/exportar/contribuintes', { responseType: 'blob' }),
}

export default api
