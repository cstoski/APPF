import * as XLSX from 'xlsx'
import { formatCpfDisplay } from './masks'
import { formatDataGeracao, formatDataRecebimento, ordenarLinhasRelatorio } from './relatorioPdf'

function sanitizarNomeArquivo(texto) {
  return String(texto || 'relatorio')
    .normalize('NFD')
    .replace(/[\u0300-\u036f]/g, '')
    .replace(/[^\w\s-]/g, '')
    .replace(/\s+/g, '_')
    .slice(0, 60)
}

function montarNomeArquivoExcel(dados, tipo) {
  const financeiro = tipo === 'financeiro'
  if (financeiro) {
    const rotulo = String(dados.periodo_label || dados.periodo || 'periodo').replace(/\//g, '-')
    return `Relatorio_Financeiro_${rotulo}.xlsx`
  }
  const nome = sanitizarNomeArquivo(dados.contribuinte_nome)
  return `Informe_Contribuicoes_${nome}.xlsx`
}

function montarAbaResumo(dados, tipo, username) {
  const financeiro = tipo === 'financeiro'
  const inst = dados.instituicao || {}
  const linhas = [
    ['Relatório', dados.titulo],
    ['Instituição', inst.razao_social || ''],
    ['CNPJ', inst.cnpj || ''],
  ]

  if (financeiro) {
    linhas.push(['Período', dados.periodo_label])
  } else {
    linhas.push(
      ['Contribuinte', dados.contribuinte_nome || ''],
      ['CPF', dados.contribuinte_cpf ? formatCpfDisplay(dados.contribuinte_cpf) : ''],
      ['Período', dados.periodo_label],
    )
  }

  linhas.push([])
  if (dados.resumo) {
    linhas.push(['Quantidade', dados.resumo.quantidade])
    linhas.push(['Valor total', dados.resumo.valor_total])
    if (financeiro) {
      linhas.push(['Valor médio', dados.resumo.valor_medio])
    }
  }
  linhas.push(['Gerado em', formatDataGeracao()])
  linhas.push(['Usuário', username || ''])

  return XLSX.utils.aoa_to_sheet(linhas)
}

function montarAbaContribuicoes(dados, tipo) {
  const financeiro = tipo === 'financeiro'
  const linhas = ordenarLinhasRelatorio(dados.linhas)

  const rows = linhas.map((l) => {
    const row = {
      Data: formatDataRecebimento(l.data_contribuicao),
      'Nº recibo': l.numero,
      ...(financeiro ? { Contribuinte: l.contribuinte_nome || '' } : {}),
      Valor: Number(l.valor),
      Forma: l.forma_pagamento || '',
      Status: l.cancelado ? 'Cancelado' : 'Ativo',
    }
    return row
  })

  if (!rows.length) {
    const vazio = financeiro
      ? { Data: '', 'Nº recibo': '', Contribuinte: '', Valor: '', Forma: '', Status: '' }
      : { Data: '', 'Nº recibo': '', Valor: '', Forma: '', Status: '' }
    rows.push(vazio)
  }

  return XLSX.utils.json_to_sheet(rows)
}

function montarAbaResumoMensal(totaisMensais) {
  const rows = totaisMensais.map((m) => ({
    Mês: m.mes_label,
    Quantidade: m.quantidade,
    'Valor total': m.valor_total,
  }))
  const totalQtd = totaisMensais.reduce((s, m) => s + m.quantidade, 0)
  const totalVal = totaisMensais.reduce((s, m) => s + m.valor_total, 0)
  rows.push({ Mês: 'Total do ano', Quantidade: totalQtd, 'Valor total': totalVal })
  return XLSX.utils.json_to_sheet(rows)
}

export function exportarRelatorioExcel(dados, tipo, username) {
  if (!dados) {
    throw new Error('Gere o relatório antes de exportar para Excel.')
  }

  const wb = XLSX.utils.book_new()
  XLSX.utils.book_append_sheet(wb, montarAbaContribuicoes(dados, tipo), 'Contribuições')
  XLSX.utils.book_append_sheet(wb, montarAbaResumo(dados, tipo, username), 'Resumo')

  if (tipo === 'financeiro' && dados.periodo === 'anual' && dados.totais_mensais?.length) {
    XLSX.utils.book_append_sheet(wb, montarAbaResumoMensal(dados.totais_mensais), 'Resumo mensal')
  }

  XLSX.writeFile(wb, montarNomeArquivoExcel(dados, tipo))
}
