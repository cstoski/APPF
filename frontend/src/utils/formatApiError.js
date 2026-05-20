export function formatApiError(err, fallback = 'Erro na requisição.') {
  const detail = err?.response?.data?.detail
  if (!detail) {
    return err?.message || fallback
  }
  if (typeof detail === 'string') {
    return detail
  }
  if (Array.isArray(detail)) {
    return detail.map((item) => item.msg || item.message || JSON.stringify(item)).join(' ')
  }
  return fallback
}
