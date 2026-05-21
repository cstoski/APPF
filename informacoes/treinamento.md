# Sequência de treinamento — ZELO (Contribuições APPF)

Roteiro sugerido para gravação ou consumo de vídeos de capacitação. Os tempos são **estimativas por vídeo** (fala + demonstração na tela), não incluem pausas nem exercícios práticos.

**Referências:** [Manual do usuário](../frontend/public/manual/index.html) · [README do projeto](../README.md)

### Manuais técnicos por trilha

| Trilha | Documento |
|--------|-----------|
| A — Operacional | [treinamento-trilha-a-operacional.md](./treinamento-trilha-a-operacional.md) |
| B — Administrador | [treinamento-trilha-b-administrador.md](./treinamento-trilha-b-administrador.md) |
| C — Implantação | [treinamento-trilha-c-implantacao.md](./treinamento-trilha-c-implantacao.md) |

---

## Como usar esta sequência

| Trilha | Público | Módulos | Tempo total (vídeos) |
|--------|---------|---------|----------------------|
| **A — Operacional** | Tesoureiro, secretaria, operador | 1 → 9 | **~2 h 05 min** |
| **B — Administrador** | MASTER (gestão da instituição) | 10 → 14 | **~1 h 37 min** |
| **C — Implantação e suporte** | TI, fornecedor, suporte interno | 15 → 17 | **~1 h 07 min** |

Recomendação: concluir a trilha **A** antes da **B**. A trilha **C** é opcional para quem só opera o dia a dia.

---

## Trilha A — Operacional (dia a dia)

### Módulo 1 — Primeiro contato com o ZELO

| # | Vídeo | Assunto | Tempo |
|---|--------|---------|-------|
| 1.1 | O que é o ZELO e para quem serve | Visão geral: contribuintes, recibos, relatórios, operação local/offline, nome comercial vs SGCV | 6 min |
| 1.2 | Como abrir o sistema no Windows | Atalho, ícone na bandeja, abrir no navegador (`127.0.0.1`), instância única, indicador de status da API | 8 min |
| 1.3 | Navegação e menu principal | Dashboard, Contribuintes, Recibos, Relatórios, Configuração; menu **Sobre** (versão, manual, suporte) | 5 min |

**Subtotal módulo 1:** 19 min

---

### Módulo 2 — Acesso e perfis

| # | Vídeo | Assunto | Tempo |
|---|--------|---------|-------|
| 2.1 | Login e troca de senha | Usuário/senha, sessão, boas práticas de credenciais | 5 min |
| 2.2 | Perfil Operador x Administrador (MASTER) | O que cada perfil pode ver e alterar; por que o operador não mexe em usuários nem na APPF | 7 min |

**Subtotal módulo 2:** 12 min

---

### Módulo 3 — Dashboard

| # | Vídeo | Assunto | Tempo |
|---|--------|---------|-------|
| 3.1 | Leitura do painel inicial | Indicadores, totais, visão anual; quando usar o dashboard na rotina | 8 min |

**Subtotal módulo 3:** 8 min

---

### Módulo 4 — Contribuintes

| # | Vídeo | Assunto | Tempo |
|---|--------|---------|-------|
| 4.1 | Cadastro e edição | Campos obrigatórios, nome, CPF, contato; salvamento e validações na tela | 12 min |
| 4.2 | Busca, exclusão lógica e reativação | Localizar por nome ou CPF; inativar e reativar sem perder histórico | 8 min |
| 4.3 | Regras de CPF e LGPD | CPF duplicado entre ativos (bloqueio); mesmo nome com CPF diferente (permitido); dados sensíveis cifrados | 10 min |

**Subtotal módulo 4:** 30 min

---

### Módulo 5 — Importação em lote

| # | Vídeo | Assunto | Tempo |
|---|--------|---------|-------|
| 5.1 | Planilha modelo e pré-visualização | Formato Excel, colunas esperadas, preview antes de confirmar | 10 min |
| 5.2 | Resultado da importação | Novos, atualizados e pulados; conferência pós-importação na lista de contribuintes | 7 min |

**Subtotal módulo 5:** 17 min

---

### Módulo 6 — Recibos e contribuições

| # | Vídeo | Assunto | Tempo |
|---|--------|---------|-------|
| 6.1 | Lançar uma contribuição | Selecionar contribuinte, data, valor, forma de pagamento, descrição; gerar recibo numerado | 12 min |
| 6.2 | PDF, impressão e duplicata na folha | Visualizar PDF, imprimir, opção de duas vias na mesma página | 8 min |
| 6.3 | Enviar recibo por e-mail e WhatsApp | Quando usar cada canal; pré-requisitos (e-mail do contribuinte, SMTP já configurado) | 10 min |
| 6.4 | Cancelar recibo | Motivo mínimo de 10 caracteres; efeito após cancelamento (sem reimpressão/envio) | 8 min |

**Subtotal módulo 6:** 38 min

---

### Módulo 7 — Relatórios

| # | Vídeo | Assunto | Tempo |
|---|--------|---------|-------|
| 7.1 | Relatório por contribuinte | Período, filtros, exportar PDF e Excel | 10 min |
| 7.2 | Relatório financeiro APPF | Mensal, anual, intervalo; resumo e gráfico no PDF anual | 12 min |

**Subtotal módulo 7:** 22 min

---

### Módulo 8 — Consulta da configuração (operador)

| # | Vídeo | Assunto | Tempo |
|---|--------|---------|-------|
| 8.1 | Dados da instituição em modo leitura | Razão social, CNPJ, endereço, nomes e assinaturas que aparecem no recibo; o que o operador **não** altera | 6 min |

**Subtotal módulo 8:** 6 min

---

### Módulo 9 — Boas práticas do operador

| # | Vídeo | Assunto | Tempo |
|---|--------|---------|-------|
| 9.1 | Rotina segura e conferência | Conferir valores antes de emitir recibo; não compartilhar login; uso do manual integrado | 5 min |
| 9.2 | O que fazer quando algo falha | API offline, erro de validação, mensagem de licença; quando acionar o administrador ou suporte | 8 min |

**Subtotal módulo 9:** 13 min

**Total trilha A:** ~2 h 05 min (19 vídeos)

---

## Trilha B — Administrador (MASTER)

### Módulo 10 — Configuração da APPF

| # | Vídeo | Assunto | Tempo |
|---|--------|---------|-------|
| 10.1 | Dados institucionais | Razão social, CNPJ, endereço, presidente e tesoureiro; impacto nos documentos gerados | 10 min |
| 10.2 | Assinaturas no recibo | Upload, preview, pasta `data/assinaturas/`; substituição sem recompilar o programa | 8 min |
| 10.3 | Texto padrão do recibo | Personalização do texto exibido no PDF | 6 min |

**Subtotal módulo 10:** 24 min

---

### Módulo 11 — E-mail (SMTP)

| # | Vídeo | Assunto | Tempo |
|---|--------|---------|-------|
| 11.1 | Configurar SMTP | Host, porta, STARTTLS/SSL, usuário, remetente; exemplos Gmail, Microsoft 365, hospedagem | 14 min |
| 11.2 | Testar e validar envio | Salvar e testar SMTP; interpretar sucesso e erros comuns | 8 min |

**Subtotal módulo 11:** 22 min

---

### Módulo 12 — Usuários e segurança

| # | Vídeo | Assunto | Tempo |
|---|--------|---------|-------|
| 12.1 | Cadastro de usuários | Criar operador e administrador; desativar acesso | 10 min |
| 12.2 | Logs operacionais (visão admin) | `acesso.log`, `recibos.log`, `emails.log`, `licencas.log`; o que procurar em auditoria | 9 min |

**Subtotal módulo 12:** 19 min

---

### Módulo 13 — Licenciamento

| # | Vídeo | Assunto | Tempo |
|---|--------|---------|-------|
| 13.1 | Ativar licença no equipamento | HWID, serial, validade 365 dias; perfil MASTER obrigatório | 10 min |
| 13.2 | Expiração, cortesia e modo demonstração | 7 dias só consulta após expirar; serial demo 3 dias, uma vez por máquina | 8 min |

**Subtotal módulo 13:** 18 min

---

### Módulo 14 — Backup e continuidade

| # | Vídeo | Assunto | Tempo |
|---|--------|---------|-------|
| 14.1 | Backup do banco e pastas críticas | `data/`, logs, assinaturas; frequência recomendada | 9 min |
| 14.2 | Contato com suporte | Menu Sobre, versão, e-mail/telefone; informações úteis ao abrir chamado | 5 min |

**Subtotal módulo 14:** 14 min

**Total trilha B:** ~1 h 37 min (9 vídeos) — *pode ser gravada após domínio da trilha A*

---

## Trilha C — Implantação e suporte (TI / fornecedor)

### Módulo 15 — Instalação e atualização

| # | Vídeo | Assunto | Tempo |
|---|--------|---------|-------|
| 15.1 | Instalar com `ZELO-Setup.exe` | Primeira execução, atalhos, pasta de dados | 12 min |
| 15.2 | Atualizar versão no cliente | Fluxo de release manual + instalador (ver [atualizacao-software.md](./atualizacao-software.md)) | 10 min |

**Subtotal módulo 15:** 22 min

---

### Módulo 16 — Rede local e múltiplos acessos

| # | Vídeo | Assunto | Tempo |
|---|--------|---------|-------|
| 16.1 | Acesso em rede na escola | Servidor + estações, firewall, URL na rede local (`tools/iniciar_rede.bat`) | 15 min |

**Subtotal módulo 16:** 15 min

---

### Módulo 17 — Build e release (equipe técnica)

| # | Vídeo | Assunto | Tempo |
|---|--------|---------|-------|
| 17.1 | Checklist antes de enviar ao cliente | Itens de [checklist-release.md](./checklist-release.md) em ordem prática | 12 min |
| 17.2 | Visão do processo de build | Resumo de [BUILD.md](./BUILD.md): PyInstaller, frontend, instalador Inno Setup | 18 min |

**Subtotal módulo 17:** 30 min

**Total trilha C:** ~1 h 07 min (5 vídeos)

---

## Resumo geral

| Trilha | Vídeos | Tempo estimado |
|--------|--------|----------------|
| A — Operacional | 19 | ~2 h 05 min |
| B — Administrador | 9 | ~1 h 37 min |
| C — Implantação / suporte | 5 | ~1 h 07 min |
| **Todas (sequência completa)** | **33** | **~4 h 49 min** |

Com exercícios práticos (cadastrar 3 contribuintes, emitir 2 recibos, gerar 1 relatório), reserve **+2 h** para a trilha A e **+1 h** para a trilha B.

---

## Ordem sugerida de gravação ou publicação

1. Módulos **1 → 2** (base para qualquer usuário)  
2. **4 → 6 → 7** (núcleo operacional)  
3. **3, 5, 8, 9** (complementos)  
4. Trilha **B** na ordem **10 → 14**  
5. Trilha **C** conforme demanda de implantação  

---

## Checklist por vídeo (produção)

- [ ] Resolução mínima 1920×1080; cursor visível  
- [ ] Dados fictícios (CPF/e-mail de exemplo), nunca dados reais de contribuintes  
- [ ] Mostrar versão no menu **Sobre** no início ou fim  
- [ ] Legenda ou roteiro alinhado ao [manual](../frontend/public/manual/index.html)  
- [ ] Card final: “Próximo vídeo: **X.Y — título**”

---

*Documento criado em maio/2026. Ajuste os tempos após a primeira rodada de gravação (regra prática: tempo final ≈ 1,2× a estimativa se houver muitas dúvidas reais de usuários).*
