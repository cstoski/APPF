import { useEffect, useState } from 'react'
import { useSearchParams } from 'react-router-dom'
import { appfService, sistemaService } from '../services/api'
import { formatApiError } from '../utils/formatApiError'
import { useAuth } from '../hooks/useAuth.jsx'
import { useLicenca } from '../hooks/useLicenca.jsx'
import AssinaturaMiniPreview from '../components/AssinaturaMiniPreview'
import SmtpAjudaModal, { BotaoAjudaCampo } from '../components/SmtpAjudaModal'
import TrocarMinhaSenhaForm from '../components/TrocarMinhaSenhaForm'
import { SMTP_AJUDA_INTRO } from '../config/smtpAjuda'
import { SERIAL_DEMO, VALIDADE_DIAS_DEMO } from '../config/licencaDemo'
import { exibirSerialLicenca, formatarSerialLicencaGrupos, serialLicencaCompletoParaEnvio } from '../utils/serialLicenca'
import '../styles/operacional.css'

function formatarDataHoraPtBr(iso) {
  if (!iso) return '—'
  try {
    return new Intl.DateTimeFormat('pt-BR', { dateStyle: 'long', timeStyle: 'short' }).format(new Date(iso))
  } catch {
    return '—'
  }
}

const emptyConfig = {
  razao_social: '',
  cnpj: '',
  endereco: '',
  nome_presidente: '',
  nome_tesoureiro: '',
  caminho_assinatura_presidente: '',
  caminho_assinatura_tesoureiro: '',
  smtp_host: 'localhost',
  smtp_porta: 587,
  smtp_usuario: '',
  smtp_remetente: 'nao-responder@appf.local',
  smtp_usar_starttls: true,
  smtp_senha_configurada: false,
}

function rotuloModoLicenca(modo) {
  const map = {
    ATIVA: 'Vigente — operações liberadas',
    GRACE: 'Expirada — somente leitura (cortesia)',
    EXPIRADA: 'Expirada — bloqueio total',
    DEMO_EXPIRADA: 'Demonstração encerrada — serial demo não pode ser reutilizado',
    NAO_ATIVADA: 'Não ativada neste computador',
    INTEGRIDADE_FALHA: 'Dados inválidos — contate o suporte',
  }
  return map[modo] || modo
}

function tabInicialFromUrl(searchParams, podeTrocarSenha) {
  const t = searchParams.get('tab')
  if (t === 'email') return 'email'
  if (t === 'licenca') return 'licenca'
  if (t === 'senha' && podeTrocarSenha) return 'senha'
  if (podeTrocarSenha && !t) return 'senha'
  return 'appf'
}

export default function ConfiguracaoPage() {
  const { isAdmin, username, perfil } = useAuth()
  const { licenca, refreshLicenca } = useLicenca()
  const podeAtivarLicenca = perfil === 'MASTER'
  const podeTrocarSenha = !isAdmin && perfil !== 'DEV'
  const [searchParams] = useSearchParams()
  const tabInicial = tabInicialFromUrl(searchParams, podeTrocarSenha)
  const [tab, setTab] = useState(tabInicial)
  const [config, setConfig] = useState(emptyConfig)
  const [assinPresidente, setAssinPresidente] = useState(null)
  const [assinTesoureiro, setAssinTesoureiro] = useState(null)
  const [smtpSenha, setSmtpSenha] = useState('')
  const [serial, setSerial] = useState('')
  const [loading, setLoading] = useState(false)
  const [error, setError] = useState('')
  const [success, setSuccess] = useState('')
  const [validacao, setValidacao] = useState(null)
  const [ajudaSmtpCampo, setAjudaSmtpCampo] = useState(null)

  const aplicarResultadoValidacao = (resultado, escopoLabel, { salvou = false } = {}) => {
    setValidacao(resultado)
    if (!resultado) return
    const falhas = resultado.itens.filter((i) => !i.ok)
    if (resultado.ok) {
      setSuccess(
        salvou
          ? escopoLabel === 'e-mail'
            ? 'Configuração de e-mail salva e conexão SMTP verificada com sucesso.'
            : 'Configuração APPF salva e validada com sucesso.'
          : escopoLabel === 'e-mail'
            ? 'Configuração de e-mail atual está correta (conexão SMTP OK).'
            : 'Configuração APPF atual está completa.',
      )
      setError('')
    } else if (salvou) {
      setSuccess('Dados salvos no sistema.')
      setError(
        `Salvo, mas a validação encontrou ${falhas.length} problema(s):\n` +
          falhas.map((i) => `• ${i.mensagem}`).join('\n'),
      )
    } else {
      setSuccess('')
      setError(
        `Validação encontrou ${falhas.length} problema(s):\n` +
          falhas.map((i) => `• ${i.mensagem}`).join('\n'),
      )
    }
  }

  const load = async () => {
    setLoading(true)
    setError('')
    try {
      const cfgRes = await appfService.obterConfig()
      setConfig({
        razao_social: cfgRes.data.razao_social || '',
        cnpj: cfgRes.data.cnpj || '',
        endereco: cfgRes.data.endereco || '',
        nome_presidente: cfgRes.data.nome_presidente || '',
        nome_tesoureiro: cfgRes.data.nome_tesoureiro || '',
        caminho_assinatura_presidente: cfgRes.data.caminho_assinatura_presidente || '',
        caminho_assinatura_tesoureiro: cfgRes.data.caminho_assinatura_tesoureiro || '',
        smtp_host: cfgRes.data.smtp_host || 'localhost',
        smtp_porta: cfgRes.data.smtp_porta ?? 587,
        smtp_usuario: cfgRes.data.smtp_usuario || '',
        smtp_remetente: cfgRes.data.smtp_remetente || 'nao-responder@appf.local',
        smtp_usar_starttls: cfgRes.data.smtp_usar_starttls !== false,
        smtp_senha_configurada: !!cfgRes.data.smtp_senha_configurada,
      })
      setSmtpSenha('')
      await refreshLicenca()
    } catch (err) {
      setError(formatApiError(err, 'Erro ao carregar configurações.'))
    } finally {
      setLoading(false)
    }
  }

  useEffect(() => {
    load()
  }, [])

  const salvarAppf = async (e, escopoValidacao = 'appf') => {
    e.preventDefault()
    if (!isAdmin) {
      setError('Apenas MASTER ou DEV podem alterar a configuração APPF.')
      return
    }
    setLoading(true)
    setError('')
    setSuccess('')
    setValidacao(null)
    try {
      const fd = new FormData()
      fd.append('razao_social', config.razao_social)
      fd.append('cnpj', config.cnpj)
      fd.append('endereco', config.endereco)
      fd.append('nome_presidente', config.nome_presidente)
      fd.append('nome_tesoureiro', config.nome_tesoureiro)
      fd.append('smtp_host', config.smtp_host)
      fd.append('smtp_porta', String(config.smtp_porta))
      fd.append('smtp_usuario', config.smtp_usuario || '')
      fd.append('smtp_remetente', config.smtp_remetente)
      fd.append('smtp_usar_starttls', config.smtp_usar_starttls ? 'true' : 'false')
      fd.append('escopo_validacao', escopoValidacao)
      if (smtpSenha.trim()) fd.append('smtp_senha', smtpSenha.trim())
      if (assinPresidente) fd.append('assinatura_presidente', assinPresidente)
      if (assinTesoureiro) fd.append('assinatura_tesoureiro', assinTesoureiro)
      const { data } = await appfService.salvarConfig(fd)
      aplicarResultadoValidacao(data.validacao, escopoValidacao === 'email' ? 'e-mail' : 'APPF', {
        salvou: true,
      })
      setAssinPresidente(null)
      setAssinTesoureiro(null)
      await load()
    } catch (err) {
      setError(formatApiError(err, 'Erro ao salvar configuração.'))
      setValidacao(null)
    } finally {
      setLoading(false)
    }
  }

  const testarSemSalvar = async (escopo) => {
    if (!isAdmin) return
    setLoading(true)
    setError('')
    setSuccess('')
    setValidacao(null)
    try {
      const { data } = await appfService.validarConfig(escopo)
      aplicarResultadoValidacao(data, escopo === 'email' ? 'e-mail' : 'APPF', { salvou: false })
    } catch (err) {
      setError(formatApiError(err, 'Erro ao validar configuração.'))
    } finally {
      setLoading(false)
    }
  }

  const copiarHwid = () => {
    if (licenca?.hwid && navigator.clipboard?.writeText) {
      navigator.clipboard.writeText(licenca.hwid)
      setSuccess('HWID copiado para a área de transferência.')
      setError('')
    }
  }

  const ativarLicenca = async (e) => {
    e.preventDefault()
    if (!podeAtivarLicenca) {
      setError('Somente o perfil MASTER pode ativar ou renovar a licença.')
      return
    }
    setLoading(true)
    setError('')
    setSuccess('')
    try {
      const { data } = await sistemaService.ativarLicenca(serialLicencaCompletoParaEnvio(serial))
      setSuccess(data.mensagem || 'Licença ativada.')
      setSerial('')
      await refreshLicenca()
    } catch (err) {
      setError(formatApiError(err, 'Erro ao ativar licença.'))
    } finally {
      setLoading(false)
    }
  }

  return (
    <div className="page-grid">
      <div className="section-header">
        <div>
          <h2 className="page-title">Configuração</h2>
          <p className="page-description">Dados da APPF, e-mail (SMTP), assinaturas e licença offline.</p>
        </div>
      </div>

      <div className="tabs">
        {podeTrocarSenha && (
          <button type="button" className={`tab-btn ${tab === 'senha' ? 'active' : ''}`} onClick={() => setTab('senha')}>
            Minha senha
          </button>
        )}
        <button type="button" className={`tab-btn ${tab === 'appf' ? 'active' : ''}`} onClick={() => setTab('appf')}>
          APPF
        </button>
        <button type="button" className={`tab-btn ${tab === 'email' ? 'active' : ''}`} onClick={() => setTab('email')}>
          E-mail
        </button>
        <button type="button" className={`tab-btn ${tab === 'licenca' ? 'active' : ''}`} onClick={() => setTab('licenca')}>
          Licença
        </button>
      </div>

      {error && (
        <div className="alert alert-error" style={{ whiteSpace: 'pre-line' }}>
          {error}
        </div>
      )}
      {success && <div className="alert alert-success">{success}</div>}
      {validacao && (
        <section className="card config-validacao-card">
          <h4 className="config-validacao-title">
            Resultado da validação {validacao.ok ? '— OK' : '— atenção'}
          </h4>
          <ul className="config-validacao-list">
            {validacao.itens.map((item) => (
              <li key={item.campo} className={item.ok ? 'ok' : 'fail'}>
                <span className="config-validacao-icon" aria-hidden="true">
                  {item.ok ? '✓' : '✗'}
                </span>
                {item.mensagem}
              </li>
            ))}
          </ul>
        </section>
      )}

      {tab === 'senha' && podeTrocarSenha && (
        <section className="card card-strong">
          <h3>Alterar minha senha</h3>
          <p className="text-muted">
            Informe a senha atual e defina uma nova senha de acesso ao sistema. Mínimo de 6 caracteres.
          </p>
          <TrocarMinhaSenhaForm
            username={username}
            onSucesso={(msg) => {
              setSuccess(msg)
              setError('')
            }}
            onErro={(msg) => {
              setError(msg)
              setSuccess('')
            }}
          />
        </section>
      )}

      {tab === 'licenca' && (
        <section className="card card-strong">
          <h3>Licença do sistema</h3>
          <p className="text-muted licenca-intro">
            <strong>Uma licença por computador</strong> (HWID). Validade fixa de{' '}
            <strong>{licenca?.validade_dias ?? 365} dias</strong> a partir da data de emissão do serial.
            Após expirar, há <strong>{licenca?.grace_dias ?? 7} dias</strong> de cortesia apenas para consulta.
            Ativação e renovação: <strong>somente perfil MASTER</strong>.
          </p>
          <p className="text-muted licenca-demo-hint">
            <strong>Modo demonstração (3 dias, uma vez por equipamento):</strong> serial fixo{' '}
            <code>{licenca?.serial_demo || SERIAL_DEMO}</code> — válido em qualquer instalação, mas cada
            computador só pode usar uma vez; após 3 dias o sistema bloqueia e o serial demo não libera de novo.
          </p>

          {licenca ? (
            <>
              {licenca.modo === 'ATIVA' && (
                <div className="alert alert-success">
                  Licença em vigor até {formatarDataHoraPtBr(licenca.data_expiracao)}.
                  {typeof licenca.dias_restantes === 'number' && (
                    <span> Restam {licenca.dias_restantes} dia(s).</span>
                  )}
                </div>
              )}
              {licenca.modo === 'DEMO_EXPIRADA' && (
                <div className="alert alert-danger">
                  Demonstração encerrada. O serial demo já foi consumido neste equipamento e não pode ser
                  reutilizado. Solicite licença comercial (serial gerado para o HWID).
                </div>
              )}
              {licenca.eh_demo && licenca.modo === 'ATIVA' && (
                <div className="alert alert-info">
                  Modo demonstração ativo — restam {licenca.dias_restantes ?? 0} dia(s) de {VALIDADE_DIAS_DEMO}{' '}
                  dias de teste.
                </div>
              )}
              {licenca.modo === 'GRACE' && (
                <div className="alert alert-warning">
                  Licença expirada — modo somente leitura por mais {licenca.grace_dias_restantes ?? 0} dia(s).
                  Renove com um serial novo gerado para este HWID.
                </div>
              )}
              {(licenca.modo === 'NAO_ATIVADA' || licenca.modo === 'EXPIRADA') && (
                <div className="alert alert-danger">
                  Sistema bloqueado para operações. {podeAtivarLicenca ? 'Ative abaixo.' : 'Solicite ao MASTER.'}
                </div>
              )}
              {licenca.modo === 'INTEGRIDADE_FALHA' && (
                <div className="alert alert-error">
                  Licença adulterada ou inválida. Não edite o banco manualmente. Contate o suporte.
                </div>
              )}

              <ol className="licenca-passos">
                <li>
                  Copie o HWID e envie ao suporte para gerar o serial deste equipamento.
                  <div className="licenca-bloqueio-hwid-row">
                    <code className="licenca-hwid">{licenca.hwid}</code>
                    <button type="button" className="btn btn-secondary btn-sm" onClick={copiarHwid}>
                      Copiar HWID
                    </button>
                  </div>
                </li>
                <li>Receba o serial (16 caracteres) gerado exclusivamente para este HWID.</li>
                <li>
                  {podeAtivarLicenca
                    ? 'Cole o serial abaixo e clique em Ativar ou renovar.'
                    : 'O perfil MASTER deve colar o serial nesta tela.'}
                </li>
              </ol>

              <dl className="licenca-dl">
                <dt>Situação</dt>
                <dd>{rotuloModoLicenca(licenca.modo)}</dd>
                <dt>Emissão do serial</dt>
                <dd>
                  {licenca.data_emissao_serial
                    ? new Intl.DateTimeFormat('pt-BR').format(new Date(licenca.data_emissao_serial))
                    : '—'}
                </dd>
                <dt>Última ativação no sistema</dt>
                <dd>{licenca.data_ativacao ? formatarDataHoraPtBr(licenca.data_ativacao) : '—'}</dd>
                <dt>Expira em</dt>
                <dd>{licenca.data_expiracao ? formatarDataHoraPtBr(licenca.data_expiracao) : '—'}</dd>
                <dt>Tipo</dt>
                <dd>{licenca.eh_demo ? 'Demonstração' : 'Comercial'}</dd>
                <dt>Serial atual</dt>
                <dd>{exibirSerialLicenca(licenca.serial)}</dd>
                {licenca.demo_consumido && (
                  <>
                    <dt>Serial demo</dt>
                    <dd>
                      <code>{licenca.serial_demo || SERIAL_DEMO}</code>
                      {licenca.demo_consumido && ' — já utilizado neste equipamento'}
                    </dd>
                  </>
                )}
              </dl>

              {podeAtivarLicenca ? (
                <form onSubmit={ativarLicenca} className="mt-3">
                  <label>
                    Serial de ativação / renovação
                    <input
                      type="text"
                      value={serial}
                      onChange={(e) => setSerial(formatarSerialLicencaGrupos(e.target.value))}
                      placeholder="XXXX-XXXX-XXXX-XXXX"
                      maxLength={19}
                      autoComplete="off"
                      spellCheck={false}
                      inputMode="text"
                      required
                    />
                  </label>
                  <p className="text-muted form-field-hint licenca-serial-hint">
                    Licença comercial: serial gerado para este HWID (365 dias). Demonstração: use{' '}
                    <code>{SERIAL_DEMO}</code> (3 dias, uma vez por PC; não reutilizável após expirar).
                  </p>
                  <div className="form-actions">
                    <button type="submit" className="btn btn-primary" disabled={loading}>
                      Ativar ou renovar licença
                    </button>
                  </div>
                </form>
              ) : (
                <p className="alert alert-info">Somente usuários MASTER podem ativar ou renovar a licença.</p>
              )}
            </>
          ) : (
            <p className="text-muted">Carregando status da licença…</p>
          )}
        </section>
      )}

      {tab === 'appf' && (
        <section className="card card-strong">
          <h3>Dados da APPF</h3>
          {!isAdmin && (
            <p className="alert alert-info">Somente leitura. Perfil atual não pode editar.</p>
          )}
          <form onSubmit={(e) => salvarAppf(e, 'appf')}>
            <div className="form-appf">
              <div className="form-row form-row-2">
                <label>
                  Razão social
                  <input
                    value={config.razao_social}
                    onChange={(e) => setConfig({ ...config, razao_social: e.target.value })}
                    disabled={!isAdmin}
                    required
                  />
                </label>
                <label>
                  CNPJ
                  <input
                    value={config.cnpj}
                    onChange={(e) => setConfig({ ...config, cnpj: e.target.value })}
                    disabled={!isAdmin}
                    required
                  />
                </label>
              </div>
              <div className="form-row">
                <label>
                  Endereço
                  <input
                    value={config.endereco}
                    onChange={(e) => setConfig({ ...config, endereco: e.target.value })}
                    disabled={!isAdmin}
                    required
                  />
                </label>
              </div>
              <div className="form-row form-row-2">
                <label>
                  Nome do tesoureiro
                  <input
                    value={config.nome_tesoureiro}
                    onChange={(e) => setConfig({ ...config, nome_tesoureiro: e.target.value })}
                    disabled={!isAdmin}
                    required
                  />
                </label>
                <div className="form-assinatura-col">
                  <span className="form-assinatura-label">Assinatura</span>
                  <div className="form-assinatura-row">
                    <AssinaturaMiniPreview
                      caminho={config.caminho_assinatura_tesoureiro}
                      arquivo={assinTesoureiro}
                      alt="Assinatura do tesoureiro"
                    />
                    {isAdmin && (
                      <label className="form-assinatura-file">
                        <span className="label-optional">Alterar (PNG/JPG)</span>
                        <input
                          type="file"
                          accept=".png,.jpg,.jpeg"
                          onChange={(e) => setAssinTesoureiro(e.target.files?.[0] || null)}
                        />
                      </label>
                    )}
                  </div>
                </div>
              </div>
              <div className="form-row form-row-2">
                <label>
                  Nome do presidente
                  <input
                    value={config.nome_presidente}
                    onChange={(e) => setConfig({ ...config, nome_presidente: e.target.value })}
                    disabled={!isAdmin}
                    required
                  />
                </label>
                <div className="form-assinatura-col">
                  <span className="form-assinatura-label">Assinatura</span>
                  <div className="form-assinatura-row">
                    <AssinaturaMiniPreview
                      caminho={config.caminho_assinatura_presidente}
                      arquivo={assinPresidente}
                      alt="Assinatura do presidente"
                    />
                    {isAdmin && (
                      <label className="form-assinatura-file">
                        <span className="label-optional">Alterar (PNG/JPG)</span>
                        <input
                          type="file"
                          accept=".png,.jpg,.jpeg"
                          onChange={(e) => setAssinPresidente(e.target.files?.[0] || null)}
                        />
                      </label>
                    )}
                  </div>
                </div>
              </div>
            </div>
            {isAdmin && (
              <div className="form-actions">
                <button type="button" className="btn btn-secondary" disabled={loading} onClick={() => testarSemSalvar('appf')}>
                  Testar configuração atual
                </button>
                <button type="submit" className="btn btn-primary" disabled={loading}>
                  Salvar e validar
                </button>
              </div>
            )}
          </form>
        </section>
      )}

      {tab === 'email' && (
        <section className="card card-strong">
          <h3>Servidor de e-mail (SMTP)</h3>
          <p className="text-muted">{SMTP_AJUDA_INTRO}</p>
          <p className="text-muted">
            A senha é armazenada de forma cifrada no sistema.
          </p>
          {!isAdmin && (
            <p className="alert alert-info">Somente leitura. Perfil atual não pode editar.</p>
          )}
          <form onSubmit={(e) => salvarAppf(e, 'email')}>
            <div className="form-appf">
              <div className="form-row form-row-2">
                <label>
                  <span className="label-with-help">
                    Host SMTP
                    <BotaoAjudaCampo campo="host" onAbrir={setAjudaSmtpCampo} />
                  </span>
                  <input
                    value={config.smtp_host}
                    onChange={(e) => setConfig({ ...config, smtp_host: e.target.value })}
                    disabled={!isAdmin}
                    required
                    placeholder="smtp.exemplo.com"
                  />
                </label>
                <label>
                  <span className="label-with-help">
                    Porta
                    <BotaoAjudaCampo campo="porta" onAbrir={setAjudaSmtpCampo} />
                  </span>
                  <input
                    type="number"
                    min={1}
                    max={65535}
                    value={config.smtp_porta}
                    onChange={(e) => setConfig({ ...config, smtp_porta: Number(e.target.value) })}
                    disabled={!isAdmin}
                    required
                  />
                </label>
              </div>
              <div className="form-row form-row-2">
                <label>
                  <span className="label-with-help">
                    Usuário <span className="label-optional">(opcional)</span>
                    <BotaoAjudaCampo campo="usuario" onAbrir={setAjudaSmtpCampo} />
                  </span>
                  <input
                    value={config.smtp_usuario}
                    onChange={(e) => setConfig({ ...config, smtp_usuario: e.target.value })}
                    disabled={!isAdmin}
                    autoComplete="off"
                  />
                </label>
                <label>
                  <span className="label-with-help">
                    Senha{' '}
                    {config.smtp_senha_configurada && (
                      <span className="label-optional">(deixe em branco para manter)</span>
                    )}
                    <BotaoAjudaCampo campo="senha" onAbrir={setAjudaSmtpCampo} />
                  </span>
                  <input
                    type="password"
                    value={smtpSenha}
                    onChange={(e) => setSmtpSenha(e.target.value)}
                    disabled={!isAdmin}
                    autoComplete="new-password"
                    placeholder={config.smtp_senha_configurada ? '••••••••' : ''}
                  />
                </label>
              </div>
              <div className="form-row form-row-2">
                <label>
                  <span className="label-with-help">
                    E-mail remetente
                    <BotaoAjudaCampo campo="remetente" onAbrir={setAjudaSmtpCampo} />
                  </span>
                  <input
                    type="email"
                    value={config.smtp_remetente}
                    onChange={(e) => setConfig({ ...config, smtp_remetente: e.target.value })}
                    disabled={!isAdmin}
                    required
                  />
                </label>
                <div className="form-smtp-starttls-wrap">
                  <span className="label-with-help form-assinatura-label">
                    Usar STARTTLS
                    <BotaoAjudaCampo campo="starttls" onAbrir={setAjudaSmtpCampo} />
                  </span>
                  <label className="checkbox-inline form-smtp-starttls">
                    <input
                      type="checkbox"
                      checked={!!config.smtp_usar_starttls}
                      onChange={(e) => setConfig({ ...config, smtp_usar_starttls: e.target.checked })}
                      disabled={!isAdmin}
                    />
                    Ativar criptografia TLS na conexão
                  </label>
                </div>
              </div>
            </div>
            {isAdmin && (
              <div className="form-actions">
                <button type="button" className="btn btn-secondary" disabled={loading} onClick={() => testarSemSalvar('email')}>
                  Testar conexão SMTP
                </button>
                <button type="submit" className="btn btn-primary" disabled={loading}>
                  Salvar e testar SMTP
                </button>
              </div>
            )}
          </form>
          <SmtpAjudaModal
            open={!!ajudaSmtpCampo}
            campo={ajudaSmtpCampo}
            onClose={() => setAjudaSmtpCampo(null)}
          />
        </section>
      )}
    </div>
  )
}
