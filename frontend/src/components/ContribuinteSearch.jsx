import { useState } from 'react'
import { contribuinteService } from '../services/api'
import { formatApiError } from '../utils/formatApiError'
import { formatCpfDisplay, formatTelefoneDisplay } from '../utils/masks'

export default function ContribuinteSearch({ onSelect, onCadastrarNovo, selectedId = null }) {
  const [termo, setTermo] = useState('')
  const [resultados, setResultados] = useState([])
  const [semResultados, setSemResultados] = useState(false)
  const [loading, setLoading] = useState(false)
  const [error, setError] = useState('')

  const buscar = async () => {
    if (termo.trim().length < 2) {
      setError('Digite ao menos 2 caracteres para buscar.')
      setSemResultados(false)
      return
    }
    setLoading(true)
    setError('')
    setSemResultados(false)
    try {
      const { data } = await contribuinteService.buscar(termo.trim())
      setResultados(data)
      if (!data.length) {
        setSemResultados(true)
      }
    } catch (err) {
      setError(formatApiError(err, 'Erro ao buscar contribuintes.'))
      setResultados([])
      setSemResultados(false)
    } finally {
      setLoading(false)
    }
  }

  const handleTermoChange = (e) => {
    setTermo(e.target.value)
    setSemResultados(false)
    setResultados([])
    setError('')
  }

  return (
    <div>
      <div className="search-row">
        <input
          type="text"
          placeholder="Nome ou CPF do contribuinte"
          value={termo}
          onChange={handleTermoChange}
          onKeyDown={(e) => e.key === 'Enter' && (e.preventDefault(), buscar())}
        />
        <button type="button" className="btn btn-primary" onClick={buscar} disabled={loading}>
          {loading ? 'Buscando...' : 'Buscar'}
        </button>
      </div>

      {error && <div className="alert alert-error mt-2">{error}</div>}

      {semResultados && (
        <div className="search-empty mt-2">
          <p className="text-muted">Nenhum contribuinte encontrado para &quot;{termo.trim()}&quot;.</p>
          {onCadastrarNovo && (
            <button
              type="button"
              className="btn btn-primary mt-2"
              onClick={() => onCadastrarNovo(termo.trim())}
            >
              Cadastrar novo contribuinte
            </button>
          )}
        </div>
      )}

      {resultados.length > 0 && (
        <div className="search-results">
          {resultados.map((c) => (
            <div
              key={c.id}
              className={`search-result-item ${selectedId === c.id ? 'selected' : ''}`}
            >
              <div className="search-result-linha">
                <span className="search-result-nome">{c.nome_completo}</span>
                <span className="search-result-campo">
                  <span className="search-result-label">CPF</span>
                  {formatCpfDisplay(c.cpf)}
                </span>
                <span className="search-result-campo">
                  <span className="search-result-label">Tel.</span>
                  {formatTelefoneDisplay(c.telefone)}
                </span>
                <span className="search-result-campo search-result-campo--email">
                  <span className="search-result-label">E-mail</span>
                  {c.email?.trim() || '—'}
                </span>
              </div>
              <button type="button" className="btn btn-sm btn-outline" onClick={() => onSelect(c)}>
                Selecionar
              </button>
            </div>
          ))}
        </div>
      )}
    </div>
  )
}
