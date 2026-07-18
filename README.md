# P12 Distribuidora

Sistema de gestão de **caixa em turnos** e **estoque** para uma distribuidora de
bebidas com operação 24h. Feito para rodar em um notebook na loja, servindo os
celulares/computadores da equipe pela rede local.

| Camada | Stack | Pasta |
|--------|-------|-------|
| API | FastAPI + SQLAlchemy + PostgreSQL | raiz (`main.py`, `routes/`, `services/`…) |
| Painel web | React + Vite | `frontend/` |

- **[DOCUMENTACAO.md](DOCUMENTACAO.md)** — regras de negócio, arquitetura, modelo de dados, endpoints.
- **[frontend/README.md](frontend/README.md)** — detalhes do painel.

## Instalação completa (Docker)

```bash
./subir_servidor.sh           # notebook-servidor da loja: limpa a porta 80,
                              # cuida do sudo e sobe tudo aberto pra rede local
./instalar.sh                 # instalação só nesta máquina (127.0.0.1)
```

O script confere o Docker, gera o `.env` com chave JWT forte e sobe banco,
API e painel de uma vez. Rodar de novo é seguro (não apaga dados do banco
nem sobrescreve um `.env` existente).

## Subindo tudo (desenvolvimento)

```bash
# 1. Banco (PostgreSQL em Docker)
docker run -d --name distribuidora-db -p 5432:5432 \
  -e POSTGRES_PASSWORD=postgres -e POSTGRES_DB=distribuidora \
  -v distribuidora-dados:/var/lib/postgresql/data \
  postgres:16-alpine

# 2. API
python -m venv venv && source venv/bin/activate
pip install -r requirements.txt
cp .env.example .env        # gere sua SECRET_KEY_JWT (instruções no arquivo)
python scripts/seed.py      # cria o admin inicial (ADMIN_NOME/ADMIN_SENHA do .env)
python main.py              # http://127.0.0.1:8000/docs

# 3. Painel (outro terminal)
cd frontend && npm install && npm run dev   # http://localhost:3000
```

Login inicial: o usuário/senha definidos em `ADMIN_NOME`/`ADMIN_SENHA` do `.env`
(**troque a senha padrão antes de usar de verdade**).

## Testes

```bash
pytest                      # backend (SQLite em memória, não toca no Postgres)
cd frontend && npm test     # frontend (Vitest + MSW)
```

## Usando na loja (notebook como servidor)

1. Dê um **IP fixo** ao notebook no roteador da loja (ex.: `192.168.0.10`).
2. Suba API e painel como acima — o Vite já escuta a rede (`host: true`), então
   os celulares acessam `http://192.168.0.10:3000`.
3. No `.env`, restrinja o CORS: `CORS_ORIGINS="http://192.168.0.10:3000"`.
4. Configure o notebook para **não suspender** com a tampa fechada.
5. **Backup diário do banco** (o mais importante — sem isso, um HD queimado
   leva vendas e estoque juntos):

```bash
docker exec distribuidora-db pg_dump -U postgres distribuidora > backup_$(date +%F).sql
```

Agende no cron e copie o arquivo para fora do notebook (pendrive/nuvem).
