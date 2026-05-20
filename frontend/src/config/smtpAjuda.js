export const SMTP_AJUDA_CAMPOS = {
  host: {
    titulo: 'Host SMTP',
    oQueE:
      'Endereço do servidor de envio de e-mails (SMTP). É o computador do seu provedor que recebe as mensagens que o sistema envia.',
    ondeEncontrar:
      'No painel do provedor de e-mail ou hospedagem, procure por “SMTP”, “Servidor de saída”, “Outgoing server” ou “Servidor de e-mail”. Exemplos: smtp.gmail.com, smtp.office365.com, smtp.seudominio.com.br.',
    dicas: ['Copie exatamente como o provedor informa, sem http:// e sem barra no final.'],
  },
  porta: {
    titulo: 'Porta',
    oQueE:
      'Número da porta de conexão com o servidor SMTP. Define como o sistema “conversa” com o servidor de e-mail.',
    ondeEncontrar:
      'Na mesma tela do SMTP do provedor, ao lado do host. Com STARTTLS costuma ser 587; com SSL direto 465; em servidores antigos pode aparecer 25.',
    dicas: [
      'Porta 587 + STARTTLS é o mais comum hoje.',
      'Use a porta indicada pelo provedor — porta errada impede o envio.',
    ],
  },
  usuario: {
    titulo: 'Usuário SMTP',
    oQueE:
      'Login usado para autenticar no servidor. Pode ser o e-mail completo ou um usuário específico de SMTP.',
    ondeEncontrar:
      'Em “Autenticação SMTP”, “Usuário”, “Login” ou “Account name”. Muitos provedores usam o mesmo e-mail que você usa para entrar na caixa de correio.',
    dicas: [
      'Alguns servidores permitem envio sem usuário; nesse caso deixe em branco.',
      'Gmail e Microsoft costumam exigir o e-mail completo como usuário.',
    ],
  },
  senha: {
    titulo: 'Senha SMTP',
    oQueE:
      'Senha de autenticação do SMTP. Pode ser a senha da caixa de correio ou uma senha de aplicativo gerada pelo provedor.',
    ondeEncontrar:
      'No painel de segurança do e-mail: “Senha de app”, “App password”, “SMTP password” ou a senha da conta. Gmail e Outlook frequentemente exigem senha de aplicativo (não a senha normal de login).',
    dicas: [
      'A senha fica cifrada no sistema; deixe em branco ao salvar para manter a atual.',
      'Se o envio falhar após trocar a senha do e-mail, gere uma nova senha SMTP no provedor.',
    ],
  },
  remetente: {
    titulo: 'E-mail remetente',
    oQueE:
      'Endereço que aparecerá como remetente nos recibos e relatórios enviados pelo sistema.',
    ondeEncontrar:
      'Use um e-mail autorizado pelo servidor SMTP — em geral a mesma conta configurada em Usuário, ou um alias permitido pelo provedor (ex.: noreply@seudominio.com).',
    dicas: [
      'Deve ser um endereço válido; o provedor pode rejeitar se não for da mesma conta/domínio.',
      'Evite endereços genéricos bloqueados pelo provedor sem configuração prévia.',
    ],
  },
  starttls: {
    titulo: 'Usar STARTTLS',
    oQueE:
      'Ativa criptografia na conexão com o servidor (TLS). Protege usuário, senha e conteúdo durante o envio.',
    ondeEncontrar:
      'No painel do provedor, procure “STARTTLS”, “TLS”, “Criptografia” ou “Segurança da conexão”. Se a porta recomendada for 587, marque STARTTLS como ativo.',
    dicas: [
      'Mantenha marcado quando o provedor usar porta 587.',
      'Desmarque apenas se o suporte do provedor indicar conexão sem TLS (pouco comum).',
    ],
  },
}

export const SMTP_AJUDA_INTRO =
  'Configure com os dados de envio (SMTP) do seu provedor de e-mail ou da TI. Clique em ? ao lado de cada campo para ver o que é e onde encontrar no servidor.'
