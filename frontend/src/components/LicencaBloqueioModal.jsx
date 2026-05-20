import { useState } from 'react'
import { useNavigate } from 'react-router-dom'
import { useLicenca } from '../hooks/useLicenca.jsx'
import { useAuth } from '../hooks/useAuth.jsx'
import { sistemaService } from '../services/api'
import { formatApiError } from '../utils/formatApiError'
import { SERIAL_DEMO } from '../config/licencaDemo'
import {
  formatarSerialLicencaGrupos,
  serialLicencaCompletoParaEnvio,
} from '../utils/serialLicenca'

function copiarHwid(hwid) {
  if (navigator.clipboard?.writeText) {
    navigator.clipboard.writeText(hwid)
  }
}

export default function LicencaBloqueioModal() {
  const { licenca, loading, refreshLicenca } = useLicenca()
  const { perfil, username, logout } = useAuth()
  const navigate = useNavigate()
  const [serial, setSerial] = useState('')
  const [msg, setMsg] = useState('')
  const [erro, setErro] = useState('')
  const [ativando, setAtivando] = useState(false)

  if (loading || !licenca || licenca.pode_leitura) return null

  const ehMaster = perfil === 'MASTER'

  const handleSair = async () => {
    await logout()
    navigate('/login', { replace: true })
  }

  const handleAtivar = async (e) => {
    e.preventDefault()
    if (!ehMaster) return
    setAtivando(true)
    setErro('')
    setMsg('')
    try {
      const { data } = await sistemaService.ativarLicenca(serialLicencaCompletoParaEnvio(serial))
      setMsg(data.mensagem || 'Licença ativada.')
      setSerial('')
      await refreshLicenca()
    } catch (err) {
      setErro(formatApiError(err, 'Erro ao ativar licença.'))
    } finally {
      setAtivando(false)
    }
  }

  return (
    <div className="licenca-bloqueio-overlay" role="dialog" aria-modal="true" aria-labelledby="licenca-bloqueio-titulo">
      <div className="licenca-bloqueio-card card card-strong">
        <h2 id="licenca-bloqueio-titulo">Ativação necessária</h2>
        <p>
          Este computador ainda não possui licença em vigor (ou o prazo encerrou). Validade de{' '}
          <strong>{licenca.validade_dias ?? 365} dias</strong> por equipamento.
        </p>

        <p className="licenca-bloqueio-sessao text-muted">
          Sessão atual: <strong>{username}</strong> ({perfil || 'sem perfil'})
          {!ehMaster && (
            <span>
              {' '}
              — para ativar, saia e entre com o usuário <strong>zelo_master</strong> (MASTER).
            </span>
          )}
        </p>

        <ol className="licenca-passos">
          <li>
            Copie o <strong>HWID</strong> e envie ao suporte.
            <div className="licenca-bloqueio-hwid-row">
              <code className="licenca-hwid">{licenca.hwid}</code>
              <button type="button" className="btn btn-secondary btn-sm" onClick={() => copiarHwid(licenca.hwid)}>
                Copiar HWID
              </button>
            </div>
          </li>
          <li>
            Licença comercial: serial de 16 caracteres para este HWID. Demonstração (3 dias, 1x por PC):{' '}
            <code>{licenca?.serial_demo || SERIAL_DEMO}</code>
          </li>
          <li>
            {ehMaster
              ? 'Cole o serial abaixo e clique em Ativar licença.'
              : 'O perfil MASTER deve ativar o serial (use o botão Sair abaixo).'}
          </li>
        </ol>

        {licenca?.demo_consumido && licenca?.modo === 'DEMO_EXPIRADA' && (
          <p className="alert alert-warning">
            O serial de demonstração já foi usado neste equipamento e não pode ser inserido novamente.
          </p>
        )}

        {ehMaster && !(licenca?.demo_consumido && licenca?.modo === 'DEMO_EXPIRADA') && (
          <form onSubmit={handleAtivar} className="licenca-bloqueio-form">
            <label>
              Serial de ativação
              <input
                type="text"
                value={serial}
                onChange={(e) => setSerial(formatarSerialLicencaGrupos(e.target.value))}
                placeholder="XXXX-XXXX-XXXX-XXXX"
                maxLength={19}
                autoComplete="off"
                required
              />
            </label>
            {msg && <div className="alert alert-success">{msg}</div>}
            {erro && <div className="alert alert-error">{erro}</div>}
            <div className="form-actions">
              <button type="submit" className="btn btn-primary" disabled={ativando}>
                {ativando ? 'Ativando…' : 'Ativar licença'}
              </button>
            </div>
          </form>
        )}

        <div className="licenca-bloqueio-acoes">
          <button type="button" className="btn btn-secondary" onClick={handleSair}>
            Sair e trocar usuário
          </button>
        </div>
      </div>
    </div>
  )
}
