import { useState } from 'react'
import { IconMail, IconPdf, IconPrint, IconWhatsApp } from './ActionIcons'
import EnviarReciboEmailModal from './EnviarReciboEmailModal'
import EnviarReciboWhatsAppModal from './EnviarReciboWhatsAppModal'
import { contribuicaoService } from '../services/api'
import { baixarReciboPdf, formatDataEmissao } from '../utils/reciboPdf'
import { formatValorRecibo, imprimirRecibo } from '../utils/reciboShare'
import { formatarDataRecibo } from '../utils/reciboTexto'

/** Desative temporariamente o envio por WhatsApp; altere para true para reativar. */
const ENVIAR_WHATSAPP_RECIBO_HABILITADO = false

function registrarLogRecibo(reciboId, acao, detalhes) {
  contribuicaoService
    .registrarAcao(reciboId, { acao, detalhes: detalhes || undefined })
    .catch(() => {})
}

export default function ReciboViewCard({ recibo, contribuinte, configAppf }) {
  const [acaoLoading, setAcaoLoading] = useState(null)
  const [acaoErro, setAcaoErro] = useState('')
  const [emailModalAberto, setEmailModalAberto] = useState(false)
  const [whatsappModalAberto, setWhatsappModalAberto] = useState(false)
  const [emailSucesso, setEmailSucesso] = useState('')
  const [whatsappSucesso, setWhatsappSucesso] = useState('')
  const [pdfDuplicadoNaFolha, setPdfDuplicadoNaFolha] = useState(false)

  const opcoesPdf = { duplicarNaFolha: pdfDuplicadoNaFolha }

  if (!recibo) return null

  const exportacaoBloqueada = recibo.cancelado

  const executarAcao = async (nome, fn, logAcao) => {
    setAcaoLoading(nome)
    setAcaoErro('')
    try {
      await fn()
      if (logAcao) {
        registrarLogRecibo(recibo.id, logAcao)
      }
    } catch (err) {
      setAcaoErro(err?.message || 'Não foi possível concluir a ação.')
    } finally {
      setAcaoLoading(null)
    }
  }

  return (
    <section
      className={`card card-strong recibo-card ${recibo.cancelado ? 'cancelado' : ''}`}
      id="recibo-print-area"
      data-numero={recibo.numero}
    >
      <div className="recibo-card-header">
        <h3>Recibo {recibo.numero}</h3>
        <div className="recibo-actions">
          <button
            type="button"
            className="btn btn-icon btn-outline"
            onClick={() =>
              executarAcao(
                'pdf',
                () => baixarReciboPdf(recibo, contribuinte, configAppf, opcoesPdf),
                pdfDuplicadoNaFolha ? 'GERAR_PDF_DUPLICADO' : 'GERAR_PDF',
              )
            }
            title={exportacaoBloqueada ? 'Indisponível para recibos cancelados' : 'Gerar PDF'}
            aria-label="Gerar PDF do recibo"
            disabled={!!acaoLoading || exportacaoBloqueada}
          >
            <IconPdf />
          </button>
          <button
            type="button"
            className="btn btn-icon btn-outline"
            onClick={() =>
              executarAcao(
                'print',
                () => imprimirRecibo(recibo, contribuinte, configAppf, opcoesPdf),
                pdfDuplicadoNaFolha ? 'IMPRIMIR_DUPLICADO' : 'IMPRIMIR',
              )
            }
            title={exportacaoBloqueada ? 'Indisponível para recibos cancelados' : 'Imprimir'}
            aria-label="Imprimir recibo"
            disabled={!!acaoLoading || exportacaoBloqueada}
          >
            <IconPrint />
          </button>
          <button
            type="button"
            className="btn btn-icon btn-outline"
            onClick={() => {
              setEmailSucesso('')
              setEmailModalAberto(true)
            }}
            title={exportacaoBloqueada ? 'Indisponível para recibos cancelados' : 'Enviar por e-mail'}
            aria-label="Enviar recibo por e-mail"
            disabled={!!acaoLoading || exportacaoBloqueada}
          >
            <IconMail />
          </button>
          {ENVIAR_WHATSAPP_RECIBO_HABILITADO && (
            <button
              type="button"
              className="btn btn-icon btn-whatsapp"
              onClick={() => {
                setWhatsappSucesso('')
                setWhatsappModalAberto(true)
              }}
              title={exportacaoBloqueada ? 'Indisponível para recibos cancelados' : 'Enviar por WhatsApp'}
              aria-label="Enviar recibo por WhatsApp"
              disabled={!!acaoLoading || exportacaoBloqueada}
            >
              <IconWhatsApp />
            </button>
          )}
        </div>
      </div>

      {!exportacaoBloqueada && (
        <label className="recibo-pdf-opcao">
          <input
            type="checkbox"
            checked={pdfDuplicadoNaFolha}
            onChange={(e) => setPdfDuplicadoNaFolha(e.target.checked)}
          />
          Duplicar recibo na mesma folha (linha de recorte entre as vias)
        </label>
      )}

      {acaoLoading && (
        <p className="text-muted recibo-acao-status">Processando {acaoLoading}...</p>
      )}
      {acaoErro && <p className="alert alert-error">{acaoErro}</p>}
      {emailSucesso && <p className="alert alert-success">{emailSucesso}</p>}
      {ENVIAR_WHATSAPP_RECIBO_HABILITADO && whatsappSucesso && (
        <p className="alert alert-success">{whatsappSucesso}</p>
      )}

      <EnviarReciboEmailModal
        open={emailModalAberto}
        recibo={recibo}
        contribuinte={contribuinte}
        configAppf={configAppf}
        opcoesPdf={opcoesPdf}
        onClose={() => setEmailModalAberto(false)}
        onEnviado={(msg) => setEmailSucesso(msg)}
      />

      {ENVIAR_WHATSAPP_RECIBO_HABILITADO && (
        <EnviarReciboWhatsAppModal
          open={whatsappModalAberto}
          recibo={recibo}
          contribuinte={contribuinte}
          configAppf={configAppf}
          onClose={() => setWhatsappModalAberto(false)}
          onEnviado={(msg, telefone) => {
            setWhatsappSucesso(msg)
            if (telefone) {
              registrarLogRecibo(recibo.id, 'ENVIAR_WHATSAPP', `telefone=${telefone}`)
            }
          }}
        />
      )}

      <div className="recibo-detalhes">
        {contribuinte && (
          <p>
            <strong>Contribuinte:</strong> {contribuinte.nome_completo}
          </p>
        )}
        <p>
          <strong>Valor:</strong> {formatValorRecibo(recibo.valor)}
        </p>
        <p>
          <strong>Data da contribuição:</strong> {formatarDataRecibo(recibo.data_contribuicao)}
        </p>
        <p className="text-muted recibo-emissor">
          <strong>Registrado por:</strong> {recibo.usuario_emissor || '—'} em{' '}
          {formatDataEmissao(recibo.data_criacao)}
        </p>
        {recibo.forma_pagamento && (
          <p>
            <strong>Forma de pagamento:</strong> {recibo.forma_pagamento}
          </p>
        )}
        {recibo.descricao && (
          <p>
            <strong>Descrição:</strong> {recibo.descricao}
          </p>
        )}
        {recibo.cancelado && (
          <>
            <p className="alert alert-warning">
              <strong>Cancelado:</strong> {recibo.motivo_cancelamento || '—'}
              <br />
              <span className="recibo-cancelamento-meta">
                Por {recibo.usuario_cancelador || '—'} em{' '}
                {recibo.data_cancelamento ? formatDataEmissao(recibo.data_cancelamento) : '—'}
              </span>
            </p>
            <p className="text-muted recibo-exportacao-bloqueada">
              PDF, impressão e e-mail
              {ENVIAR_WHATSAPP_RECIBO_HABILITADO ? ' e WhatsApp' : ''} não estão disponíveis para
              recibos cancelados.
            </p>
          </>
        )}
      </div>
    </section>
  )
}
