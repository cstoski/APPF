# Gerar executável e instalador ZELO (Windows)

## Ícone do programa

Coloque o logo em `ZeloAppfIco.png` na raiz e gere o `.ico`:

```bat
tools\gerar_icone.bat
```

O build (`build_exe.bat`) regenera o ícone automaticamente se o PNG existir.

## Pré-requisitos

- Python 3.11+ com `pip install -r requirements.txt`
- Node.js 18+ (para build do frontend)
- PyInstaller (`pip install pyinstaller`)
- **Inno Setup 6** (só para o instalador): https://jrsoftware.org/isdl.php

## Instalador (recomendado)

Gera o programa **sem janela de prompt**, empacota tudo e cria `dist\ZELO-Setup.exe`:

```bat
build\build_installer.bat
```

O assistente de instalação:

- Sugere **`C:\ZELO`**, mas você pode escolher **outra pasta**
- Cria atalho **ZELO** na área de trabalho (com ícone do programa)
- Não apaga a pasta `data` do usuário em atualizações (banco e logs)

Depois de instalar, use o atalho na área de trabalho ou o `ZELO.exe` na pasta escolhida.

## Apenas executável (sem instalador)

```bat
build\build_exe.bat
```

Saída em `dist\ZELO\` — copie a pasta inteira para outro PC.

## Comportamento em execução

| Modo | Console (prompt) |
|------|------------------|
| `ZELO.exe` / instalador | **Oculto** + ícone na **bandeja do sistema** |
| `python run_desktop.py` | Visível (desenvolvimento) |
| `python run_desktop.py --tray` | Bandeja (igual ao executável) |

### Bandeja do sistema (executável)

- **Abrir ZELO no navegador** — reabre a interface se o browser foi fechado
- **Status e serviços** — API, banco, licença e usuários conectados
- **Encerrar ZELO** — fecha servidor e processo

Se o ZELO já estiver rodando, clicar no atalho da área de trabalho **só abre o navegador** (não inicia segunda instância).

Usuários “conectados” = logins com atividade na API nos últimos **5 minutos**.

Logs do programa instalado: `{pasta instalada}\data\logs\zelo.log` (ex.: `C:\ZELO\data\logs\zelo.log`)

URL: http://127.0.0.1:8765 (navegador abre automaticamente)

## Testar sem empacotar

```bat
cd frontend
npm install
npm run build
cd ..
python run_desktop.py
```

## Credenciais iniciais

Logins, senhas e chave demo estão em **`CREDENCIAIS.local.md`** (arquivo local, não versionado no Git).

## Desinstalar

Painel de Controle → Programas → **ZELO**, ou o `unins000.exe` na pasta onde instalou.

Para manter o banco e as assinaturas enviadas no cadastro, faça backup da pasta `data` antes de desinstalar.

As imagens de assinatura (presidente/tesoureiro) ficam em `data/assinaturas/` e **não** são incluídas no executável — só após upload em **Configuração → APPF**.
