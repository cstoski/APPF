import pdfMake from 'pdfmake/build/pdfmake'
import pdfFonts from 'pdfmake/build/vfs_fonts'
import { formatCpfDisplay } from './masks'
import { blocoAssinaturas, carregarImagemPdf } from './pdfAssinaturas'

const vfs = pdfFonts.pdfMake?.vfs ?? pdfFonts.default?.pdfMake?.vfs
if (vfs) {
  pdfMake.vfs = vfs
}

export function formatDataRecebimento(iso) {
  if (!iso) return '—'
  const s = String(iso)
  const m = s.match(/^(\d{4})-(\d{2})-(\d{2})/)
  if (m) return `${m[3]}/${m[2]}/${m[1]}`
  const d = new Date(iso)
  if (Number.isNaN(d.getTime())) return '—'
  return d.toLocaleDateString('pt-BR', { day: '2-digit', month: '2-digit', year: 'numeric' })
}

export function formatDataGeracao() {
  return new Date().toLocaleDateString('pt-BR', {
    day: '2-digit',
    month: '2-digit',
    year: 'numeric',
  })
}

function formatValor(valor) {
  return `R$ ${Number(valor).toFixed(2).replace('.', ',')}`
}

export function ordenarLinhasRelatorio(linhas) {
  return [...(linhas || [])].sort((a, b) => {
    const da = new Date(a.data_contribuicao).getTime()
    const db = new Date(b.data_contribuicao).getTime()
    if (da !== db) return da - db
    return String(a.numero).localeCompare(String(b.numero))
  })
}

function instituicaoDe(dados) {
  if (dados.instituicao) return dados.instituicao
  return {
    razao_social: dados.razao_social || 'APPF',
    cnpj: dados.cnpj || '',
    nome_presidente: dados.nome_presidente || '',
    nome_tesoureiro: dados.nome_tesoureiro || '',
    caminho_assinatura_presidente: dados.caminho_assinatura_presidente || '',
    caminho_assinatura_tesoureiro: dados.caminho_assinatura_tesoureiro || '',
  }
}

function montarCabecalho(dados, tipo) {
  const inst = instituicaoDe(dados)
  const financeiro = tipo === 'financeiro'
  const blocos = [
    { text: dados.titulo, style: 'tituloRelatorio', alignment: 'center', margin: [0, 0, 0, 10] },
    { text: inst.razao_social, style: 'tituloInstituicao', alignment: 'center' },
    { text: `CNPJ: ${inst.cnpj || '—'}`, alignment: 'center', margin: [0, 2, 0, 8], fontSize: 10 },
  ]

  if (financeiro) {
    blocos.push({
      text: `Período: ${dados.periodo_label}`,
      alignment: 'center',
      margin: [0, 0, 0, 12],
    })
  } else {
    blocos.push(
      { text: `Contribuinte: ${dados.contribuinte_nome}`, margin: [0, 0, 0, 2] },
      ...(dados.contribuinte_cpf
        ? [{ text: `CPF: ${formatCpfDisplay(dados.contribuinte_cpf)}`, margin: [0, 0, 0, 2] }]
        : []),
      { text: `Período: ${dados.periodo_label}`, margin: [0, 0, 0, 12] },
    )
  }

  return { inst, blocos }
}

function montarRodapeConteudo(dados, username, tipo) {
  const blocos = []
  const financeiro = tipo === 'financeiro'
  const resumo = dados.resumo
  if (resumo) {
    const linhaResumo = [
      { text: 'Quantidade: ', bold: true },
      { text: String(resumo.quantidade) },
      { text: '   |   Valor total: ', bold: true },
      { text: formatValor(resumo.valor_total) },
    ]
    if (financeiro) {
      linhaResumo.push(
        { text: '   |   Valor médio: ', bold: true },
        { text: formatValor(resumo.valor_medio) },
      )
    }
    blocos.push({
      text: linhaResumo,
      margin: [0, 12, 0, 4],
      fontSize: 10,
    })
  }
  blocos.push({
    text: `Gerado em: ${formatDataGeracao()}${username ? ` — por ${username}` : ''}`,
    fontSize: 9,
    color: '#444',
    margin: [0, 0, 0, 8],
  })
  return blocos
}

function montarTabela(linhas, financeiro) {
  const ordenadas = ordenarLinhasRelatorio(linhas)
  const header = [
    { text: 'Data', style: 'tableHeader' },
    { text: 'Nº recibo', style: 'tableHeader' },
    ...(financeiro ? [{ text: 'Contribuinte', style: 'tableHeader' }] : []),
    { text: 'Valor', style: 'tableHeader' },
    { text: 'Forma', style: 'tableHeader' },
  ]

  const body = ordenadas.map((l) => {
    const row = [
      { text: formatDataRecebimento(l.data_contribuicao), style: l.cancelado ? 'linhaCancelada' : {} },
      { text: l.numero, style: l.cancelado ? 'linhaCancelada' : {} },
      ...(financeiro
        ? [{ text: l.contribuinte_nome || '—', style: l.cancelado ? 'linhaCancelada' : {} }]
        : []),
      { text: formatValor(l.valor), style: l.cancelado ? 'linhaCancelada' : {} },
      { text: l.forma_pagamento || '—', style: l.cancelado ? 'linhaCancelada' : {} },
    ]
    return row
  })

  if (!body.length) {
    body.push([
      {
        text: 'Nenhuma contribuição no período.',
        colSpan: header.length,
        alignment: 'center',
        italics: true,
        margin: [0, 8, 0, 8],
      },
      ...header.slice(1).map(() => ({})),
    ])
  }

  const widths = financeiro
    ? ['14%', '18%', '21%', '14%', '15%']
    : ['18%', '18%', '21%', '21%', '22%']

  return {
    table: {
      headerRows: 1,
      widths,
      body: [header, ...body],
    },
    layout: {
      hLineWidth: () => 0.5,
      vLineWidth: () => 0.5,
      hLineColor: () => '#ccc',
      vLineColor: () => '#ccc',
      paddingLeft: () => 6,
      paddingRight: () => 6,
      paddingTop: () => 4,
      paddingBottom: () => 4,
    },
    margin: [0, 0, 0, 4],
  }
}

const MESES_ABREV = ['Jan', 'Fev', 'Mar', 'Abr', 'Mai', 'Jun', 'Jul', 'Ago', 'Set', 'Out', 'Nov', 'Dez']

function montarSecaoAnualMensal(totaisMensais) {
  if (!totaisMensais?.length) return []

  const body = totaisMensais.map((m) => [
    { text: m.mes_label, style: 'tableHeader' },
    { text: String(m.quantidade), alignment: 'center' },
    { text: formatValor(m.valor_total), alignment: 'right' },
  ])

  const totalQtd = totaisMensais.reduce((s, m) => s + m.quantidade, 0)
  const totalVal = totaisMensais.reduce((s, m) => s + m.valor_total, 0)

  body.push([
    { text: 'Total do ano', bold: true, fillColor: '#f0f4f8' },
    { text: String(totalQtd), alignment: 'center', bold: true, fillColor: '#f0f4f8' },
    { text: formatValor(totalVal), alignment: 'right', bold: true, fillColor: '#f0f4f8' },
  ])

  const tabelaMensal = {
    table: {
      headerRows: 1,
      widths: ['*', '18%', '22%'],
      body: [
        [
          { text: 'Mês', style: 'tableHeader' },
          { text: 'Quantidade', style: 'tableHeader', alignment: 'center' },
          { text: 'Valor total', style: 'tableHeader', alignment: 'right' },
        ],
        ...body,
      ],
    },
    layout: {
      hLineWidth: () => 0.5,
      vLineWidth: () => 0.5,
      hLineColor: () => '#ccc',
      vLineColor: () => '#ccc',
      paddingLeft: () => 6,
      paddingRight: () => 6,
      paddingTop: () => 4,
      paddingBottom: () => 4,
    },
    margin: [0, 16, 0, 12],
  }

  const grafico = montarGraficoBarrasMensal(totaisMensais)

  return [
    { text: 'Resumo mensal de contribuições', style: 'tituloSecao', margin: [0, 8, 0, 6] },
    tabelaMensal,
    ...(grafico ? [grafico] : []),
  ]
}

function montarGraficoBarrasMensal(totaisMensais) {
  const chartWidth = 515
  const barAreaHeight = 85
  const maxVal = Math.max(...totaisMensais.map((m) => m.valor_total), 1)
  const colWidth = chartWidth / 12
  const barWidth = Math.min(colWidth - 6, 32)

  const canvasItems = [
    {
      type: 'line',
      x1: 0,
      y1: barAreaHeight,
      x2: chartWidth,
      y2: barAreaHeight,
      lineWidth: 0.5,
      lineColor: '#999',
    },
  ]

  totaisMensais.forEach((m, i) => {
    const h = m.valor_total > 0 ? Math.max((m.valor_total / maxVal) * barAreaHeight, 2) : 0
    const x = i * colWidth + (colWidth - barWidth) / 2
    const y = barAreaHeight - h
    if (h > 0) {
      canvasItems.push({
        type: 'rect',
        x,
        y,
        w: barWidth,
        h,
        color: '#2563eb',
      })
    }
  })

  const rotulosMeses = {
    columns: MESES_ABREV.map((abrev) => ({
      width: colWidth,
      text: abrev,
      alignment: 'center',
      fontSize: 7,
      color: '#444',
    })),
    margin: [0, 2, 0, 0],
  }

  return {
    stack: [
      { text: 'Gráfico — valor total por mês (R$)', style: 'tituloSecao', margin: [0, 4, 0, 6] },
      { canvas: canvasItems, margin: [0, 0, 0, 0] },
      rotulosMeses,
    ],
    margin: [0, 0, 0, 8],
  }
}

export async function montarDocDefinitionRelatorio(dados, tipo, username) {
  const financeiro = tipo === 'financeiro'
  const { inst, blocos } = montarCabecalho(dados, tipo)
  const rodapeConteudo = montarRodapeConteudo(dados, username, tipo)

  const [imgPresidente, imgTesoureiro] = await Promise.all([
    carregarImagemPdf(inst.caminho_assinatura_presidente),
    carregarImagemPdf(inst.caminho_assinatura_tesoureiro),
  ])

  const assinaturas = blocoAssinaturas(inst, imgPresidente, imgTesoureiro)

  const secaoAnual =
    financeiro && dados.periodo === 'anual' && dados.totais_mensais?.length
      ? montarSecaoAnualMensal(dados.totais_mensais)
      : []

  return {
    pageSize: 'A4',
    pageMargins: [40, 40, 40, 110],
    defaultStyle: { font: 'Roboto', fontSize: 10 },
    content: [
      ...blocos,
      montarTabela(dados.linhas, financeiro),
      ...secaoAnual,
      ...rodapeConteudo,
    ],
    footer: (currentPage, pageCount) => {
      if (currentPage === pageCount) {
        return {
          margin: [40, 0, 40, 20],
          stack: [
            { ...assinaturas, margin: [0, 0, 0, 8] },
            {
              text: `Página ${currentPage} de ${pageCount}`,
              alignment: 'center',
              fontSize: 9,
              color: '#555',
            },
          ],
        }
      }
      return {
        margin: [40, 0, 40, 20],
        text: `Página ${currentPage} de ${pageCount}`,
        alignment: 'center',
        fontSize: 9,
        color: '#555',
      }
    },
    styles: {
      tituloInstituicao: { fontSize: 13, bold: true },
      tituloRelatorio: { fontSize: 12, bold: true },
      tituloSecao: { fontSize: 11, bold: true },
      tableHeader: { bold: true, fillColor: '#f0f4f8', fontSize: 9 },
      linhaCancelada: { color: '#888', decoration: 'lineThrough' },
      cargoAssinatura: { fontSize: 9, color: '#444' },
    },
  }
}

export async function gerarRelatorioPdfBlob(dados, tipo, username) {
  const docDefinition = await montarDocDefinitionRelatorio(dados, tipo, username)
  return new Promise((resolve, reject) => {
    try {
      pdfMake.createPdf(docDefinition).getBlob((blob) => resolve(blob))
    } catch (err) {
      reject(err)
    }
  })
}

export async function imprimirRelatorioPdf(dados, tipo, username) {
  const blob = await gerarRelatorioPdfBlob(dados, tipo, username)
  const url = URL.createObjectURL(blob)

  return new Promise((resolve, reject) => {
    const iframe = document.createElement('iframe')
    iframe.style.cssText = 'position:fixed;right:0;bottom:0;width:0;height:0;border:none'
    iframe.title = 'Impressão relatório'

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
      reject(new Error('Não foi possível carregar o PDF do relatório.'))
    }

    iframe.src = url
    document.body.appendChild(iframe)
  })
}
