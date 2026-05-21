# Checklist — release para cliente (Fase 1)

Use antes de enviar cada `ZELO-Setup.exe`.

## Versão e comunicação

- [ ] Número da versão definido (ex.: `1.2.0`)
- [ ] Changelog curto escrito para o cliente
- [ ] Nome do arquivo do instalador identifica a versão (opcional: `ZELO-Setup-1.2.0.exe`)

## Build

- [ ] `frontend`: `npm run build` incluído no fluxo do `build_installer.bat`
- [ ] `build\build_installer.bat` concluído sem erros
- [ ] Arquivo gerado: `dist\ZELO-Setup.exe`

## Testes (máquina de teste)

- [ ] Instalação limpa abre em http://127.0.0.1:8765
- [ ] Login e licença funcionam
- [ ] Atualização **por cima** na mesma pasta mantém contribuintes/recibos em `data\`
- [ ] Bandeja: abrir navegador, status, encerrar
- [ ] Funções alteradas nesta release testadas (ex.: relatório PDF, cadastro)

## Banco de dados

- [ ] Abrir app com cópia de um `data\` antigo de cliente (ou backup real anonimizado)
- [ ] Migrações em `database.py` rodam sem erro no log (`data\logs\zelo.log`)

## Entrega ao cliente

- [ ] Instrução enviada: fechar ZELO pela bandeja antes de instalar
- [ ] Mesma pasta de instalação indicada (ex.: `C:\ZELO`)
- [ ] Backup de `data\` recomendado para mudanças grandes
- [ ] Data da entrega e versão registradas (controle interno)

## Pós-instalação (confirmação com cliente)

- [ ] Cliente consegue abrir o sistema
- [ ] Versão/correção esperada validada
- [ ] Sem perda de dados reportada

---

Estratégia geral: [atualizacao-software.md](./atualizacao-software.md)
