import {
  blobToBase64,
  compartilharReciboPdf,
  gerarReciboPdfBlob,
  imprimirReciboPdf,
  nomeArquivoRecibo,
  validarReciboParaExportacao,
} from './reciboPdf'
import { contribuicaoService, contribuinteService } from '../services/api'
import { formatTelefoneInput, normalizarTelefoneWhatsApp } from './masks'
import { obterTextoCorpoRecibo } from './reciboTexto'

export function formatValorRecibo(valor) {
  return `R$ ${Number(valor).toFixed(2).replace('.', ',')}`
}

export function montarAssuntoEmailRecibo(recibo) {
  return `Recibo de Contribuição APPF nº ${recibo.numero}`
}

export function montarCorpoEmailRecibo(recibo, contribuinte, configAppf = null) {
  const nome = contribuinte?.nome_completo || 'Contribuinte'
  const instituicao =
    configAppf?.razao_social || recibo.razao_social || 'Associação de Pais e Professores e Funcionários'
  const valor = formatValorRecibo(recibo.valor)

  return `Prezado(a) ${nome},

Encaminhamos o recibo de contribuição voluntária nº ${recibo.numero}, no valor de ${valor}, emitido pela ${instituicao}.

O documento em PDF está anexo a esta mensagem para seus registros.

Atenciosamente,
${instituicao}`
}

export function montarTextoRecibo(recibo, contribuinte) {
  const linhas = [`Recibo APPF nº ${recibo.numero}`, '', obterTextoCorpoRecibo(recibo, contribuinte)]
  if (recibo.forma_pagamento) {
    linhas.push(`Forma de pagamento: ${recibo.forma_pagamento}`)
  }
  if (recibo.descricao) {
    linhas.push(`Descrição: ${recibo.descricao}`)
  }
  if (recibo.cancelado) {
    linhas.push(`Status: CANCELADO — ${recibo.motivo_cancelamento || ''}`)
  }
  return linhas.join('\n')
}

export function imprimirRecibo(recibo, contribuinte, configAppf = null, opcoes = {}) {
  return imprimirReciboPdf(recibo, contribuinte, configAppf, opcoes)
}

export async function prepararEnvioReciboWhatsApp(recibo, contribuinte, configAppf = null) {
  validarReciboParaExportacao(recibo)

  let contrib = contribuinte
  if (contribuinte?.id && !contribuinte.telefone) {
    try {
      const { data } = await contribuinteService.obter(contribuinte.id)
      contrib = { ...contribuinte, ...data }
    } catch {
      /* mantém contribuinte parcial */
    }
  }

  const telefoneRaw = (contrib?.telefone || '').trim()
  const texto = montarTextoRecibo(recibo, contrib)
  return {
    telefone: telefoneRaw ? formatTelefoneInput(telefoneRaw) : '',
    mensagem: `${texto}\n\nSegue o PDF do recibo.`,
    nome_anexo: nomeArquivoRecibo(recibo),
  }
}

export function montarUrlWhatsApp(telefone, mensagem) {
  const numero = normalizarTelefoneWhatsApp(telefone)
  const texto = encodeURIComponent(mensagem.trim())
  if (numero) {
    return `https://wa.me/${numero}?text=${texto}`
  }
  return `https://wa.me/?text=${texto}`
}

export async function enviarReciboWhatsAppComPdf(recibo, contribuinte, configAppf, form) {
  validarReciboParaExportacao(recibo)

  const telefone = form.telefone?.trim()
  if (!telefone) {
    throw new Error('Informe o telefone do destinatário.')
  }

  const numero = normalizarTelefoneWhatsApp(telefone)
  if (numero.length < 12) {
    throw new Error('Telefone inválido. Informe DDD e número com 10 ou 11 dígitos.')
  }

  const mensagem = form.mensagem.trim()
  const resultado = await compartilharReciboPdf(recibo, contribuinte, configAppf, mensagem)

  if (resultado.modo === 'share') {
    return { mensagem: 'Recibo compartilhado com o PDF.', modo: 'share' }
  }
  if (resultado.modo === 'cancelado') {
    return { modo: 'cancelado' }
  }

  const msg = `${mensagem}\n\nO PDF do recibo foi baixado. Anexe o arquivo ao enviar pelo WhatsApp.`
  window.open(montarUrlWhatsApp(telefone, msg), '_blank', 'noopener,noreferrer')

  return {
    mensagem: 'WhatsApp aberto com telefone e mensagem. Anexe o PDF baixado na conversa.',
    modo: 'download',
  }
}

export async function enviarReciboEmailApi(recibo, payload) {
  validarReciboParaExportacao(recibo)
  const { data } = await contribuicaoService.enviarReciboEmail(recibo.id, payload)
  return data
}

export async function prepararEnvioReciboEmail(recibo, contribuinte, configAppf = null) {
  validarReciboParaExportacao(recibo)

  let contrib = contribuinte
  if (contribuinte?.id && !contribuinte.email) {
    try {
      const { data } = await contribuinteService.obter(contribuinte.id)
      contrib = { ...contribuinte, ...data }
    } catch {
      /* mantém contribuinte parcial */
    }
  }

  return {
    destinatario_email: (contrib?.email || '').trim(),
    assunto: montarAssuntoEmailRecibo(recibo),
    corpo_texto: montarCorpoEmailRecibo(recibo, contrib, configAppf),
    nome_anexo: nomeArquivoRecibo(recibo),
  }
}

export async function enviarReciboEmailComPdf(recibo, contribuinte, configAppf, form, opcoes = {}) {
  validarReciboParaExportacao(recibo)
  const blob = await gerarReciboPdfBlob(recibo, contribuinte, configAppf, opcoes)
  const pdf_base64 = await blobToBase64(blob)

  return enviarReciboEmailApi(recibo, {
    destinatario_email: form.destinatario_email.trim(),
    assunto: form.assunto.trim(),
    corpo_texto: form.corpo_texto.trim(),
    pdf_base64,
    nome_anexo: form.nome_anexo || nomeArquivoRecibo(recibo),
  })
}
