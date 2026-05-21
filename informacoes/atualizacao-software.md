# Atualização de software — estratégia adotada

## Decisão

Foi escolhida a **Fase 1: atualização manual por release**, sem verificador automático embutido no aplicativo (por enquanto).

Cada correção ou melhoria é publicada como uma **nova versão numerada**, empacotada em `ZELO-Setup.exe`, e enviada ao cliente para instalação **por cima** da instalação existente.

Atualizações automáticas (download + instalador silencioso, `latest.json`, etc.) ficam registradas aqui como **evolução futura opcional**, não como escopo atual.

---

## Por que essa opção

| Vantagem | Observação |
|----------|------------|
| Simples de implementar e manter | Não exige servidor de updates nem alteração no `ZELO.exe` |
| Controle total do que cada cliente recebe | Você decide quando e para quem enviar |
| Compatível com o modelo atual | Instalador Inno Setup + pasta `data/` local + licença por máquina |
| Menor risco em campo | Cliente vê o assistente de instalação e pode fazer backup antes |

| Limite | Mitigação |
|--------|-----------|
| Depende do cliente executar o instalador | Enviar instruções curtas (ver abaixo) e confirmar a versão após instalar |
| Não há aviso “há atualização” dentro do app | Comunicação por e-mail/WhatsApp com número da versão |

---

## O que é atualizado e o que não é

### Atualiza com o instalador (`ZELO-Setup.exe`)

- Executável `ZELO.exe` e bibliotecas empacotadas (PyInstaller)
- Interface web (build do `frontend/`)
- Regras de negócio no backend (Python/FastAPI dentro do pacote)
- Migrações do banco executadas na **primeira abertura** após a atualização (`app/config/database.py`)

### Não deve ser substituído na atualização

| Pasta / arquivo | Conteúdo |
|-----------------|----------|
| `{instalação}\data\` | Banco SQLite, logs, configurações locais |
| `{instalação}\data\assinaturas\` | Imagens de assinatura enviadas pelo cadastro |
| Licença já ativada na máquina | Permanece válida (mesmo HWID) |

O script do instalador está configurado para **não apagar** `data\*` em reinstalações/atualizações. Mesmo assim, recomenda-se backup antes de versões grandes.

---

## Fluxo para você (fornecedor)

1. **Desenvolver e testar** localmente (`python run_desktop.py` e/ou `dist\ZELO\`).
2. **Definir a versão** (ex.: `1.2.0`) e anotar mudanças (changelog curto).
3. **Gerar o instalador:**
   ```bat
   build\build_installer.bat
   ```
   Saída: `dist\ZELO-Setup.exe` (renomear se quiser, ex.: `ZELO-Setup-1.2.0.exe`).
4. **Testar atualização “por cima”** em um PC com versão anterior e pasta `data\` preenchida.
5. **Enviar ao cliente** o instalador + instruções (seção abaixo) + resumo das novidades.
6. **Registrar** data, versão e cliente (planilha ou issue interna).

Detalhes de build: [BUILD.md](../BUILD.md).

---

## Fluxo para o cliente (instalação da atualização)

1. **Fechar o ZELO** — ícone na bandeja do sistema → **Encerrar ZELO** (ou encerrar pelo Gerenciador de Tarefas se necessário).
2. **Opcional — backup:** copiar a pasta `data` (ex.: `C:\ZELO\data`) para pendrive ou outra pasta.
3. **Executar** o novo `ZELO-Setup.exe` recebido.
4. Escolher a **mesma pasta** da instalação anterior (ex.: `C:\ZELO`) quando o assistente perguntar.
5. Concluir o assistente e abrir o ZELO pelo atalho da área de trabalho.
6. **Conferir** login, licença, contribuintes e um recibo/relatório de teste.

Mensagem sugerida ao cliente:

> Atualização ZELO vX.Y.Z — Feche o programa pela bandeja, execute o instalador na mesma pasta de sempre (ex.: C:\ZELO). Seus dados em `data` são mantidos. Em caso de dúvida, faça cópia da pasta `data` antes de instalar.

---

## Versionamento sugerido

Use **SemVer** simplificado: `MAIOR.MENOR.CORREÇÃO`

- **MAIOR** — mudança grande ou incompatível (rara).
- **MENOR** — funcionalidade nova.
- **CORREÇÃO** — bugfix, ajuste de PDF, performance, etc.

Exemplo de changelog (enviar junto com o instalador):

```text
ZELO 1.2.0 (20/05/2026)
- Relatórios PDF: tabela e rodapé ajustados
- Cadastro: permite mesmo nome com CPF diferente
- Correções diversas na bandeja do sistema
```

*(Quando houver arquivo `APP_VERSION` no código, manter o mesmo número da release.)*

---

## Checklist rápido antes de enviar

Ver lista completa: [checklist-release.md](./checklist-release.md).

- [ ] Versão e changelog definidos
- [ ] `build\build_installer.bat` executado sem erro
- [ ] Teste de instalação por cima com `data\` existente
- [ ] Migrações SQLite testadas com banco antigo
- [ ] Licença e login OK após atualizar
- [ ] Cliente informado sobre fechar o ZELO antes de instalar

---

## Backup recomendado

Antes de atualizações importantes, orientar cópia de:

- `{pasta instalada}\data\appf_local.sqlite3` (ou nome do SQLite em uso)
- `{pasta instalada}\data\assinaturas\`
- `{pasta instalada}\data\logs\` (opcional, para suporte)

---

## Evolução futura (não implementada)

Se no futuro for necessário reduzir trabalho manual:

- Endpoint ou arquivo `latest.json` com versão, URL do instalador e hash SHA256
- Item na bandeja: **Verificar atualização**
- Instalação silenciosa Inno (`/SILENT`) após fechar o ZELO

Até lá, permanece a política deste documento: **release versionada + instalador + comunicação ao cliente**.

---

## Referências no repositório

| Item | Caminho |
|------|---------|
| Build e instalador | `BUILD.md`, `build\build_installer.bat`, `build\installer.iss` |
| Dados do usuário | `app/runtime_paths.py` → pasta `data/` |
| Migrações de banco | `app/config/database.py` |
| Credenciais de teste (local) | `CREDENCIAIS.local.md` (não versionar) |

---

*Última revisão da estratégia: maio/2026 — Fase 1 (atualização manual).*
