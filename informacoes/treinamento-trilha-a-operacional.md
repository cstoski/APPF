# Manual de treinamento — Trilha A (Operacional)

**Público:** tesoureiro, secretaria, perfil **OPERADOR** (e MASTER em tarefas do dia a dia).  
**Pré-requisito:** nenhum (primeira trilha).  
**Roteiro de vídeos:** [treinamento.md](./treinamento.md) — módulos 1 a 9.  
**Tempo estimado (vídeos):** ~2 h 05 min · **Prática sugerida:** +2 h.

---

## 1. Visão técnica do sistema

| Item | Detalhe |
|------|---------|
| Nome comercial | **ZELO** |
| Nome interno / manual | **Contribuições APPF (SGCV)** |
| Arquitetura | Navegador → API FastAPI → SQLite local |
| URL (instalado) | `http://127.0.0.1:8765` |
| URL (desenvolvimento) | Frontend `http://127.0.0.1:5173` + API `http://127.0.0.1:8000` |
| Dados | Pasta `data/` ao lado da instalação (banco, logs, assinaturas) |
| Conectividade | Operação **offline** após o serviço local estar em execução; não depende de nuvem |

O executável **ZELO** mantém a API ativa, ícone na **bandeja do sistema** e **instância única** (segundo atalho só reabre o navegador).

---

## Módulo 1 — Primeiro contato (vídeos 1.1–1.3)

### Objetivos de aprendizagem

- Identificar componentes (tray, navegador, API).
- Abrir o sistema e interpretar o indicador de status da API.
- Navegar pelas rotas principais da interface.

### Procedimento — abrir o ZELO (produção)

1. Iniciar pelo atalho **ZELO** ou `ZELO.exe`.
2. Confirmar ícone na bandeja (perto do relógio).
3. Menu da bandeja → **Abrir no navegador** (ou equivalente).
4. Acessar `http://127.0.0.1:8765` — a porta **8765** é fixa no pacote desktop (`tools/run_desktop.py`).

### Indicador de status (navbar)

O componente **ApiServerStatus** consulta periodicamente a API. Estados típicos:

| Estado | Significado | Ação do operador |
|--------|-------------|------------------|
| Online | API respondendo | Uso normal |
| Offline | Serviço parado ou porta bloqueada | Reiniciar ZELO; se persistir, acionar TI/admin |

### Rotas da interface (React Router)

| Menu | Rota | Função |
|------|------|--------|
| Dashboard | `/dashboard` | Indicadores e série mensal |
| Contribuintes | `/contribuintes` | Cadastro, busca, importação embutida |
| Recibos | `/contribuicoes` | Lançamento e gestão de recibos |
| Relatórios | `/relatorios` | Por contribuinte e financeiro |
| Configuração | `/configuracao` | Leitura institucional; operador não edita APPF/SMTP |
| Importação (alternativa) | `/importacao` | Mesmo fluxo de importação em tela dedicada |

Menu **Sobre**: versão do frontend, link do manual (`/manual/index.html`), contato de suporte (`frontend/src/config/sobre.js`).

### Referência técnica

- Status desktop (somente localhost): `GET /api/v1/desktop/status`
- Ping: `GET /ping`

### Exercício

1. Abrir o ZELO e confirmar status **Online**.
2. Percorrer cada item do menu e voltar ao Dashboard.

---

## Módulo 2 — Acesso e perfis (vídeos 2.1–2.2)

### Objetivos

- Realizar login e encerrar sessão com segurança.
- Trocar a própria senha (quando permitido).
- Diferenciar **OPERADOR** e **MASTER**.

### Login

| Campo | Regra |
|-------|--------|
| Usuário | Texto livre, 3–80 caracteres (cadastro admin) |
| Senha | Mínimo 6 caracteres na troca; política definida pelo admin na criação |

**API:** `POST /api/v1/auth/login`  
**Corpo:** `{ "username": "...", "password": "..." }`  
**Resposta:** `{ "access_token": "...", "token_type": "bearer" }`

O frontend armazena o token em **sessionStorage** (`appf_token`, `appf_username`). Ao fechar o navegador, a sessão da aba termina; o token não fica em cookie persistente.

**JWT:** validade **12 horas**; assinatura vinculada ao **HWID** da máquina (token de outro PC não funciona aqui).

### Logout

- UI: botão Sair na navbar → `POST /api/v1/auth/logout` com Bearer token.

### Troca de senha

Disponível em **Configuração → Senha** para usuários que **não** são conta sistema (`admin`, `dev_support_appf`).

**API:** `POST /api/v1/auth/trocar-senha`  
**Corpo:** `{ "senha_atual", "nova_senha" }` — nova senha mín. 6 caracteres e diferente da atual.

### Perfis

| Perfil | Label na UI | Escrita em |
|--------|-------------|------------|
| **OPERADOR** | Operador | Contribuintes, recibos, relatórios; config em leitura |
| **MASTER** | Administrador | Tudo do operador + APPF, SMTP, usuários, ativação de licença |

Rotas **Usuários** (`/usuarios`) e edição de config institucional exigem `MASTER` ou conta de suporte **DEV** (não aparece no CRUD de usuários).

### Licença e escrita (impacto no operador)

| Modo da licença | Leitura | Criar/editar recibos e cadastros |
|-----------------|---------|----------------------------------|
| **ATIVA** | Sim | Sim |
| **GRACE** (7 dias após expirar) | Sim | **Não** — somente consulta |
| **EXPIRADA** / demo expirada | Bloqueio conforme tela | Não |

Mensagens de bloqueio vêm do middleware `require_licenca` / `require_licenca_escrita` no backend.

### Exercício

1. Login com usuário operador de teste.
2. Confirmar que **Usuários** não aparece no menu.
3. Trocar senha e fazer login novamente.

---

## Módulo 3 — Dashboard (vídeo 3.1)

### Objetivos

Interpretar indicadores e a série **contribuições mês a mês**.

### API

`GET /api/v1/dashboard/resumo?mes={1-12}&ano={2000-2100}`  
Padrão: mês e ano correntes.

### Campos principais da resposta

| Campo | Significado técnico |
|-------|---------------------|
| `contribuintes_ativos` / `contribuintes_excluidos` | Contagem com `excluido` false/true |
| `recibos_ativos_total` / `recibos_cancelados_total` | Todos os tempos |
| `recibos_emitidos_mes_ativos` | Recibos **não cancelados** no mês de referência |
| `valor_total_mes_ativos` | Soma dos valores (ativos no mês) |
| `recibos_emitidos_ano_ativos` / `valor_total_ano_ativos` | Ano de referência |
| `valor_dezembro_ano_anterior` | Comparativo explícito com dez. do ano anterior |
| `contribuicoes_mes_a_mes[]` | Por mês: `valor_total`, `quantidade`, `variacao_percentual_mes_anterior` |
| `licenca_ativa` | Licença em modo que permite operação plena |
| `smtp_configurado` | Host, usuário, remetente e senha SMTP preenchidos |
| `razao_social` | Texto da instituição cadastrada |

**Regra de negócio:** totais financeiros do dashboard **excluem recibos cancelados**.

### Uso na rotina

- Início do mês: conferir `valor_total_mes_ativos` vs. expectativa da tesouraria.
- Fim do ano: usar série anual e comparativo de dezembro.
- Se `smtp_configurado: false`, envio de e-mail de recibos falhará até o admin configurar SMTP (trilha B).

### Exercício

Alterar mês/ano no seletor (se disponível na UI) e correlacionar um valor com um recibo conhecido emitido naquele mês.

---

## Módulo 4 — Contribuintes (vídeos 4.1–4.3)

### Objetivos

Cadastrar, editar, buscar, excluir logicamente e reativar contribuintes, respeitando CPF e LGPD.

### Campos do formulário (UI → API)

| Campo UI | API / banco | Obrigatório | Limite / regra |
|----------|-------------|-------------|----------------|
| Nome completo | `nome_completo` | Sim | Máx. 200 caracteres |
| CPF | `cpf` (envio); `cpf_cifrado` + `cpf_busca_hash` (armazenamento) | Não* | 11 dígitos ou vazio; máscara na UI |
| E-mail | `email` → `email_cifrado` | Não | Validado se informado |
| Telefone | `telefone` → `telefone_cifrado` | Não | Mín. 8 dígitos se informado |
| Observações | `observacoes` | Não | Máx. 500 |
| (implícito no create) | `consentimento_lgpd: true` | Sim no POST | Sem consentimento o create é rejeitado |

\* CPF vazio é permitido; recomenda-se preencher para recibos e relatórios consistentes.

### Criptografia (LGPD)

- Algoritmo: **Fernet** com chave derivada de `FERNET_PEPPER + HWID`.
- **Lista** (`GET /contribuintes`): CPF exibido mascarado (`***.XXX.XXX-**`).
- **Detalhe** (`GET /contribuintes/{id}`): CPF/e-mail/telefone em claro — exige licença de **escrita** ativa.

### Regras de CPF

1. Normalização: apenas dígitos.
2. Se informado: exatamente **11 dígitos** válidos como quantidade (validação de dígitos verificadores conforme implementação do backend).
3. **Duplicidade:** entre registros **ativos** (`excluido=false`), o hash do CPF deve ser único → HTTP **400** com mensagem de CPF já cadastrado.
4. **Mesmo nome, CPF diferente:** permitido (famílias, homônimos).

### API — contribuintes

| Método | Rota | Licença |
|--------|------|---------|
| GET | `/api/v1/contribuintes?excluidos=false` | Leitura (GRACE ok) |
| GET | `/api/v1/contribuintes/buscar?termo=` | Busca por nome (ILIKE) ou CPF completo |
| GET | `/api/v1/contribuintes/{id}` | Escrita ativa para PII completo |
| POST | `/api/v1/contribuintes` | Escrita |
| PUT | `/api/v1/contribuintes/{id}` | Escrita; só ativos |
| DELETE | `/api/v1/contribuintes/{id}` | Exclusão lógica (204) |
| POST | `/api/v1/contribuintes/{id}/reativar` | Escrita |

Lista limitada a **5000** registros por requisição.

### Procedimento — cadastro

1. **Contribuintes** → **Novo** (ou atalho na tela Recibos ao buscar inexistente).
2. Preencher nome; CPF com máscara; contatos opcionais.
3. Salvar → POST com `consentimento_lgpd: true`.

### Procedimento — exclusão e reativação

- **Excluir:** marca `excluido=true`; histórico de recibos permanece.
- **Reativar:** disponível na listagem de excluídos (`excluidos=true`).

### Erros comuns

| Mensagem / situação | Causa | Solução |
|---------------------|-------|---------|
| CPF já cadastrado | Ativo com mesmo hash | Localizar o cadastro existente ou corrigir CPF |
| Licença somente leitura | Modo GRACE | Admin deve renovar licença |
| Não foi possível carregar contribuinte | Sem licença escrita no GET detalhe | Normal em GRACE para edição — usar listagem |

### Exercício

1. Cadastrar contribuinte A (CPF fictício válido).
2. Tentar cadastrar B com **mesmo CPF** → confirmar erro.
3. Cadastrar C com **mesmo nome** e CPF diferente → deve permitir.
4. Excluir A e reativar.

---

## Módulo 5 — Importação em lote (vídeos 5.1–5.2)

### Objetivos

Importar planilha Excel/CSV com preview e decisão linha a linha.

### Formatos aceitos

- `.xlsx` (openpyxl)
- `.csv`

### Colunas (cabeçalho case-insensitive)

| Campo canônico | Aliases aceitos |
|----------------|-----------------|
| `nome_completo` | nome, nome_completo, contribuinte, nome do contribuinte |
| `cpf` | cpf, documento, cpf do contribuinte |
| `email` | email, e-mail |
| `telefone` | telefone, celular, fone |

Nome mínimo **3** caracteres na importação.

### Fluxo de API

1. `POST /api/v1/dados/importar/preview-detalhado` — multipart `arquivo`
2. UI exibe status por linha: `NOVO`, `DUP_CPF`, `DUP_ARQUIVO`, `INVALIDO`
3. Operador define ação: `IMPORTAR`, `ATUALIZAR`, `PULAR`
4. `POST /api/v1/dados/importar/aplicar` — `arquivo`, `modo_duplicados` (`PULAR`|`ATUALIZAR`), opcional `decisoes_json`

### Parâmetro global de duplicados

| `modo_duplicados` | Comportamento padrão para linhas `DUP_CPF` sem decisão individual |
|-------------------|-------------------------------------------------------------------|
| `PULAR` | Mantém cadastro existente |
| `ATUALIZAR` | Sobrescreve dados do ativo existente |

### Resposta da aplicação

Contadores típicos: `importados`, `atualizados`, `pulados` — exibidos na UI após concluir.

### Exportação (conferência)

`GET /api/v1/dados/exportar/contribuintes` → arquivo `contribuintes.xlsx` com campos descriptografados (requer permissões adequadas).

### Onde importar na UI

- Painel na página **Contribuintes**
- Rota dedicada `/importacao`

### Exercício

1. Montar planilha com 3 linhas: nova, CPF duplicado de registro existente, nome inválido (1 caractere).
2. Preview → ajustar ações → aplicar.
3. Conferir contadores e listagem.

---

## Módulo 6 — Recibos e contribuições (vídeos 6.1–6.4)

### Objetivos

Emitir recibo numerado, gerar PDF, imprimir, compartilhar e cancelar com rastreio.

### Campos do lançamento

| Campo UI | API `ReciboCreate` | Regra |
|----------|-------------------|--------|
| Contribuinte | `contribuinte_id` | Obrigatório |
| Data | `data_contribuicao` | ISO `YYYY-MM-DD`; **não futura** |
| Valor | `valor` | Numérico **> 0** |
| Forma de pagamento | `forma_pagamento` | UI: Dinheiro, PIX, Cartão, Transferência; máx. 50 chars |
| Descrição | `descricao` | Opcional; máx. 200 |

### Numeração do recibo

Formato: **`YYYYMMDD` + 4 dígitos sequenciais no dia** (ex.: `202605200001`).  
Gerado no servidor com transação SQLite `BEGIN IMMEDIATE` para evitar duplicata.

### Snapshot no recibo

No momento da emissão são gravados na tabela do recibo: dados da instituição (`config_appf`), `texto_legal_recibo`, `usuario_emissor`. Alterações posteriores na config **não alteram** recibos já emitidos.

### API — contribuições

| Método | Rota |
|--------|------|
| GET | `/api/v1/contribricoes?contribuinte_id=` |
| GET | `/api/v1/contribricoes/{recibo_id}` |
| POST | `/api/v1/contribricoes` |
| POST | `/api/v1/contribricoes/{id}/cancelar` |
| POST | `/api/v1/contribricoes/{id}/registrar-acao` |
| POST | `/api/v1/contribricoes/{id}/enviar-email` |

### PDF e impressão (cliente)

- Biblioteca: **pdfMake** (`frontend/src/utils/reciboPdf.js`).
- Assinaturas: URLs `/static/assinaturas/{presidente|tesoureiro}_{uuid}.png|jpg|jpeg`.
- Opção **duplicata na mesma folha:** duas vias no mesmo PDF.
- Ações registradas: `GERAR_PDF`, `IMPRIMIR` via `registrar-acao`.

### E-mail do recibo (servidor)

`POST .../enviar-email` com:

- `destinatario_email`, `assunto`, `corpo_texto`
- `pdf_base64` (deve começar com `%PDF`)
- `nome_anexo`

**Pré-requisitos:** SMTP configurado (trilha B); contribuinte com e-mail; recibo **não cancelado**.  
Log: `data/logs/emails.log` — status `ACEITO_SMTP` = servidor de saída aceitou; **não** garante entrega/leitura.

### WhatsApp (cliente)

Sem API WhatsApp no servidor. Fluxo (`reciboShare.js`):

1. Monta texto com dados do recibo.
2. Abre compartilhamento nativo ou link `wa.me` com telefone normalizado (DDD + 10–11 dígitos).
3. Registra `ENVIAR_WHATSAPP` em `registrar-acao`.

### Cancelamento

| Campo | Regra |
|-------|--------|
| `motivo_cancelamento` | **10 a 500** caracteres |
| Efeito | `cancelado=true`; bloqueio de reimpressão, PDF, e-mail |
| Auditoria | `usuario_cancelador`, `data_cancelamento`; log em `data/logs/recibos.log` |

### Exercício

1. Emitir recibo de R$ 50,00 PIX para contribuinte com e-mail de teste.
2. Gerar PDF e registrar impressão.
3. (Se SMTP ok) enviar e-mail.
4. Cancelar com motivo de 10+ caracteres e tentar reenviar — deve falhar.

---

## Módulo 7 — Relatórios (vídeos 7.1–7.2)

### Objetivos

Gerar relatório por contribuinte e financeiro da APPF; exportar PDF/Excel no navegador.

### Tipos e API

**Por contribuinte**  
`GET /api/v1/relatorios/contribuinte?contribuinte_id=&data_inicio=&data_fim=&incluir_cancelados=false`

**Financeiro**  
`GET /api/v1/relatorios/financeiro?periodo=mensal|semestral|anual&ano=&mes=&semestre=1|2&incluir_cancelados=false`

### Estrutura da resposta (ambos)

- `titulo`, `periodo_label`, `data_inicio`, `data_fim`
- `instituicao` (razão social, CNPJ)
- `linhas[]`: data, valor, forma, descrição, flags de cancelamento
- `resumo`: `quantidade`, `valor_total`, `valor_medio`, `quantidade_cancelados`
- Financeiro **anual:** `totais_mensais[]` com `mes`, `mes_label`, `quantidade`, `valor_total`

**Regra:** totais do `resumo` **excluem cancelados** do valor total; cancelados podem aparecer nas linhas se `incluir_cancelados=true`.

### Exportação

| Formato | Implementação |
|---------|---------------|
| PDF | `relatorioPdf.js` — `imprimirRelatorioPdf`; gráfico no anual |
| Excel | `relatorioExcel.js` — `exportarRelatorioExcel` |

Processamento **no navegador** — não há arquivo temporário no servidor.

### Envio de histórico por e-mail

`POST /api/v1/relatorios/contribuinte/enviar-email` — corpo HTML com tabela; requer SMTP.

### Exercício

1. Relatório por contribuinte: ano corrente, PDF + Excel.
2. Relatório financeiro **anual** com gráfico no PDF.
3. Comparar `valor_total` do relatório com dashboard do mesmo período.

---

## Módulo 8 — Configuração em leitura (vídeo 8.1)

### Objetivos

Saber quais dados institucionais entram no recibo e o que o operador **não** pode alterar.

### API (leitura)

`GET /api/v1/appf` — disponível com licença em modo leitura (GRACE).

### Campos visíveis (impacto no recibo/PDF)

| Campo | Uso |
|-------|-----|
| `razao_social`, `cnpj`, `endereco` | Cabeçalho institucional |
| `nome_presidente`, `nome_tesoureiro` | Texto e bloco de assinaturas |
| `caminho_assinatura_presidente`, `caminho_assinatura_tesoureiro` | Imagens via `/static/assinaturas/...` |
| `texto_legal_recibo` | Corpo legal/padrão do PDF |
| SMTP | Remetente de e-mails — operador não edita |

Operador com perfil **OPERADOR** vê abas sem formulário de gravação institucional; alterações são feitas pelo **MASTER** (trilha B).

---

## Módulo 9 — Boas práticas e suporte (vídeos 9.1–9.2)

### Rotina recomendada

1. Conferir contribuinte e valor **antes** de **Gerar contribuição**.
2. Usar descrição objetiva (ex.: "Mensalidade mar/2026").
3. Não compartilhar usuário/senha; cada tesoureiro com login próprio.
4. Consultar manual: menu **Sobre** → Manual ou `/manual/index.html`.

### Diagnóstico rápido

| Sintoma | Verificação técnica |
|---------|---------------------|
| API offline | Tray ativo? Porta 8765? `GET /ping` |
| Erro 401 | Token expirado (12 h) — novo login |
| Erro licença escrita | `GET /api/v1/licenca` → `modo` |
| E-mail não envia | `smtp_configurado` no dashboard; `emails.log` |
| PDF sem assinatura | Arquivos em `data/assinaturas/`; paths na config |

### Logs (para informar ao admin/suporte)

Pasta: `{instalação}/data/logs/`

| Arquivo | Conteúdo |
|---------|----------|
| `acesso.log` | Login, logout, usuários |
| `recibos.log` | Emissão, cancelamento, PDF, WhatsApp |
| `emails.log` | Envios SMTP |
| `licencas.log` | Ativação e falhas de licença |
| `zelo.log` | Erros gerais da aplicação |

### Abertura de chamado

Informar: versão (menu Sobre), modo da licença, print da mensagem, horário, usuário logado (sem senha), trecho relevante do log.

**Suporte padrão:** `suporte@appf.org.br` · `(41) 99862-2287` — ver `sobre.js`.

---

## Avaliação final da trilha A

| Critério | Esperado |
|----------|----------|
| Cadastro | 3 contribuintes sem erro de CPF duplicado |
| Recibo | 2 recibos com formas diferentes; 1 PDF gerado |
| Cancelamento | 1 recibo cancelado com motivo válido |
| Relatório | 1 PDF por contribuinte + 1 financeiro mensal |
| Importação | Planilha 5+ linhas com preview aplicado |

---

## Referências cruzadas

- Índice de vídeos: [treinamento.md](./treinamento.md)
- Manual do usuário: [frontend/public/manual/index.html](../frontend/public/manual/index.html)
- Trilha seguinte (admin): [treinamento-trilha-b-administrador.md](./treinamento-trilha-b-administrador.md)

*Atualizado: maio/2026.*
