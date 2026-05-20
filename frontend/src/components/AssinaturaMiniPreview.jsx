import { useEffect, useState } from 'react'
import { staticAssetUrl } from '../services/api'

export default function AssinaturaMiniPreview({ caminho, arquivo, alt }) {
  const [src, setSrc] = useState('')

  useEffect(() => {
    if (arquivo) {
      const url = URL.createObjectURL(arquivo)
      setSrc(url)
      return () => URL.revokeObjectURL(url)
    }
    if (caminho) {
      setSrc(staticAssetUrl(caminho))
      return undefined
    }
    setSrc('')
    return undefined
  }, [caminho, arquivo])

  if (!src) {
    return (
      <span className="assinatura-mini assinatura-mini--empty" title="Nenhuma assinatura cadastrada">
        —
      </span>
    )
  }

  return <img src={src} alt={alt} className="assinatura-mini" title={alt} />
}
