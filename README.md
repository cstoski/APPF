# ZELO — Sistema de Contribuições APPF

Aplicação desktop para **Windows** voltada à gestão de contribuintes, emissão de recibos, relatórios e configuração da **APPF** (Associação de Pais e Professores / instituição configurável). O sistema roda **localmente** no computador do cliente: API em Python, interface web em React e banco SQLite, sem depender de nuvem para o dia a dia.

---

## Visão geral

| Aspecto | Descrição |
|---------|-----------|
| **Nome comercial** | ZELO |
| **Uso principal** | Cadastro de contribuintes, registro de contribuições, recibos em PDF, relatórios e importação em lote |
| **Implantação** | Instalador `ZELO-Setup.exe` ou pasta `dist\ZELO\` (PyInstaller) |
| **Acesso** | Navegador em `http://127.0.0.1:8765` (executável) ou desenvolvimento em `http://127.0.0.1:8000` + Vite |
| **Dados** | Pasta `data/` ao lado do programa (banco, logs, assinaturas enviadas pelo cadastro) |
| **Licenciamento** | Ativação por serial vinculada ao HWID da máquina |

---

## Funcionalidades

### Contribuintes

- Cadastro, edição, exclusão lógica e reativação
- CPF, e-mail e telefone armazenados com **cifragem** (LGPD)
- **Mesmo nome com CPF diferente** é permitido; **CPF duplicado** entre ativos é bloqueado
- Busca por nome ou CPF
- Importação e exportação via planilha Excel

### Contribuições e recibos

- Lançamento de contribuições com data, valor e forma de pagamento
- Geração de **recibo em PDF** (pdfMake), impressão e opção de duplicar na mesma folha
- Envio por e-mail (SMTP configurável)
- Cancelamento de recibos (impede reimpressão/envio após cancelado)
- Texto do recibo configurável pela instituição

### Relatórios

- Relatório **por contribuinte** e **financeiro** (mensal, anual, intervalo)
- Exportação **PDF** e **Excel**
- Relatório anual financeiro com resumo mensal e gráfico no PDF

### Dashboard

- Indicadores e totais (incluindo visão anual otimizada no backend)

### Configuração APPF

- Razão social, CNPJ, endereço, nomes de presidente e tesoureiro
- Upload de **assinaturas** (armazenadas em `data/assinaturas/`, fora do executável)
- Configuração de SMTP para envio de e-mails

### Usuários e segurança

- Login com JWT
- Perfis (administração de usuários)
- Logs de operações (contribuintes, recibos, licença, e-mail, acesso)
- Licença comercial ou modo demonstração

### Desktop (Windows)

- Executável **sem console**, com ícone na **bandeja do sistema**
- Menu: abrir navegador, status (API, banco, licença, usuários conectados), encerrar
- **Instância única**: novo atalho só reabre o browser se o ZELO já estiver rodando

---

## Arquitetura

```text
┌─────────────────────────────────────────────────────────────┐
│  Navegador (Chrome / Edge) — interface React (SPA)          │
└───────────────────────────┬─────────────────────────────────┘
                            │ HTTP / API REST
┌───────────────────────────▼─────────────────────────────────┐
│  FastAPI (app/) — autenticação, regras, PDF, importação    │
└───────────────────────────┬─────────────────────────────────┘
                            │
┌───────────────────────────▼─────────────────────────────────┐
│  SQLite (data/appf_local.sqlite3) + arquivos em data/       │
└─────────────────────────────────────────────────────────────┘
```

### Stack tecnológica

| Camada | Tecnologia |
|--------|------------|
| Backend | Python 3.11+, FastAPI, SQLAlchemy, Uvicorn |
| Frontend | React 18, Vite, React Router, Axios |
| PDF | pdfMake (recibos e relatórios) |
| Planilhas | pandas, openpyxl, xlsx (frontend) |
| Desktop | PyInstaller, pystray, Inno Setup 6 |
| Segurança | JWT, bcrypt, Fernet (dados sensíveis) |

---

## Estrutura do repositório

```text
APPF-cursor/
├── app/                    # Backend FastAPI
│   ├── config/             # Banco, migrações SQLite
│   ├── models/             # SQLAlchemy (contribuintes, recibos, usuários, licença)
│   ├── routers/            # Endpoints REST
│   ├── services/           # Regras de negócio, PDF, e-mail, licença, logs
│   ├── data/               # Banco e dados locais em desenvolvimento (gitignored)
│   └── main.py             # Aplicação FastAPI + SPA
├── frontend/               # Interface React
│   ├── public/images/      # Logos da interface
│   └── src/                # Páginas e componentes
├── tools/                  # Scripts utilitários
│   ├── run_desktop.py      # Inicia API + bandeja (dev e referência do .exe)
│   ├── criar_admin.py      # Cria usuário administrador inicial
│   ├── gerar_licenca.py    # Gera serial de licença
│   └── gerar_icone.bat     # Gera ícone .ico para o executável
├── informacoes/            # Documentação operacional (releases, atualizações)
├── build/                  # Scripts PyInstaller / Inno Setup (gerado/local)
├── dist/                   # Saída do build (gitignored)
└── requirements.txt        # Dependências Python
```

---

## Requisitos

### Desenvolvimento

- **Python 3.11+**
- **Node.js 18+**
- Windows (recomendado para bandeja e instalador; API pode ser testada em outros SO com limitações no desktop)

### Produção (cliente)

- Windows 10/11
- Instalação via `ZELO-Setup.exe` (ver [informacoes/BUILD.md](informacoes/BUILD.md))

---

## Instalação para desenvolvimento

### 1. Backend

```bat
python -m venv .venv
.venv\Scripts\activate
pip install -r requirements.txt
```

Para gerar o `ZELO.exe` / instalador, instale também as dependências de build:

```bat
pip install -r requirements-build.txt
```

### 2. Frontend

```bat
cd frontend
npm install
```

### 3. Chave de licença (desenvolvimento)

Copie o exemplo e ajuste a chave local (não versionada):

```bat
copy tools\license_secret.example.env tools\license_secret.local
```

Ou defina a variável de ambiente `APPF_LICENSE_SECRET`.

### 4. Usuário administrador inicial

```bat
python tools\criar_admin.py
```

Credenciais de teste e chave demo: arquivo **`CREDENCIAIS.local.md`** na raiz (crie localmente; não vai para o Git).

---

## Executar em desenvolvimento

### Opção A — API + Vite (hot reload no frontend)

Terminal 1 — API na porta **8000**:

```bat
python -m uvicorn app.main:app --host 127.0.0.1 --port 8000 --reload
```

Terminal 2 — Frontend na porta **5173**:

```bat
cd frontend
npm run dev
```

Abra: **http://127.0.0.1:5173**

### Opção B — Modo desktop (igual ao executável, porta **8765**)

Build do frontend e servidor integrado:

```bat
cd frontend
npm run build
cd ..
python tools\run_desktop.py
```

Abre automaticamente: **http://127.0.0.1:8765**

Bandeja do sistema (Windows):

```bat
python tools\run_desktop.py --tray
```

### Opção C — Scripts em `tools/`

| Script | Uso |
|--------|-----|
| `tools\iniciar_sistema.bat` | API em `127.0.0.1:8000` |
| `tools\iniciar_rede.bat` | API + Vite na rede local (acesso pelo celular na mesma Wi-Fi) |

---

## Build e distribuição

Documentação completa: **[informacoes/BUILD.md](informacoes/BUILD.md)**

| Comando | Resultado |
|---------|-----------|
| `build\build_installer.bat` | `dist\ZELO-Setup.exe` (recomendado) |
| `build\build_exe.bat` | Pasta `dist\ZELO\` |

**Atualizações para clientes** (releases manuais, preservando `data/`):

- [informacoes/atualizacao-software.md](informacoes/atualizacao-software.md)
- [informacoes/checklist-release.md](informacoes/checklist-release.md)

---

## Dados locais e backup

| Caminho (instalado) | Conteúdo |
|---------------------|----------|
| `{pasta}\data\appf_local.sqlite3` | Banco SQLite |
| `{pasta}\data\assinaturas\` | Imagens de assinatura (upload) |
| `{pasta}\data\logs\zelo.log` | Log do servidor |

Em desenvolvimento, o equivalente fica em **`app/data/`**.

**Backup:** copie a pasta `data` antes de atualizar ou desinstalar.

---

## API

- Documentação interativa (com servidor rodando): `http://127.0.0.1:8000/docs` ou `:8765/docs`
- Health check: `GET /ping`
- Autenticação: `POST /api/v1/auth/token` (form OAuth2 password)

Principais grupos de rotas: `/api/v1/contribuintes`, contribuições/recibos, `/api/v1/dados` (importação), `/api/v1/relatorios`, `/api/v1/dashboard`, `/api/v1/sistema`, `/api/v1/desktop`.

---

## Licenciamento

- Serial assinado vinculado ao **HWID** da máquina
- Geração de serial (fornecedor): `tools\gerar_licenca.bat` / `python tools\gerar_licenca.py`
- Modo demonstração configurável na aplicação

---

## Privacidade (LGPD)

- CPF, e-mail e telefone de contribuintes armazenados **cifrados**
- Busca por CPF usa hash (`cpf_busca_hash`), sem descriptografar toda a base
- Consentimento LGPD no cadastro de contribuintes
- Logs de operações para auditoria interna

---

## Documentação adicional

| Documento | Assunto |
|-----------|---------|
| [informacoes/README.md](informacoes/README.md) | Índice da pasta de informações |
| [informacoes/BUILD.md](informacoes/BUILD.md) | Executável, instalador, bandeja |
| [informacoes/atualizacao-software.md](informacoes/atualizacao-software.md) | Política de atualização |
| [frontend/README.md](frontend/README.md) | Detalhes do frontend e acesso em rede |

---

## Solução de problemas

| Problema | Sugestão |
|----------|----------|
| Porta em uso | Feche outro ZELO ou altere `--port` em `run_desktop.py` |
| Tela em branco após build | Rode `npm run build` em `frontend/` antes do PyInstaller |
| Erro de licença | Verifique serial, HWID e `APPF_LICENSE_SECRET` / `tools/license_secret.local` |
| CPF já cadastrado | Esperado se o CPF já existe em contribuinte ativo |
| Firewall (rede local) | Libere portas **5173** e **8000** para `iniciar_rede.bat` |

Logs: `data\logs\zelo.log` (instalado) ou console/arquivo conforme modo de execução.

---

## Licença do projeto

Uso proprietário / cliente — consulte o contrato com o fornecedor do ZELO.

---

*ZELO — Contribuições APPF · FastAPI + React · Windows desktop*
