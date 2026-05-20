import packageJson from '../../package.json'

export const APP_NOME = 'Contribuições APPF'
export const APP_PRODUTO = 'SGCV'
export const APP_VERSAO_FRONTEND = packageJson.version

export const MANUAL_URL = '/manual/index.html'

export const SUPORTE = {
  email: 'suporte@appf.org.br',
  telefone: '(41) 99862-2287',
  horario: 'Segunda a sexta, das 8h às 18h',
  observacao: 'Informe o número da versão e descreva o problema com o máximo de detalhes possível.',
}

export const TERMOS_DE_USO = `TERMOS DE USO DO SOFTWARE

1. Objeto
Este Termo regula o uso do sistema ${APP_NOME} (${APP_PRODUTO}), destinado ao registro de contribuições, emissão de recibos e gestão de informações da APPF em ambiente local/offline.

2. Licença de uso
O software é licenciado para uso pela instituição contratante, vinculado ao equipamento autorizado (HWID), conforme política de licenciamento do fornecedor. É vedada a cópia, redistribuição ou engenharia reversa sem autorização expressa.

3. Responsabilidades do usuário
O usuário deve manter credenciais de acesso em sigilo, registrar informações verdadeiras, realizar backups periódicos dos dados locais e utilizar o sistema em conformidade com a legislação aplicável, inclusive a LGPD quanto ao tratamento de dados pessoais de contribuintes.

4. Dados pessoais
Dados sensíveis (CPF, e-mail, telefone) são armazenados com medidas de proteção previstas no sistema. O operador é responsável pelo uso adequado das exportações, impressões e envios de recibos gerados pelo software.

5. Disponibilidade e suporte
Por operar em modo local, a disponibilidade depende da infraestrutura da instituição. Atualizações, correções e suporte técnico seguem o contrato ou acordo de prestação de serviços com o fornecedor.

6. Limitação de responsabilidade
O fornecedor não se responsabiliza por perdas decorrentes de uso indevido, falha de backup, indisponibilidade de rede local ou decisões operacionais tomadas com base em relatórios gerados sem conferência adequada.

7. Alterações
Estes termos podem ser atualizados em novas versões do software. O uso continuado após a atualização implica concordância com a versão vigente.

Última atualização: maio de 2026.`
