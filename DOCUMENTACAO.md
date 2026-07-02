# Documentação — Distribuidora API

Sistema de gestão para uma distribuidora de bebidas com **operação 24 horas**.
Backend em **FastAPI + PostgreSQL (SQLAlchemy)**. Dois perfis de acesso:
**Administrador** e **Funcionário**. O foco é o controle de caixa em turnos
contínuos e a gestão básica de estoque, com responsabilidade sempre atrelada ao
usuário do turno.

---

## 1. Regras de Negócio

### RN01 — Vínculo de Responsabilidade
Apenas o funcionário **dono do turno ativo** pode registrar vendas e movimentar
aquele caixa.
- **Onde:** `services/transacao_service.py` → `_turno_do_usuario()` compara
  `current_user.id` com `turno.funcionario_id` (403 caso não seja o dono).
  O encerramento do turno aplica a mesma checagem em `turno_service.encerrar_turno`.

### RN02 — Transição de Caixa
Um novo turno/caixa **não** pode ser iniciado se houver um turno com status
`aberto`.
- **Onde:** `services/turno_service.py` → `abrir_turno()` verifica se já existe
  turno aberto (409). Reforço no banco: **índice único parcial**
  `uq_turno_unico_aberto` em `models/turno_model.py`
  (`unique WHERE status = 'aberto'`), que barra corridas de concorrência.

---

## 2. Requisitos → Implementação

| Requisito | Descrição | Implementação |
|-----------|-----------|---------------|
| **RF01** | Autenticação por perfis | `routes/login.py`, `security/dependencies.py` |
| **RF02** | Controle de turnos | `services/turno_service.py`, `routes/turnos.py` |
| **RF03** | Abertura/fechamento de caixa | `models/caixa_model.py`, `services/caixa_service.py`, `routes/caixa.py` |
| **RF04** | Registro de transações | `services/transacao_service.py`, `routes/transacoes.py` |
| **RF05** | Visualização de estoque | `GET /produtos` (`routes/estoque.py`) |
| **RF06** | Baixa de estoque na venda | `services/transacao_service.py` → `MovimentoEstoque` |
| **RF07** | Dashboard administrativo | `services/dashboard_service.py`, `routes/dashboard.py` |
| **RNF01** | Disponibilidade 24/7 | JWT stateless, `pool_pre_ping`, migrações Alembic (sem downtime) |
| **RNF02** | Tracking e auditoria | `funcionario_id` gravado em `Transacao` e `MovimentoEstoque` |
| **RNF03** | Controle de acesso | `require_admin` em `/usuarios` e `/dashboard` |
| **RNF04** | Desempenho | índices em FKs/status/data; consultas de caixa enxutas |

---

## 3. Estrutura do Projeto

```
projeto_max/
├── main.py                 # Cria a app FastAPI e registra todos os routers
├── database.py             # Engine, SessionLocal, Base e a dependência get_db()
├── alembic.ini, alembic/   # Migrações de schema (versionamento do banco)
├── scripts/seed.py         # Cria o administrador inicial (bootstrap)
│
├── models/                 # ORM SQLAlchemy (tabelas do banco)
│   ├── usuario_model.py     # Usuario
│   ├── turno_model.py       # Turno (+ índice único parcial RN02)
│   ├── caixa_model.py       # Caixa (1:1 com Turno)
│   ├── transacao_model.py   # Transacao + ItemVenda
│   └── estoque_model.py     # Produto + MovimentoEstoque
│
├── schemas/                # Pydantic: DTOs de request/response + modelos de domínio
│   ├── usuario.py, auth.py, turno.py, caixa.py, transacao.py,
│   └── estoque.py, dashboard.py
│
├── services/               # Regras de negócio (rotas ficam "magras")
│   ├── turno_service.py     # abrir/encerrar (RN01, RN02)
│   ├── caixa_service.py     # status/saldo do caixa
│   ├── transacao_service.py # venda atômica + baixa de estoque (RF04/RF06/RNF02)
│   ├── estoque_service.py   # CRUD de produtos e reposição
│   └── dashboard_service.py # agregações (faturamento, mais vendidos)
│
├── security/               # Autenticação
│   ├── gerenciador_senha.py # hash bcrypt
│   ├── gerenciador_jwt.py   # tokens access/refresh
│   └── dependencies.py      # get_current_user, require_admin
│
├── routes/                 # Endpoints HTTP
│   ├── login.py (/auth), usuarios.py, turnos.py, caixa.py,
│   └── transacoes.py, estoque.py, dashboard.py
│
└── tests/                  # pytest (unitários de domínio + integração TestClient)
```

**Camadas:** `routes` (HTTP) → `services` (regras) → `models` (ORM) → banco.
`schemas` validam entrada/saída; `security` cuida de identidade e permissão.

---

## 4. Modelo de Dados

| Entidade | Campos principais | Relações |
|----------|-------------------|----------|
| **Usuario** | `id, nome, senha_hash, permissao, numero_telefone, ativo` | 1:N Turno |
| **Turno** | `id, funcionario_id, data_abertura, data_fechamento, status` | N:1 Usuario · 1:1 Caixa |
| **Caixa** | `id, turno_id, saldo_inicial, saldo_final_informado, abertura, fechamento` | 1:1 Turno · 1:N Transacao |
| **Transacao** | `id, caixa_id, funcionario_id, tipo, categoria, valor, metodo_pagamento, data` | N:1 Caixa · 1:N ItemVenda |
| **ItemVenda** | `id, transacao_id, produto_id, quantidade, valor_unitario` | N:1 Transacao · N:1 Produto |
| **Produto** | `id, nome, valor, quantidade, fornecedor, descricao, ativo` | — |
| **MovimentoEstoque** | `id, produto_id, quantidade, tipo, data, funcionario_id, transacao_id, motivo` | N:1 Produto |

- **tipo** da transação: `entrada` | `saida`.
- **categoria**: `venda` | `sangria` | `despesa` | `suprimento`.
- **status** do turno: `aberto` | `encerrado`.

---

## 5. Endpoints

| Método | Rota | Acesso |
|--------|------|--------|
| POST | `/auth/login` | público |
| POST | `/auth/refresh` | público (refresh token) |
| POST | `/auth/logout` | autenticado |
| GET | `/auth/me` | autenticado (perfil do usuário logado) |
| POST · GET · PATCH | `/usuarios` · `/usuarios/{id}` | **admin** (RNF03) |
| POST | `/turnos/abrir` | autenticado |
| POST | `/turnos/encerrar` | dono do turno (RN01) |
| GET | `/turnos/ativo` | autenticado |
| GET | `/caixa/atual` | autenticado |
| POST | `/caixa/fechar` | dono do turno (RN01) |
| POST | `/transacoes/venda` | dono do turno (RN01) |
| POST | `/transacoes/saida` | dono do turno (RN01) |
| GET | `/transacoes` | autenticado |
| GET | `/produtos` | autenticado (RF05) |
| POST · PATCH | `/produtos` · `/produtos/{id}` | **admin** |
| POST | `/produtos/{id}/entrada` | **admin** (reposição) |
| GET | `/dashboard/resumo` | **admin** (RF07/RNF03) |
| GET | `/dashboard/mais-vendidos` | **admin** |
| GET | `/dashboard/caixa-status` | **admin** |

Documentação interativa (Swagger): **`/docs`**.

---

## 6. Fluxo Típico de Operação

1. **Login** (`/auth/login`) → recebe `access_token` e `refresh_token`.
2. Funcionário **abre o turno** (`/turnos/abrir`) informando o `saldo_inicial`
   (cria o Caixa). *Bloqueado se já houver turno aberto — RN02.*
3. Durante o turno, registra **vendas** (`/transacoes/venda`) — cada venda baixa
   o estoque (RF06) e grava o `funcionario_id` (RNF02) — e **saídas**
   (`/transacoes/saida`: sangria/despesa).
4. Consulta o **caixa** (`/caixa/atual`) e o **estoque** (`/produtos`) a qualquer
   momento.
5. Ao final, **encerra o turno** (`/turnos/encerrar`) informando o saldo final
   (conferência). *Apenas o dono encerra — RN01.*
6. O **admin** acompanha tudo pelo **dashboard** (`/dashboard/*`).

---

## 7. Como Executar

### Pré-requisitos
- Python 3.12+ e um servidor **PostgreSQL** em execução.

### Passos
```bash
# 1. Ambiente e dependências
python -m venv venv && source venv/bin/activate
pip install -r requirements.txt

# 2. Configuração (copie e edite)
cp .env.example .env         # ajuste DATABASE_URL e SECRET_KEY_JWT

# 3. Banco: crie as tabelas via Alembic
alembic revision --autogenerate -m "init"   # gera a 1ª migração
alembic upgrade head

# 4. Admin inicial
python scripts/seed.py       # cria usuário admin (ADMIN_NOME/ADMIN_SENHA)

# 5. Suba a API
python main.py               # http://127.0.0.1:8000/docs
```
> Em desenvolvimento, a app também cria as tabelas no startup
> (`Base.metadata.create_all`). Em produção, prefira **Alembic**.

### Testes
```bash
pytest        # unitários de domínio + integração (SQLite em memória)
```

---

## 8. Autenticação e Segurança

- **Senhas:** hash **bcrypt** com salt (`security/gerenciador_senha.py`).
  Cadastro exige 6–72 caracteres (72 bytes é o limite do próprio bcrypt).
- **Tokens:** **JWT** HS256 (`security/gerenciador_jwt.py`) — `access` (1h) e
  `refresh` (7 dias). Renovação em `/auth/refresh`. A API **se recusa a subir**
  se `SECRET_KEY_JWT` estiver ausente ou tiver menos de 32 caracteres
  (fail-fast: chave fraca permitiria forjar tokens de admin).
- **Autorização:** `get_current_user` valida o token e **recarrega o usuário do
  banco** a cada requisição (permissão/ativo sempre atuais); `require_admin`
  restringe rotas administrativas (RNF03).
- **Login endurecido:** usuário inexistente, senha errada e conta desativada
  respondem o mesmo 401, e um hash "isca" equaliza o tempo de resposta —
  impede descobrir quais usuários existem (user enumeration por timing).
- **Anti-lockout:** um admin não pode rebaixar nem desativar a si mesmo
  (`routes/usuarios.py`), evitando um sistema sem nenhum administrador.
- **Concorrência:** a venda tranca a linha do produto (`SELECT ... FOR UPDATE`)
  antes de baixar o estoque — duas vendas simultâneas não vendem além do saldo.
- **Validação espelhada no schema:** limites de tamanho dos DTOs Pydantic
  seguem as colunas do banco (`String(120)`, `Numeric(12,2)`…), transformando
  erros de banco (500) em respostas 422 claras.
- **CORS:** origens liberadas via `CORS_ORIGINS` no `.env`; sem
  `allow_credentials` porque a auth viaja no header `Authorization`, não em cookies.
- **Auditoria (RNF02):** toda `Transacao` e todo `MovimentoEstoque` guardam o
  `funcionario_id` do turno ativo — nunca vindo do corpo da requisição.
- **Fuso do negócio:** timestamps gravados em UTC; o "dia" do dashboard segue
  `FUSO_NEGOCIO` (padrão `America/Sao_Paulo`) — venda das 22h não cai em "amanhã".
