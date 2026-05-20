import { useEffect, useRef, useState } from 'react'
import { createPortal } from 'react-dom'
import {
  APP_NOME,
  APP_PRODUTO,
  APP_VERSAO_FRONTEND,
  MANUAL_URL,
  SUPORTE,
  TERMOS_DE_USO,
} from '../config/sobre'
import { sistemaService } from '../services/api'

function SobreModal({ modal, onClose, infoBackend, carregandoInfo }) {
  useEffect(() => {
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
  }, [onClose])

  return createPortal(
    <div className="modal-overlay sobre-modal-overlay" onClick={onClose} role="presentation">
      <div
        className="modal-panel card card-strong sobre-modal"
        onClick={(e) => e.stopPropagation()}
        role="dialog"
        aria-modal="true"
        aria-labelledby="sobre-modal-title"
      >
        <div className="modal-header">
          <h3 id="sobre-modal-title">
            {modal === 'versao' && 'Versão da aplicação'}
            {modal === 'termos' && 'Termos de uso'}
            {modal === 'suporte' && 'Suporte técnico'}
          </h3>
          <button type="button" className="btn btn-outline" onClick={onClose}>
            Fechar
          </button>
        </div>

        {modal === 'versao' && (
          <div className="sobre-conteudo">
            <p>
              <strong>{APP_NOME}</strong> — {APP_PRODUTO}
            </p>
            <dl className="sobre-dl">
              <dt>Versão do frontend</dt>
              <dd>{APP_VERSAO_FRONTEND}</dd>
              <dt>Versão da API</dt>
              <dd>
                {carregandoInfo
                  ? 'Carregando...'
                  : infoBackend?.versao || 'Indisponível (servidor offline)'}
              </dd>
              {infoBackend?.build && (
                <>
                  <dt>Build</dt>
                  <dd>{infoBackend.build}</dd>
                </>
              )}
            </dl>
            <p className="text-muted">
              Sistema local para gestão de contribuições, recibos e relatórios da APPF.
            </p>
            <div className="form-actions">
              <a
                href={MANUAL_URL}
                className="btn btn-outline"
                target="_blank"
                rel="noopener noreferrer"
              >
                Abrir manual
              </a>
            </div>
          </div>
        )}

        {modal === 'termos' && (
          <div className="sobre-conteudo sobre-termos">{TERMOS_DE_USO}</div>
        )}

        {modal === 'suporte' && (
          <div className="sobre-conteudo">
            <p>Entre em contato com a equipe de suporte técnico:</p>
            <dl className="sobre-dl">
              <dt>E-mail</dt>
              <dd>
                <a href={`mailto:${SUPORTE.email}`}>{SUPORTE.email}</a>
              </dd>
              <dt>Telefone</dt>
              <dd>
                <a href={`tel:${SUPORTE.telefone.replace(/\D/g, '')}`}>{SUPORTE.telefone}</a>
              </dd>
              <dt>Horário</dt>
              <dd>{SUPORTE.horario}</dd>
            </dl>
            <p className="text-muted">{SUPORTE.observacao}</p>
            <div className="form-actions">
              <a href={MANUAL_URL} className="btn btn-outline" target="_blank" rel="noopener noreferrer">
                Consultar manual
              </a>
              <a href={`mailto:${SUPORTE.email}`} className="btn btn-primary">
                Enviar e-mail
              </a>
            </div>
          </div>
        )}
      </div>
    </div>,
    document.body,
  )
}

export default function SobreMenu() {
  const [menuAberto, setMenuAberto] = useState(false)
  const [modal, setModal] = useState(null)
  const [infoBackend, setInfoBackend] = useState(null)
  const [carregandoInfo, setCarregandoInfo] = useState(false)
  const containerRef = useRef(null)

  useEffect(() => {
    if (!menuAberto) return undefined

    const fecharAoClicarFora = (e) => {
      if (containerRef.current && !containerRef.current.contains(e.target)) {
        setMenuAberto(false)
      }
    }
    const fecharComEsc = (e) => {
      if (e.key === 'Escape') setMenuAberto(false)
    }
    document.addEventListener('mousedown', fecharAoClicarFora)
    document.addEventListener('keydown', fecharComEsc)
    return () => {
      document.removeEventListener('mousedown', fecharAoClicarFora)
      document.removeEventListener('keydown', fecharComEsc)
    }
  }, [menuAberto])

  useEffect(() => {
    if (modal !== 'versao') return undefined

    let cancelado = false
    setCarregandoInfo(true)
    sistemaService
      .info()
      .then(({ data }) => {
        if (!cancelado) setInfoBackend(data)
      })
      .catch(() => {
        if (!cancelado) setInfoBackend(null)
      })
      .finally(() => {
        if (!cancelado) setCarregandoInfo(false)
      })

    return () => {
      cancelado = true
    }
  }, [modal])

  const abrirModal = (tipo) => {
    setMenuAberto(false)
    setModal(tipo)
  }

  const fecharModal = () => {
    setModal(null)
    setInfoBackend(null)
  }

  return (
    <>
      <div className="navbar-sobre" ref={containerRef}>
        <button
          type="button"
          className="btn btn-outline navbar-sobre-trigger"
          onClick={() => setMenuAberto((v) => !v)}
          aria-expanded={menuAberto}
          aria-haspopup="true"
        >
          Sobre
        </button>

        {menuAberto && (
          <div className="navbar-sobre-dropdown" role="menu">
            <button type="button" role="menuitem" onClick={() => abrirModal('versao')}>
              Versão da aplicação
            </button>
            <button type="button" role="menuitem" onClick={() => abrirModal('termos')}>
              Termos de uso
            </button>
            <button type="button" role="menuitem" onClick={() => abrirModal('suporte')}>
              Suporte técnico
            </button>
            <a
              href={MANUAL_URL}
              role="menuitem"
              target="_blank"
              rel="noopener noreferrer"
              onClick={() => setMenuAberto(false)}
            >
              Manual do usuário
            </a>
          </div>
        )}
      </div>

      {modal && (
        <SobreModal
          modal={modal}
          onClose={fecharModal}
          infoBackend={infoBackend}
          carregandoInfo={carregandoInfo}
        />
      )}
    </>
  )
}
