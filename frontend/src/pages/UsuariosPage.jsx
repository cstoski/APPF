import { useEffect, useState } from 'react'
import { Navigate } from 'react-router-dom'
import { IconEdit } from '../components/ActionIcons'
import UsuarioFormModal from '../components/UsuarioFormModal'
import { labelPerfil } from '../config/usuarioPerfis'
import { usuariosService } from '../services/api'
import { formatApiError } from '../utils/formatApiError'
import { useAuth } from '../hooks/useAuth.jsx'
import '../styles/operacional.css'

export default function UsuariosPage() {
  const { isAdmin } = useAuth()
  const [usuarios, setUsuarios] = useState([])
  const [loading, setLoading] = useState(false)
  const [error, setError] = useState('')
  const [success, setSuccess] = useState('')
  const [modal, setModal] = useState(null)

  const load = async () => {
    setLoading(true)
    setError('')
    try {
      const { data } = await usuariosService.listar()
      setUsuarios(data)
    } catch (err) {
      setError(formatApiError(err, 'Erro ao listar usuários.'))
    } finally {
      setLoading(false)
    }
  }

  useEffect(() => {
    if (isAdmin) load()
  }, [isAdmin])

  if (!isAdmin) {
    return <Navigate to="/dashboard" replace />
  }

  const desativar = async (usuario) => {
    if (!window.confirm(`Desativar o usuário "${usuario.username}"?`)) return
    setError('')
    setSuccess('')
    try {
      await usuariosService.desativar(usuario.id)
      setSuccess(`Usuário "${usuario.username}" desativado.`)
      await load()
    } catch (err) {
      setError(formatApiError(err, 'Erro ao desativar.'))
    }
  }

  const fecharModal = () => setModal(null)

  const aoSalvar = (mensagem) => {
    setSuccess(mensagem)
    setError('')
    load()
  }

  return (
    <div className="page-grid">
      <div className="section-header">
        <div>
          <h2 className="page-title">Usuários</h2>
          <p className="page-description">Cadastro e edição de operadores do sistema.</p>
        </div>
        <button type="button" className="btn btn-primary" onClick={() => setModal({ mode: 'create' })}>
          Novo usuário
        </button>
      </div>

      {error && <div className="alert alert-error">{error}</div>}
      {success && <div className="alert alert-success">{success}</div>}

      <section className="card card-strong data-table-wrap">
        <h3>Usuários cadastrados</h3>
        {loading && <p className="text-muted">Carregando...</p>}
        {!loading && usuarios.length === 0 && (
          <p className="text-muted">Nenhum usuário operador cadastrado.</p>
        )}
        {!loading && usuarios.length > 0 && (
          <table className="table table-usuarios">
            <thead>
              <tr>
                <th>Usuário</th>
                <th>Permissão</th>
                <th>Ativo</th>
                <th>Ações</th>
              </tr>
            </thead>
            <tbody>
              {usuarios.map((u) => (
                <tr key={u.id}>
                  <td>{u.username}</td>
                  <td>{labelPerfil(u.perfil)}</td>
                  <td>{u.ativo ? 'Sim' : 'Não'}</td>
                  <td>
                    <div className="table-actions">
                      {u.ativo && (
                        <>
                          <button
                            type="button"
                            className="btn btn-icon btn-outline"
                            onClick={() => setModal({ mode: 'edit', usuario: u })}
                            aria-label={`Editar ${u.username}`}
                            title="Editar"
                          >
                            <IconEdit />
                          </button>
                          <button
                            type="button"
                            className="btn btn-danger btn-sm"
                            onClick={() => desativar(u)}
                          >
                            Desativar
                          </button>
                        </>
                      )}
                    </div>
                  </td>
                </tr>
              ))}
            </tbody>
          </table>
        )}
      </section>

      {modal && (
        <UsuarioFormModal
          open
          mode={modal.mode}
          usuario={modal.usuario}
          onClose={fecharModal}
          onSaved={aoSalvar}
        />
      )}
    </div>
  )
}
