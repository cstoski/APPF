# Manual de treinamento — Trilha C (Implantação e suporte técnico)

**Público:** TI da escola, fornecedor, suporte N2, desenvolvedores.  
**Pré-requisito:** leitura resumida da trilha A; trilha B recomendada para licença e SMTP.  
**Roteiro de vídeos:** [treinamento.md](./treinamento.md) — módulos 15 a 17.  
**Tempo estimado (vídeos):** ~1 h 07 min.

---

## 1. Arquitetura de implantação

```text
┌─────────────────────────────────────────────────────────────┐
│  Navegador (Chrome / Edge) — React SPA (estático no exe)     │
└───────────────────────────┬─────────────────────────────────┘
                            │ HTTP
┌───────────────────────────▼─────────────────────────────────┐
│  FastAPI — porta 8765 (prod) ou 8000 (dev)                   │
│  PyInstaller one-folder ou uvicorn                             │
└───────────────────────────┬─────────────────────────────────┘
                            │
┌───────────────────────────▼─────────────────────────────────┐
│  SQLite: data/appf_local.sqlite3                             │
│  Arquivos: data/logs/, data/assinaturas/                      │
└─────────────────────────────────────────────────────────────┘
```

| Modo | Porta API | Porta UI | Entrada |
|------|-----------|----------|---------|
| **Produção (ZELO.exe)** | **8765** | (mesma origem) | `tools/run_desktop.py` ou instalador |
| **Desenvolvimento** | **8000** | **5173** (Vite) | `uvicorn` + `npm run dev` |
| **Rede (dev/lab)** | **8000** `0.0.0.0` | **5173** `host:true` | `tools/iniciar_rede.bat` |

Proxy Vite (`frontend/vite.config.js`): `/api`, `/ping`, `/static` → `http://127.0.0.1:8000`.

---

## Módulo 15 — Instalação e atualização (vídeos 15.1–15.2)

### Objetivos

Instalar o ZELO em Windows, localizar dados e aplicar atualização preservando o banco.

### Artefatos de entrega

| Arquivo | Origem | Uso |
|---------|--------|-----|
| `dist/ZELO-Setup.exe` | `build/build_installer.bat` + Inno Setup 6 | Instalação cliente |
| `dist/ZELO/` | `build/build_exe.bat` | Cópia portátil sem instalador |

### Pré-requisitos no PC cliente

- Windows 10/11 64 bits
- Sem necessidade de Python/Node no cliente (tudo embutido no instalador)
- Navegador moderno (Chrome, Edge)
- Espaço em disco: ~200 MB + crescimento do SQLite

### Procedimento — instalação limpa

1. Executar `ZELO-Setup.exe` como administrador (se política da escola exigir).
2. Escolher pasta — padrão sugerido **`C:\ZELO`** (editável).
3. Concluir assistente → atalho na área de trabalho.
4. Primeira execução:
   - Ícone na bandeja aparece.
   - Navegador abre `http://127.0.0.1:8765`.
   - Banco criado em `C:\ZELO\data\appf_local.sqlite3` (caminho conforme instalação).
5. Login inicial: ver `informacoes/CREDENCIAIS.local.md` (não versionado) — **alterar senha do `admin` imediatamente**.
6. Ativar licença (MASTER) — trilha B módulo 13.

### Estrutura pós-instalação

```text
C:\ZELO\                    (exemplo)
├── ZELO.exe
├── _internal\              (bibliotecas PyInstaller)
├── data\
│   ├── appf_local.sqlite3
│   ├── assinaturas\
│   └── logs\
│       ├── zelo.log
│       ├── acesso.log
│       ├── recibos.log
│       ├── emails.log
│       └── licencas.log
└── license_secret.local    (opcional — validação de serial)
```

### Comportamento do executável

| Recurso | Implementação |
|---------|---------------|
| Console | Oculto no `.exe` |
| Bandeja | `desktop_tray.py` |
| Instância única | Segundo processo só abre browser |
| Status | `GET /api/v1/desktop/status` (localhost only) |

### Migrações de banco

Executadas na **primeira abertura** após atualização (`app/config/database.py`).  
Verificar `data/logs/zelo.log` se houver erro de schema após upgrade.

### Atualização por cima (Fase 1)

Documento completo: [atualizacao-software.md](./atualizacao-software.md).

**Resumo técnico:**

| Atualiza | Preserva |
|----------|----------|
| `ZELO.exe`, DLLs, frontend embutido, código Python empacotado | `data/` inteira, licença por HWID, `license_secret.local` |

**Fluxo para o cliente:**

1. Backup de `data/` (recomendado).
2. Fechar ZELO — bandeja → **Encerrar**.
3. Executar novo `ZELO-Setup.exe` na **mesma pasta**.
4. Abrir sistema → menu **Sobre** → conferir versão.
5. Smoke test: login, listar contribuintes, abrir um recibo.

**Fluxo para o fornecedor:**

1. Bump de versão em `frontend/package.json` e metadados do backend se aplicável.
2. `build\build_installer.bat`
3. Testar upgrade em VM com `data/` de versão anterior.
4. Enviar instalador + changelog — [checklist-release.md](./checklist-release.md).

### Exercício

1. Instalar em VM Windows limpa.
2. Cadastrar 1 contribuinte + 1 recibo.
3. Simular atualização com segundo instalador (mesma pasta).
4. Confirmar que o recibo permanece.

---

## Módulo 16 — Rede local e múltiplos acessos (vídeo 16.1)

### Objetivos

Permitir acesso de outro PC ou celular na mesma LAN (ambiente laboratório ou piloto).

> **Produção recomendada:** um PC servidor com ZELO instalado; demais máquinas acessam via navegador na rede. O script abaixo é o modo **desenvolvimento** documentado no repositório.

### Script `tools/iniciar_rede.bat`

Executa em sequência:

1. Define `APPF_LICENSE_SECRET` (ambiente dev — **não** usar valor de produção em cliente real).
2. Inicia API: `uvicorn app.main:app --host 0.0.0.0 --port 8000`
3. Inicia Vite: `cd frontend && npm run dev` (porta **5173**, `host: true`)

Exibe o IPv4 local (ex.: `192.168.1.50`).

### URLs para estações cliente

| Destino | URL |
|---------|-----|
| Interface (obrigatório) | `http://<IP_SERVIDOR>:5173` |
| Swagger API (opcional) | `http://<IP_SERVIDOR>:8000/docs` |

**Não** apontar usuários finais só para `:8000` — a UI está no Vite em desenvolvimento.

### Firewall Windows

Liberar entrada **privada** para:

- TCP **5173** (frontend dev)
- TCP **8000** (API)

PowerShell (exemplo administrativo):

```powershell
New-NetFirewallRule -DisplayName "ZELO API 8000" -Direction Inbound -Protocol TCP -LocalPort 8000 -Action Allow -Profile Private
New-NetFirewallRule -DisplayName "ZELO Web 5173" -Direction Inbound -Protocol TCP -LocalPort 5173 -Action Allow -Profile Private
```

### Produção em rede (cenário escola)

Para uso contínuo em rede **sem** Vite:

1. Instalar ZELO no **PC servidor** (porta **8765**).
2. Descobrir IP do servidor (`ipconfig`).
3. Nas estações: `http://<IP>:8765` — testar se o firewall do servidor permite **8765** inbound.
4. **Licença:** vinculada ao HWID do **servidor** onde o serviço roda.
5. **Backup:** centralizado na pasta `data/` do servidor.

Limitação: documentação oficial do instalador assume localhost; exposição em LAN exige hardening (rede privada, sem exposição à internet).

### JWT e rede

Tokens são válidos no servidor que os emitiu (mesmo HWID na assinatura). Clientes na rede usam o mesmo backend — sem problema.

### Exercício

1. Do notebook, abrir `http://<IP>:5173` após `iniciar_rede.bat`.
2. Login e emitir recibo de teste.
3. Confirmar em `acesso.log` no servidor.

---

## Módulo 17 — Build e release (vídeos 17.1–17.2)

### Objetivos

Gerar instalador, validar qualidade e entregar ao cliente com rastreabilidade.

### Pipeline de build

```text
ZeloAppfIco.png
    → tools/gerar_icone.bat → ZeloAppfIco.ico
    → build/build_exe.bat → dist/ZELO/
    → build/build_installer.bat + Inno Setup → dist/ZELO-Setup.exe
```

### Pré-requisitos de máquina de build

| Ferramenta | Versão | Instalação |
|------------|--------|------------|
| Python | 3.11+ | `pip install -r requirements.txt` |
| Build extras | — | `pip install -r requirements-build.txt` |
| Node.js | 18+ | `cd frontend && npm install` |
| PyInstaller | — | incluído em requirements-build |
| Inno Setup | 6 | https://jrsoftware.org/isdl.php |

### Comandos

**Instalador completo (recomendado):**

```bat
build\build_installer.bat
```

**Somente pasta executável:**

```bat
build\build_exe.bat
```

**Teste local sem empacotar:**

```bat
cd frontend
npm run build
cd ..
python tools\run_desktop.py
```

### Frontend no pacote

`npm run build` gera `frontend/dist/` — incorporado ao PyInstaller no fluxo do `build_installer.bat`.

### Ícone

PNG na raiz: `ZeloAppfIco.png` (ou caminho configurado no script) → `tools/gerar_icone.bat`.

### Checklist de release (detalhado)

Arquivo: [checklist-release.md](./checklist-release.md).

#### Versão e comunicação

- [ ] Versão definida (ex. `1.2.0`) em `package.json` / metadados
- [ ] Changelog para cliente
- [ ] Nome opcional: `ZELO-Setup-1.2.0.exe`

#### Build

- [ ] `npm run build` sem erro
- [ ] `build_installer.bat` OK → `dist/ZELO-Setup.exe`

#### Testes em VM

- [ ] Instalação limpa → `http://127.0.0.1:8765`
- [ ] Login + licença
- [ ] Upgrade por cima mantém dados em `data/`
- [ ] Bandeja: abrir browser, status, encerrar
- [ ] Funcionalidades alteradas nesta release

#### Banco

- [ ] Abrir com cópia anonimizada de `data/` de cliente
- [ ] Migrações sem erro em `zelo.log`

#### Entrega

- [ ] Instrução: fechar pela bandeja antes de instalar
- [ ] Mesma pasta de instalação indicada
- [ ] Backup de `data/` recomendado
- [ ] Registro interno data/versão/cliente

### Licenças no build

Gerar serial de cliente:

```bat
set APPF_LICENSE_SECRET=<mesmo do cliente>
python tools\gerar_licenca.py --hwid <HWID>
```

Arquivo `license_secret.local` na instalação do cliente deve corresponder ao secret usado na geração.

### Ferramentas auxiliares (`tools/`)

| Script | Função |
|--------|--------|
| `criar_admin.py` | Criar/resetar admin em banco existente |
| `criar_master_cliente.py` | Master para ambiente cliente |
| `gerar_licenca.py` | Serial comercial |
| `run_desktop.py` | Desktop dev/prod local |
| `iniciar_rede.bat` | API + Vite em LAN |
| `iniciar_sistema.bat` | Atalho dev local |

### OpenAPI (suporte)

Com API rodando: `http://127.0.0.1:8765/docs` ou `:8000/docs` — lista completa de rotas `/api/v1/*`.

### Índice rápido de API (treinamento)

```text
/ping
/api/v1/auth/*
/api/v1/usuarios/*
/api/v1/appf*
/api/v1/contribuintes*
/api/v1/contribricoes*
/api/v1/dados/*
/api/v1/relatorios/*
/api/v1/dashboard/resumo
/api/v1/sistema/info | /licenca*
/api/v1/desktop/*
/static/assinaturas/*
```

### Desinstalação

Painel de Controle → **ZELO** ou `unins000.exe` na pasta de instalação.  
**Backup prévio de `data/`** se o cliente quiser reinstalar depois com histórico.

---

## Troubleshooting avançado

| Problema | Diagnóstico | Ação |
|----------|-------------|------|
| Porta 8765 em uso | `netstat -ano \| findstr 8765` | Encerrar processo ZELO órfão |
| Banco corrompido | Erro SQLite no `zelo.log` | Restaurar backup `appf_local.sqlite3` |
| Licença inválida após clone de VM | HWID mudou | Novo serial para novo HWID |
| Assinaturas 404 | Arquivo removido de `data/assinaturas` | Re-upload em Config APPF |
| Frontend branco pós-build | Build não embutido | Refazer `npm run build` + installer |
| E-mail em LAN ok mas não em produção | SMTP só no servidor certo | Configurar no PC que roda ZELO.exe |

### Logs para análise N2

Prioridade: `zelo.log` → `licencas.log` → `recibos.log` → `emails.log` → `acesso.log`.

---

## Avaliação final da trilha C

| Critério | Esperado |
|----------|----------|
| Build | Gerar `ZELO-Setup.exe` em ambiente dev |
| Instalação | VM com ZELO funcional em 8765 |
| Upgrade | Dados preservados após segundo instalador |
| Rede | Acesso a `:5173` de outro dispositivo na LAN (lab) |
| Release | Checklist preenchido para versão fictícia 1.0.1 |

---

## Referências cruzadas

- [BUILD.md](./BUILD.md)
- [atualizacao-software.md](./atualizacao-software.md)
- [checklist-release.md](./checklist-release.md)
- [treinamento-trilha-a-operacional.md](./treinamento-trilha-a-operacional.md)
- [treinamento-trilha-b-administrador.md](./treinamento-trilha-b-administrador.md)
- [README.md](../README.md) (visão geral do repositório)

*Atualizado: maio/2026.*
