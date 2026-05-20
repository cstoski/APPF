import pdfMake from 'pdfmake/build/pdfmake'
import pdfFonts from 'pdfmake/build/vfs_fonts'
import { blocoAssinaturas, carregarImagemPdf } from './pdfAssinaturas'
import { resolverTextoCorpoRecibo, formatarDataRecibo } from './reciboTexto'

const vfs = pdfFonts.pdfMake?.vfs ?? pdfFonts.default?.pdfMake?.vfs
if (vfs) {
  pdfMake.vfs = vfs
}

export function formatDataEmissao(iso) {
  if (!iso) return '—'
  const d = new Date(iso)
  if (Number.isNaN(d.getTime())) return '—'
  return d.toLocaleString('pt-BR', {
    day: '2-digit',
    month: '2-digit',
    year: 'numeric',
    hour: '2-digit',
    minute: '2-digit',
  })
}

const TEXTO_AVISO_LEGAL_PDF =
  'Em conformidade com o Artigo 206, IV da Constituição Federal, que garante a gratuidade do ensino público, ' +
  'e atendendo às diretrizes do Estatuto Padrão da APPF, informamos que a contribuição financeira solicitada ' +
  'possui caráter estritamente voluntário, não guardando qualquer vínculo ou obrigatoriedade com o ato de matrícula, ' +
  'rematrícula ou permanência do estudante na instituição de ensino.'

export function validarReciboParaExportacao(recibo) {
  if (recibo?.cancelado) {
    throw new Error('Recibos cancelados não podem ser impressos, exportados em PDF nem enviados.')
  }
}

function dadosInstituicao(recibo, configAppf) {
  return {
    razao_social: recibo.razao_social || configAppf?.razao_social || 'APPF',
    cnpj: recibo.cnpj || configAppf?.cnpj || '',
    endereco: recibo.endereco || configAppf?.endereco || '',
    nome_presidente: recibo.nome_presidente || configAppf?.nome_presidente || '',
    nome_tesoureiro: recibo.nome_tesoureiro || configAppf?.nome_tesoureiro || '',
    caminho_assinatura_presidente:
      recibo.caminho_assinatura_presidente || configAppf?.caminho_assinatura_presidente || '',
    caminho_assinatura_tesoureiro:
      recibo.caminho_assinatura_tesoureiro || configAppf?.caminho_assinatura_tesoureiro || '',
  }
}

/** @typedef {{ duplicarNaFolha?: boolean }} OpcoesPdfRecibo */

const LAYOUT_TABELA_DUPLICADA = {
  hLineWidth: (i) => (i === 1 ? 0.5 : 0),
  hLineColor: () => '#94a3b8',
  hLineStyle: (i) => (i === 1 ? { dash: { length: 5, space: 4 } } : null),
  vLineWidth: () => 0,
  paddingLeft: () => 0,
  paddingRight: () => 0,
  paddingTop: (i) => (i === 0 ? 4 : 10),
  paddingBottom: (i, node) => (i === node.table.body.length - 1 ? 4 : 10),
}

async function montarConteudoRecibo(recibo, contribuinte, configAppf, textoCorpo, duplicarNaFolha = false) {
  const inst = dadosInstituicao(recibo, configAppf)
  const [imgPresidente, imgTesoureiro] = await Promise.all([
    carregarImagemPdf(inst.caminho_assinatura_presidente),
    carregarImagemPdf(inst.caminho_assinatura_tesoureiro),
  ])
  const opcoesAssinatura = duplicarNaFolha
    ? { larguraImagem: 88, espacoSemImagem: 20 }
    : {}
  const assinaturas = blocoAssinaturas(inst, imgPresidente, imgTesoureiro, opcoesAssinatura)
  const margemAssinaturas = duplicarNaFolha ? [0, 10, 0, 2] : [0, 24, 0, 6]
  const gap = duplicarNaFolha ? 10 : 16
  const gapPequeno = duplicarNaFolha ? 8 : 12

  return [
    { text: inst.razao_social, style: 'tituloInstituicao', alignment: 'center' },
    { text: `CNPJ: ${inst.cnpj || '—'}`, alignment: 'center', margin: [0, 2, 0, 0] },
    { text: inst.endereco || '—', alignment: 'center', margin: [0, 2, 0, gapPequeno] },
    { text: `RECIBO Nº ${recibo.numero}`, style: 'tituloRecibo', alignment: 'center', margin: [0, 0, 0, 6] },
    {
      text: [
        { text: `Contribuição: ${formatarDataRecibo(recibo.data_contribuicao)}` },
        { text: '  |  ', color: '#999' },
        { text: `Registro: ${formatDataEmissao(recibo.data_criacao)}` },
        { text: '  |  ', color: '#999' },
        { text: `Por: ${recibo.usuario_emissor || '—'}` },
      ],
      alignment: 'center',
      fontSize: duplicarNaFolha ? 8 : 9,
      color: '#444',
      margin: [0, 0, 0, gap],
    },
    {
      text: textoCorpo,
      style: 'corpoRecibo',
      alignment: 'justify',
      margin: [0, 0, 0, gap],
    },
    ...(recibo.descricao
      ? [
          {
            text: `Descrição: ${recibo.descricao}`,
            fontSize: duplicarNaFolha ? 9.5 : 11,
            margin: [0, 0, 0, gap],
          },
        ]
      : []),
    { ...assinaturas, margin: margemAssinaturas },
    {
      text: TEXTO_AVISO_LEGAL_PDF,
      style: 'avisoLegal',
      alignment: 'justify',
      margin: [0, 4, 0, 0],
    },
  ]
}

async function montarDocDefinition(recibo, contribuinte, configAppf, textoCorpo, opcoes = {}) {
  const duplicarNaFolha = Boolean(opcoes.duplicarNaFolha)

  const styles = {
    tituloInstituicao: { fontSize: duplicarNaFolha ? 12 : 14, bold: true },
    tituloRecibo: { fontSize: duplicarNaFolha ? 11 : 13, bold: true },
    corpoRecibo: { fontSize: duplicarNaFolha ? 9.5 : 11, lineHeight: duplicarNaFolha ? 1.28 : 1.35 },
    avisoLegal: { fontSize: duplicarNaFolha ? 7 : 8, lineHeight: 1.25, color: '#444' },
    cargoAssinatura: { fontSize: duplicarNaFolha ? 8 : 9, color: '#555' },
  }

  const margens = duplicarNaFolha ? [40, 36, 40, 36] : [48, 48, 48, 48]

  if (!duplicarNaFolha) {
    const conteudo = await montarConteudoRecibo(recibo, contribuinte, configAppf, textoCorpo, false)
    return {
      pageSize: 'A4',
      pageMargins: margens,
      defaultStyle: { font: 'Roboto', fontSize: 11 },
      content: conteudo,
      styles,
    }
  }

  const [viaSuperior, viaInferior] = await Promise.all([
    montarConteudoRecibo(recibo, contribuinte, configAppf, textoCorpo, true),
    montarConteudoRecibo(recibo, contribuinte, configAppf, textoCorpo, true),
  ])

  return {
    pageSize: 'A4',
    pageMargins: margens,
    defaultStyle: { font: 'Roboto', fontSize: 11 },
    content: [
      {
        table: {
          widths: ['*'],
          dontBreakRows: true,
          body: [[{ stack: viaSuperior }], [{ stack: viaInferior }]],
        },
        layout: LAYOUT_TABELA_DUPLICADA,
      },
    ],
    styles,
  }
}

export function blobToBase64(blob) {
  return new Promise((resolve, reject) => {
    const reader = new FileReader()
    reader.onload = () => {
      const dataUrl = reader.result
      if (typeof dataUrl !== 'string') {
        reject(new Error('Não foi possível converter o PDF.'))
        return
      }
      const base64 = dataUrl.split(',')[1]
      resolve(base64 || '')
    }
    reader.onerror = () => reject(new Error('Não foi possível ler o PDF.'))
    reader.readAsDataURL(blob)
  })
}

export function nomeArquivoRecibo(recibo) {
  return `Recibo Contribuição APPF ${recibo.numero}.pdf`
}

export async function gerarReciboPdfBlob(recibo, contribuinte, configAppf = null, opcoes = {}) {
  validarReciboParaExportacao(recibo)
  const textoCorpo = await resolverTextoCorpoRecibo(recibo, contribuinte)
  const docDefinition = await montarDocDefinition(recibo, contribuinte, configAppf, textoCorpo, opcoes)
  return new Promise((resolve, reject) => {
    try {
      pdfMake.createPdf(docDefinition).getBlob((blob) => resolve(blob))
    } catch (err) {
      reject(err)
    }
  })
}

export function baixarBlob(blob, filename) {
  const url = URL.createObjectURL(blob)
  const link = document.createElement('a')
  link.href = url
  link.download = filename
  document.body.appendChild(link)
  link.click()
  link.remove()
  URL.revokeObjectURL(url)
}

export async function baixarReciboPdf(recibo, contribuinte, configAppf = null, opcoes = {}) {
  const blob = await gerarReciboPdfBlob(recibo, contribuinte, configAppf, opcoes)
  baixarBlob(blob, nomeArquivoRecibo(recibo))
  return blob
}

/** Imprime o mesmo PDF usado em download, e-mail e WhatsApp. */
export async function imprimirReciboPdf(recibo, contribuinte, configAppf = null, opcoes = {}) {
  const blob = await gerarReciboPdfBlob(recibo, contribuinte, configAppf, opcoes)
  const url = URL.createObjectURL(blob)

  return new Promise((resolve, reject) => {
    const iframe = document.createElement('iframe')
    iframe.style.cssText = 'position:fixed;right:0;bottom:0;width:0;height:0;border:none'
    iframe.title = `Impressão recibo ${recibo.numero}`

    const limpar = () => {
      iframe.remove()
      URL.revokeObjectURL(url)
    }

    iframe.onload = () => {
      try {
        iframe.contentWindow?.focus()
        iframe.contentWindow?.print()
        setTimeout(limpar, 1500)
        resolve()
      } catch (err) {
        limpar()
        reject(err)
      }
    }

    iframe.onerror = () => {
      limpar()
      reject(new Error('Não foi possível carregar o PDF para impressão.'))
    }

    iframe.src = url
    document.body.appendChild(iframe)
  })
}

export async function compartilharReciboPdf(
  recibo,
  contribuinte,
  configAppf = null,
  textoExtra = '',
  opcoes = {},
) {
  const blob = await gerarReciboPdfBlob(recibo, contribuinte, configAppf, opcoes)
  const filename = nomeArquivoRecibo(recibo)
  const file = new File([blob], filename, { type: 'application/pdf' })
  const texto = textoExtra || `Recibo APPF nº ${recibo.numero}`

  if (navigator.share && navigator.canShare?.({ files: [file] })) {
    try {
      await navigator.share({ files: [file], title: `Recibo ${recibo.numero}`, text: texto })
      return { modo: 'share' }
    } catch (err) {
      if (err?.name === 'AbortError') {
        return { modo: 'cancelado' }
      }
    }
  }

  baixarBlob(blob, filename)
  return { modo: 'download' }
}
