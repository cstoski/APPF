# Manual de treinamento — Trilha B (Administrador / MASTER)

**Público:** gestor da APPF, TI escolar com perfil **MASTER**.  
**Pré-requisito:** trilha A concluída (ou experiência equivalente no ZELO).  
**Roteiro de vídeos:** [treinamento.md](./treinamento.md) — módulos 10 a 14.  
**Tempo estimado (vídeos):** ~1 h 37 min · **Prática sugerida:** +1 h.

---

## 1. Escopo do perfil MASTER

| Capacidade | OPERADOR | MASTER |
|------------|----------|--------|
| Dashboard, contribuintes, recibos, relatórios | Sim | Sim |
| Editar config APPF, SMTP, assinaturas | Não | Sim |
| Gerenciar usuários (`/usuarios`) | Não | Sim |
| Ativar licença (`POST /licenca/ativar`) | Não | **Sim** |
| Conta sistema `admin` | — | Existe no 1º banco; não editável pelo CRUD |

Conta **DEV** (`dev_support_appf`) tem poderes de admin para suporte do fornecedor; não é criada pela UI de usuários.

**API:** rotas sensíveis usam `require_roles("MASTER", "DEV")` em `app/routers/appf.py`, `usuarios.py`; ativação de licença exige **MASTER** estrito.

---

## Módulo 10 — Configuração da APPF (vídeos 10.1–10.3)

### Objetivos

Configurar identidade institucional, assinaturas e texto legal dos recibos.

### Acesso na UI

**Configuração** → aba **APPF** (apenas `isAdmin`).

### API

| Método | Rota | Corpo |
|--------|------|-------|
| GET | `/api/v1/appf` | — leitura autenticada |
| POST | `/api/v1/appf` | `multipart/form-data` |
| POST | `/api/v1/appf/validar?escopo=appf\|email\|tudo` | Valida campos obrigatórios |

### Campos do formulário institucional

| Campo | Obrigatório para recibo válido | Observação |
|-------|-------------------------------|------------|
| `razao_social` | Sim | Aparece em PDF, relatórios, e-mail |
| `cnpj` | Sim | Formato validado no backend |
| `endereco` | Sim | Texto livre |
| `nome_presidente` | Sim | Bloco de assinatura |
| `nome_tesoureiro` | Sim | Bloco de assinatura |
| `texto_legal_recibo` | Recomendado | Texto padrão no PDF; gravado no snapshot do recibo na emissão |
| `assinatura_presidente` | Arquivo opcional no POST | PNG/JPG/JPEG |
| `assinatura_tesoureiro` | Arquivo opcional no POST | PNG/JPG/JPEG |

### Armazenamento de assinaturas

| Ambiente | Caminho físico |
|----------|----------------|
| Instalação ZELO | `{pasta_instalacao}/data/assinaturas/` |
| Desenvolvimento | `app/data/assinaturas/` |

**URL pública:** `/static/assinaturas/presidente_{uuid}.png` (ou `tesoureiro_...`).  
Arquivos **não** ficam dentro do executável — permitem troca sem rebuild.

**Procedimento de upload:**

1. Selecionar imagem (fundo claro, proporção horizontal ~3:1).
2. Salvar config → servidor grava arquivo com UUID no nome.
3. Preview na UI (`AssinaturaMiniPreview`) e no PDF do recibo.

### Validação `escopo=appf`

Verifica presença de razão social, CNPJ, endereço, nomes e consistência mínima antes de operação em produção.

### Impacto em recibos já emitidos

Alterar config **não altera** recibos antigos — cada recibo guarda cópia dos dados institucionais no momento da emissão.

### Exercício

1. Preencher todos os campos institucionais.
2. Enviar duas assinaturas de teste.
3. Emitir recibo e confirmar assinaturas no PDF.
4. Alterar `texto_legal_recibo` e emitir novo recibo — textos diferentes nos dois PDFs.

---

## Módulo 11 — E-mail SMTP (vídeos 11.1–11.2)

### Objetivos

Configurar servidor de saída, testar conexão e interpretar falhas de envio.

### Campos SMTP (form + banco)

| Campo UI | Banco | Padrão dev |
|----------|-------|------------|
| `smtp_host` | `smtp_host` | `localhost` |
| `smtp_porta` | `smtp_porta` | `587` |
| `smtp_usuario` | `smtp_usuario` | — |
| `smtp_senha` | `smtp_senha_cifrada` (Fernet) | — |
| `smtp_usar_starttls` | boolean | `true` |
| `smtp_remetente` | `smtp_remetente` | — |

**“SMTP configurado”** (dashboard): host + usuário + remetente + senha cifrada presentes.

### Portas e TLS (referência técnica)

| Cenário | Porta | STARTTLS |
|---------|-------|----------|
| Gmail / Office 365 | 587 | Ligado |
| SSL direto | 465 | Desligado (SSL na conexão) |
| Relay interno | 25 | Desligado; usuário/senha vazios se relay aberto |

Detalhes por provedor: [manual do usuário](../frontend/public/manual/index.html) e `frontend/src/config/smtpAjuda.js`.

### API de validação

`POST /api/v1/appf/validar?escopo=email` — testa conexão SMTP real (`config_validacao_service.py`).

Na UI: **Salvar e testar SMTP** ou **Testar conexão SMTP** (aba **E-mail**).

### Envio de recibos e relatórios

| Fluxo | Endpoint | Anexo |
|-------|----------|-------|
| Recibo PDF | `POST /contribricoes/{id}/enviar-email` | PDF base64 |
| Histórico contribuinte | `POST /relatorios/contribuinte/enviar-email` | HTML no corpo |

### Log `emails.log`

Campos úteis: destinatário, assunto, status (`ACEITO_SMTP`, falha SMTP).  
**Não há rastreamento de leitura** com SMTP simples — valores `nao_rastreado` são esperados.

### Erros comuns

| Erro | Causa provável | Ação |
|------|---------------|------|
| Autenticação falhou | Senha normal em vez de senha de app (Gmail) | Gerar senha de aplicativo |
| Connection refused | Host/porta errados ou firewall | Conferir painel do provedor |
| Remetente rejeitado | `smtp_remetente` ≠ conta autorizada | Alinhar remetente ao usuário SMTP |
| STARTTLS | Porta 465 com STARTTLS ligado | Ajustar conforme tabela |

### Exercício

1. Configurar SMTP de teste (caixa institucional).
2. Validar com `escopo=email`.
3. Enviar recibo de teste para e-mail próprio.
4. Abrir `data/logs/emails.log` e localizar linha `ACEITO_SMTP`.

---

## Módulo 12 — Usuários e auditoria (vídeos 12.1–12.2)

### Objetivos

Criar operadores e administradores; desativar acessos; usar logs para auditoria.

### UI

Rota `/usuarios` — visível apenas com `adminOnly` na navbar (`isAdmin`).

### API (`/api/v1/usuarios`) — MASTER/DEV

| Método | Rota | Descrição |
|--------|------|-----------|
| GET | `` | Lista usuários (exceto `admin`) |
| POST | `` | Cria usuário |
| PUT | `/{user_id}` | Atualiza username, senha, perfil, ativo |
| POST | `/{user_id}/desativar` | `ativo=false` |

### Campos de criação

| Campo | Regra |
|-------|--------|
| `username` | 3–80 caracteres; **não** pode ser `admin` |
| `password` | Mínimo 6 caracteres |
| `perfil` | Apenas `OPERADOR` ou `MASTER` |
| `ativo` | Default true |

### Procedimento — novo tesoureiro

1. **Usuários** → Novo.
2. Perfil **Operador**.
3. Senha inicial forte; orientar troca na primeira sessão (**Configuração → Senha**).
4. Nunca reutilizar senha do usuário `admin` de fábrica em produção.

### Usuário `admin` (seed)

Criado apenas quando o banco está vazio (`database.py`):  
`admin` / senha inicial documentada internamente — **alterar imediatamente** após implantação.  
Não aparece na listagem nem pode ser editado via API de usuários.

### Logs de auditoria

Pasta: `{instalação}/data/logs/`

| Arquivo | Eventos típicos | Uso na auditoria |
|---------|-----------------|------------------|
| `acesso.log` | login, logout, CRUD usuário | Quem acessou e quando |
| `recibos.log` | emitir, cancelar, PDF, WhatsApp | Rastreio de recibo número X |
| `emails.log` | envio, teste SMTP | Prova de tentativa de envio |
| `licencas.log` | ativar, expirar, demo | Vínculo máquina ↔ serial |
| `zelo.log` | exceções, migração DB | Erros técnicos pós-atualização |

Formato: texto linha a linha com timestamp (abrir com Notepad ou editor).

### Sessões simultâneas

`GET /api/v1/desktop/status` (localhost) lista usuários com atividade nos últimos **5 minutos** (`sessao_ativa_service.py`) — útil para saber quem está na secretaria.

### Exercício

1. Criar usuário `tesoureira1` OPERADOR.
2. Desativar usuário de teste antigo.
3. Simular login da tesoureira e confirmar ausência do menu Usuários.
4. Localizar login em `acesso.log`.

---

## Módulo 13 — Licenciamento (vídeos 13.1–13.2)

### Objetivos

Ativar licença comercial, entender demo, expiração e período de cortesia.

### API

| Método | Rota | Quem |
|--------|------|------|
| GET | `/api/v1/licenca` | Autenticado — status completo |
| POST | `/api/v1/licenca/ativar` | **MASTER** — body `{ "serial": "..." }` |

### HWID (Hardware ID)

Identificador único da máquina, exibido na aba **Licença** em Configuração.

**Geração (`licenca_service.py`):**

- Windows: UUID do produto (`Win32_ComputerSystemProduct`) via WMI/PowerShell.
- Fallback: hash de variáveis de ambiente.

O serial de produção é **criptograficamente ligado** ao HWID — não funciona em outro PC.

### Tipos de serial

| Tipo | Formato | Validade | Restrição |
|------|---------|----------|-----------|
| **Produção** | `XXXX-XXXX-XXXX-XXXX` (16 alfanum.) | **365 dias** a partir da data embutida no serial | Uma ativação por HWID na tabela `licencas_ativadas` |
| **Demonstração** | `DEMO-APPF-DEMO-3DAY` | **3 dias** | **Uma vez por equipamento** (`demo_consumido`); após expirar o serial demo **não pode** ser reativado |
| Revogados | `PROAPPF2026`, `APPF2026SGCVLOCL` | — | Rejeitados |

### Modos de operação (`modo`)

| Modo | Leitura | Escrita (cadastros, recibos) |
|------|---------|------------------------------|
| `ATIVA` | Sim | Sim |
| `GRACE` | Sim | **Não** — 7 dias após expiração da licença comercial |
| `EXPIRADA` | Bloqueio conforme UI | Não |
| `DEMO_EXPIRADA` | Bloqueio | Não |
| `NAO_ATIVADA` | Parcial | Não |
| `INTEGRIDADE_FALHA` | — | Contatar suporte |

Aviso na UI quando faltam **≤ 30 dias** para expirar (licença comercial).

### Geração de serial (fornecedor — referência)

```bat
cd tools
python gerar_licenca.py --hwid <HWID_COPIADO_DA_TELA>
```

Requer `APPF_LICENSE_SECRET` idêntico no servidor do cliente:

- Variável de ambiente, ou
- Arquivo `license_secret.local` na raiz da instalação.

Modelo: `tools/license_secret.example.env`.

### Procedimento — ativação no cliente

1. Login como **MASTER**.
2. **Configuração** → **Licença**.
3. Copiar **HWID** e enviar ao fornecedor (se ainda não tiver serial).
4. Colar serial → **Ativar**.
5. Confirmar modo **ATIVA** e data de validade.

### Exercício (ambiente de teste)

1. Consultar status atual via UI.
2. (Somente lab) testar serial demo em VM descartável — confirmar bloqueio após 3 dias.
3. Ler última linha de `licencas.log`.

---

## Módulo 14 — Backup e continuidade (vídeos 14.1–14.2)

### Objetivos

Proteger dados locais e abrir chamados eficientes ao suporte.

### O que fazer backup

| Item | Caminho típico | Conteúdo crítico |
|------|----------------|------------------|
| Banco SQLite | `data/appf_local.sqlite3` | Contribuintes, recibos, usuários, licença, config |
| Assinaturas | `data/assinaturas/*` | PNG/JPG das assinaturas |
| Logs | `data/logs/*` | Auditoria (opcional mas recomendado) |
| Segredo de licença | `license_secret.local` (raiz instalação) | Necessário para validar seriais futuros |

**Não** copiar apenas o `.exe` — os dados estão em `data/`.

### Frequência sugerida

| Cenário | Frequência |
|---------|------------|
| Operação diária intensa | Backup semanal automático (script/cópia agendada) |
| Antes de atualizar ZELO | Backup imediato manual |
| Após importação grande | Backup no mesmo dia |

### Procedimento de backup manual

1. Fechar ZELO pela bandeja (opcional mas evita arquivo SQLite bloqueado).
2. Copiar pasta `data/` inteira para mídia externa ou nuvem institucional.
3. Nomear pasta com data: `backup-ZELO-2026-05-20`.

### Restauração (emergência)

1. Instalar ZELO na mesma ou nova máquina.
2. Parar o serviço.
3. Substituir `data/` pela cópia de backup.
4. **Licença:** HWID mudou se trocou de PC — necessário novo serial para o novo HWID.
5. Iniciar e validar login + contagem de contribuintes.

### Atualização de versão (resumo para admin)

Ver [atualizacao-software.md](./atualizacao-software.md):

- Instalador **não apaga** `data/` por padrão.
- Mesma pasta de instalação (ex.: `C:\ZELO`).
- Fechar ZELO pela bandeja antes de `ZELO-Setup.exe`.

### Chamado de suporte — checklist de informações

Incluir sempre:

1. Versão exibida em **Sobre** (frontend + backend se visível).
2. Modo da licença e dias restantes.
3. HWID (se problema de licença).
4. Print ou texto exato do erro na UI.
5. Trecho de `zelo.log` ou `recibos.log` com timestamp.
6. Passos para reproduzir.

**Contato:** `suporte@appf.org.br` · `(41) 99862-2287` · Seg–Sex 8h–18h.

---

## Avaliação final da trilha B

| Critério | Esperado |
|----------|----------|
| Config APPF | Instituição completa + 2 assinaturas |
| SMTP | Teste de conexão OK + 1 e-mail de recibo |
| Usuários | 1 OPERADOR criado; senha do `admin` alterada |
| Licença | Status ATIVA documentado (print) |
| Backup | Cópia da pasta `data/` em local externo |

---

## Referências cruzadas

- Trilha operacional: [treinamento-trilha-a-operacional.md](./treinamento-trilha-a-operacional.md)
- Implantação/TI: [treinamento-trilha-c-implantacao.md](./treinamento-trilha-c-implantacao.md)
- Checklist release: [checklist-release.md](./checklist-release.md)
- Build: [BUILD.md](./BUILD.md)

*Atualizado: maio/2026.*
