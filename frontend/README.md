# APPF Frontend

Frontend React para APPF.

## Scripts

- `npm install`
- `npm run dev`
- `npm run build`
- `npm run preview`

## Configuração

- O proxy de desenvolvimento está configurado para `http://127.0.0.1:8000`.
- A API chama rotas como `/auth/token`, `/dados/importar`, `/dados/importar/preview-detalhado`.

## Acesso pelo celular (mesma Wi-Fi)

1. Na raiz do projeto, execute `iniciar_rede.bat` (API em `0.0.0.0:8000` + Vite com `host: true`).
2. No celular, abra **`http://IP_DO_PC:5173`** (não use só a porta 8000 — essa é só a API).
3. Descubra o IP no PC com `ipconfig` (IPv4 da rede Wi-Fi).
4. Se não carregar, permita **portas 5173 e 8000** no Firewall do Windows para redes privadas.
