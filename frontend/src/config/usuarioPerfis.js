export const PERFIS_CADASTRO = [
  {
    value: 'OPERADOR',
    label: 'Operador',
    descricao:
      'Acesso operacional: dashboard, contribuintes, recibos, relatórios e consulta da configuração da instituição. Não altera usuários nem dados da APPF.',
  },
  {
    value: 'MASTER',
    label: 'Administrador',
    descricao:
      'Tudo do operador, mais gestão de usuários e edição da configuração institucional (APPF, SMTP e assinaturas).',
  },
]

export function labelPerfil(perfil) {
  return PERFIS_CADASTRO.find((p) => p.value === perfil)?.label || perfil
}

export function descricaoPerfil(perfil) {
  return PERFIS_CADASTRO.find((p) => p.value === perfil)?.descricao || ''
}
