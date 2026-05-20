import { staticAssetUrl } from '../services/api'

export async function carregarImagemPdf(caminho) {
  if (!caminho?.trim()) return null
  try {
    const url = staticAssetUrl(caminho)
    const res = await fetch(url)
    if (!res.ok) return null
    const blob = await res.blob()
    return await new Promise((resolve, reject) => {
      const reader = new FileReader()
      reader.onload = () => resolve(typeof reader.result === 'string' ? reader.result : null)
      reader.onerror = () => reject(new Error('Erro ao ler imagem'))
      reader.readAsDataURL(blob)
    })
  } catch {
    return null
  }
}

/** Bloco de assinaturas (imagem, nome e cargo) para PDFs pdfMake. */
export function blocoAssinaturas(inst, imgPresidente, imgTesoureiro, opcoes = {}) {
  const larguraImg = opcoes.larguraImagem ?? 120
  const espacoSemImg = opcoes.espacoSemImagem ?? 28
  const colPresidente = {
    width: '*',
    stack: [
      imgPresidente
        ? { image: imgPresidente, width: larguraImg, alignment: 'center', margin: [0, 0, 0, 6] }
        : { text: '', margin: [0, espacoSemImg, 0, 0] },
      { text: inst.nome_presidente || '—', alignment: 'center', bold: true, fontSize: 10 },
      { text: 'Presidente', style: 'cargoAssinatura', alignment: 'center', margin: [0, 2, 0, 0] },
    ],
  }
  const colTesoureiro = {
    width: '*',
    stack: [
      imgTesoureiro
        ? { image: imgTesoureiro, width: larguraImg, alignment: 'center', margin: [0, 0, 0, 6] }
        : { text: '', margin: [0, espacoSemImg, 0, 0] },
      { text: inst.nome_tesoureiro || '—', alignment: 'center', bold: true, fontSize: 10 },
      { text: 'Tesoureiro', style: 'cargoAssinatura', alignment: 'center', margin: [0, 2, 0, 0] },
    ],
  }
  return { columns: [colPresidente, colTesoureiro], columnGap: 24 }
}
