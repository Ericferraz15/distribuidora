# Distribuidora — Front-end

Painel web (React + Vite) que consome a **Distribuidora API** (FastAPI).
Cobre o sistema completo: login, operação de caixa, estoque, usuários e
dashboard administrativo — com tema claro/escuro.

## Requisitos

- Node.js 18+ e npm
- A API rodando (por padrão em `http://127.0.0.1:8000`) — veja o `DOCUMENTACAO.md` na raiz.

## Como rodar (desenvolvimento)

```bash
cd frontend
npm install
npm run dev
```

Abra `http://localhost:3000` (porta fixa em `vite.config.js`; outros aparelhos
da rede local acessam pelo IP da máquina). O Vite faz **proxy** das rotas da API
(`/auth`, `/produtos`, `/turnos`, ...) para `http://127.0.0.1:8000`, então não há
problema de CORS em desenvolvimento.

Faça login com o admin criado pelo `scripts/seed.py` da API.

## Build de produção

```bash
npm run build      # gera dist/
npm run preview    # serve o build localmente para conferência
```

Em produção o front e a API costumam ficar em hosts diferentes. Copie
`.env.example` para `.env` e defina `VITE_API_URL` com a URL da API:

```
VITE_API_URL=https://api.suadistribuidora.com
```

## Estrutura

```
frontend/
├── index.html
├── vite.config.js         # proxy dev + porta
├── src/
│   ├── main.jsx           # bootstrap (providers: tema, toast, auth, router)
│   ├── App.jsx            # rotas e guardas de acesso
│   ├── styles.css         # tema claro/escuro (CSS variables)
│   ├── api/client.js      # cliente HTTP: Bearer, refresh automático, erros
│   ├── auth/              # AuthContext + decode do JWT (perfil/permissão)
│   ├── theme/             # ThemeContext (claro/escuro persistido)
│   ├── components/        # Layout, Modal, Toast, ProtectedRoute
│   ├── lib/format.js      # formatação de moeda/data/rótulos
│   └── pages/             # Login, Dashboard, Operacao, Estoque, Usuarios
```

## Controle de acesso

- O perfil (`admin` / `funcionario`) é lido das claims do access token JWT
  (a API não expõe `/me`).
- Rotas **Dashboard** e **Usuários** exigem admin (`RNF03`); funcionários são
  redirecionados para **Operação**.
- A regra RN01 (só o dono do turno movimenta o caixa) é reforçada no back-end;
  o front desabilita as ações e avisa quando o turno é de outro usuário.
```
