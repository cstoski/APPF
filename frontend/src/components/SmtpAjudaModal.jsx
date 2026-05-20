import { useEffect } from 'react'
import { createPortal } from 'react-dom'
import { SMTP_AJUDA_CAMPOS } from '../config/smtpAjuda'

function ConteudoAjuda({ campo }) {
  if (!campo) return null
  const info = SMTP_AJUDA_CAMPOS[campo]
  if (!info) return null

  return (
    <div className="ajuda-campo-body">
      <p>
        <strong>O que é:</strong> {info.oQueE}
      </p>
      <p>
        <strong>Onde encontrar no servidor de e-mail:</strong> {info.ondeEncontrar}
      </p>
      {info.dicas?.length > 0 && (
        <>
          <p>
            <strong>Dicas:</strong>
          </p>
          <ul>
            {info.dicas.map((dica) => (
              <li key={dica}>{dica}</li>
            ))}
          </ul>
        </>
      )}
    </div>
  )
}

export default function SmtpAjudaModal({ open, campo, onClose }) {
  useEffect(() => {
    if (!open) return undefined
    const onKey = (e) => {
      if (e.key === 'Escape') onClose()
    }
    document.addEventListener('keydown', onKey)
    const prevOverflow = document.body.style.overflow
    document.body.style.overflow = 'hidden'
    return () => {
      document.removeEventListener('keydown', onKey)
      document.body.style.overflow = prevOverflow
    }
  }, [open, onClose])

  if (!open) return null

  const titulo = SMTP_AJUDA_CAMPOS[campo]?.titulo || 'Ajuda SMTP'

  return createPortal(
    <div className="modal-overlay smtp-ajuda-overlay" onClick={onClose} role="presentation">
      <div
        className="modal-panel card card-strong smtp-ajuda-modal"
        onClick={(e) => e.stopPropagation()}
        role="dialog"
        aria-modal="true"
        aria-labelledby="smtp-ajuda-title"
      >
        <div className="modal-header">
          <h3 id="smtp-ajuda-title">{titulo}</h3>
          <button type="button" className="btn btn-outline" onClick={onClose}>
            Fechar
          </button>
        </div>

        <ConteudoAjuda campo={campo} />
      </div>
    </div>,
    document.body,
  )
}

export function BotaoAjudaCampo({ campo, onAbrir }) {
  const info = SMTP_AJUDA_CAMPOS[campo]
  if (!info) return null

  return (
    <button
      type="button"
      className="btn-ajuda-campo"
      onClick={() => onAbrir(campo)}
      aria-label={`Informações sobre ${info.titulo}`}
      title={`O que é ${info.titulo}?`}
    >
      ?
    </button>
  )
}
