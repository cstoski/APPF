import { contribuinteService } from '../services/api'
import { formatCpfDisplay } from './masks'
import { formatValorRecibo } from './reciboShare'

const MESES_PT = [
  'janeiro',
  'fevereiro',
  'março',
  'abril',
  'maio',
  'junho',
  'julho',
  'agosto',
  'setembro',
  'outubro',
  'novembro',
  'dezembro',
]

export function formatarDataRecibo(iso) {
  if (!iso) return '—'
  const d = new Date(iso)
  if (Number.isNaN(d.getTime())) return '—'
  return `${d.getDate()} de ${MESES_PT[d.getMonth()]} de ${d.getFullYear()}`
}

const UNIDADES = ['', 'um', 'dois', 'três', 'quatro', 'cinco', 'seis', 'sete', 'oito', 'nove']
const DEZ_A_DEZENOVE = [
  'dez',
  'onze',
  'doze',
  'treze',
  'quatorze',
  'quinze',
  'dezesseis',
  'dezessete',
  'dezoito',
  'dezenove',
]
const DEZENAS = [
  '',
  '',
  'vinte',
  'trinta',
  'quarenta',
  'cinquenta',
  'sessenta',
  'setenta',
  'oitenta',
  'noventa',
]
const CENTENAS = [
  '',
  'cento',
  'duzentos',
  'trezentos',
  'quatrocentos',
  'quinhentos',
  'seiscentos',
  'setecentos',
  'oitocentos',
  'novecentos',
]

function centenasPorExtenso(n) {
  if (n === 0) return ''
  if (n === 100) return 'cem'
  if (n < 10) return UNIDADES[n]
  if (n < 20) return DEZ_A_DEZENOVE[n - 10]
  if (n < 100) {
    const d = Math.floor(n / 10)
    const u = n % 10
    if (!u) return DEZENAS[d]
    return DEZENAS[d] ? `${DEZENAS[d]} e ${UNIDADES[u]}` : UNIDADES[u]
  }
  const c = Math.floor(n / 100)
  const resto = n % 100
  const prefixo = CENTENAS[c]
  const sufixo = centenasPorExtenso(resto)
  if (!sufixo) return prefixo
  if (resto < 100 || resto % 10 === 0) return `${prefixo} e ${sufixo}`
  return `${prefixo} e ${sufixo}`
}

function blocoPorExtenso(n, singular, plural) {
  if (n === 0) return ''
  return `${centenasPorExtenso(n)} ${n === 1 ? singular : plural}`.trim()
}

export function valorPorExtenso(valor) {
  const q = Math.round(Number(valor) * 100) / 100
  if (Number.isNaN(q) || q < 0) return 'zero real'

  const reais = Math.floor(q)
  const centavos = Math.round((q - reais) * 100)

  if (reais === 0 && centavos === 0) return 'zero real'

  const partes = []

  if (reais > 0) {
    const milhoes = Math.floor(reais / 1_000_000)
    const restoMilhoes = reais % 1_000_000
    const milhares = Math.floor(restoMilhoes / 1_000)
    const resto = restoMilhoes % 1_000

    const blocos = []
    if (milhoes) blocos.push(blocoPorExtenso(milhoes, 'milhão', 'milhões'))
    if (milhares) {
      const t = centenasPorExtenso(milhares)
      if (t) blocos.push(`${t} mil`)
    }
    if (resto) blocos.push(centenasPorExtenso(resto))

    const textoReais = blocos.filter(Boolean).join(' e ')
    partes.push(`${textoReais} ${reais === 1 ? 'real' : 'reais'}`.trim())
  }

  if (centavos > 0) {
    const textoCent = centenasPorExtenso(centavos)
    const sufixoCent = centavos === 1 ? 'centavo' : 'centavos'
    partes.push(`${textoCent} ${sufixoCent}`)
  }

  return partes.join(' e ')
}

export function formatarCpfRecibo(cpf) {
  const digits = String(cpf || '').replace(/\D/g, '')
  if (digits.length !== 11) return 'não informado'
  return formatCpfDisplay(digits)
}

function cpfEstaCompleto(cpf) {
  const digits = String(cpf || '').replace(/\D/g, '')
  return digits.length === 11 && !String(cpf).includes('*')
}

export function removerValorExtensoDoTexto(texto) {
  return String(texto).replace(
    /(a importância de R\$ [\d.,]+)\s*\([^)]+\)(\s+em\s+)/i,
    '$1$2',
  )
}

/** Texto principal do recibo (mesmo formato do backend). */
export function montarTextoCorpoRecibo(nome, cpf, valor, dataIso, incluirExtenso = true) {
  const nomeFmt = String(nome || '—').trim().replace(/\s+/g, ' ')
  const cpfFmt = formatarCpfRecibo(cpf)
  const valorNum = formatValorRecibo(valor)
  const dataFmt = formatarDataRecibo(dataIso || new Date().toISOString())
  const valorParte = incluirExtenso
    ? `${valorNum} (${valorPorExtenso(valor)})`
    : valorNum
  return (
    `Recebemos de ${nomeFmt}, inscrito(a) no CPF sob o nº ${cpfFmt}, ` +
    `a importância de ${valorParte} em ${dataFmt}, ` +
    `a título de contribuição social voluntária destinada à Associação de Pais, ` +
    `Professores e Funcionários (APPF) deste estabelecimento de ensino.`
  )
}

export function obterTextoCorpoRecibo(recibo, contribuinte, incluirExtenso = true) {
  if (recibo?.texto_legal_recibo?.startsWith('Recebemos')) {
    const t = recibo.texto_legal_recibo
    return incluirExtenso ? t : removerValorExtensoDoTexto(t)
  }
  return montarTextoCorpoRecibo(
    contribuinte?.nome_completo,
    contribuinte?.cpf,
    recibo?.valor,
    recibo?.data_contribuicao,
    incluirExtenso,
  )
}

/** Garante CPF completo no texto (usa texto salvo no recibo ou busca no cadastro). */
export async function resolverTextoCorpoRecibo(recibo, contribuinte) {
  const textoSalvo = recibo?.texto_legal_recibo
  const cpfAusenteNoTexto =
    textoSalvo?.startsWith('Recebemos') && /CPF sob o nº não informado/i.test(textoSalvo)

  if (textoSalvo?.startsWith('Recebemos') && !cpfAusenteNoTexto) {
    return textoSalvo
  }

  let cpf = contribuinte?.cpf
  if (contribuinte?.id && !cpfEstaCompleto(cpf)) {
    try {
      const { data } = await contribuinteService.obter(contribuinte.id)
      cpf = data.cpf || cpf
    } catch {
      /* mantém cpf disponível */
    }
  }

  return montarTextoCorpoRecibo(
    contribuinte?.nome_completo,
    cpf,
    recibo?.valor,
    recibo?.data_contribuicao,
    true,
  )
}
