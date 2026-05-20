export function onlyDigits(value) {
  return String(value ?? '').replace(/\D/g, '')
}

/** Máscara de entrada: 000.000.000-00 */
export function formatCpfInput(value) {
  const d = onlyDigits(value).slice(0, 11)
  if (d.length <= 3) return d
  if (d.length <= 6) return `${d.slice(0, 3)}.${d.slice(3)}`
  if (d.length <= 9) return `${d.slice(0, 3)}.${d.slice(3, 6)}.${d.slice(6)}`
  return `${d.slice(0, 3)}.${d.slice(3, 6)}.${d.slice(6, 9)}-${d.slice(9)}`
}

/** Exibe CPF mascarado da API ou formata dígitos completos. */
export function formatCpfDisplay(value) {
  if (!value || !String(value).trim()) return '—'
  if (String(value).includes('*')) return value
  const d = onlyDigits(value)
  if (d.length !== 11) return value
  return formatCpfInput(d)
}

/** Máscara de entrada para telefone BR. */
export function formatTelefoneInput(value) {
  const d = onlyDigits(value).slice(0, 11)
  if (d.length === 0) return ''
  if (d.length <= 2) return `(${d}`
  if (d.length <= 6) return `(${d.slice(0, 2)}) ${d.slice(2)}`
  if (d.length <= 10) return `(${d.slice(0, 2)}) ${d.slice(2, 6)}-${d.slice(6)}`
  return `(${d.slice(0, 2)}) ${d.slice(2, 7)}-${d.slice(7)}`
}

/** Preenche nome ou CPF a partir do termo de busca. */
export function inferirCadastroDoTermo(termo) {
  const t = String(termo ?? '').trim()
  if (!t) {
    return { nome_completo: '', cpf: '', email: '', telefone: '', observacoes: '' }
  }
  const digits = onlyDigits(t)
  const pareceCpf = digits.length >= 3 && digits.length >= t.replace(/\s/g, '').length * 0.6
  if (pareceCpf) {
    return {
      nome_completo: '',
      cpf: formatCpfInput(digits),
      email: '',
      telefone: '',
      observacoes: '',
    }
  }
  return {
    nome_completo: t,
    cpf: '',
    email: '',
    telefone: '',
    observacoes: '',
  }
}

export function formatTelefoneDisplay(value) {
  if (!value) return '—'
  const d = onlyDigits(value)
  if (d.length < 10) return value
  return formatTelefoneInput(d)
}

/** Dígitos internacionais para links wa.me (Brasil: +55). */
export function normalizarTelefoneWhatsApp(telefone) {
  let d = onlyDigits(telefone)
  if (!d) return ''
  if (d.startsWith('0')) d = d.slice(1)
  if (d.length === 10 || d.length === 11) {
    d = `55${d}`
  }
  return d
}
