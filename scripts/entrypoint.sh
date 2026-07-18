#!/bin/sh
# Sobe o backend no container: roda o seed (idempotente — so cria o admin se o
# banco estiver vazio) e depois inicia o uvicorn.
#
# O retry existe porque o `depends_on` do compose so espera o container do
# Postgres INICIAR, nao ele estar pronto para aceitar conexoes.

tentativas=0
until python scripts/seed.py; do
    tentativas=$((tentativas + 1))
    if [ "$tentativas" -ge 15 ]; then
        echo "Banco nao respondeu apos ${tentativas} tentativas; abortando." >&2
        exit 1
    fi
    echo "Banco ainda indisponivel (tentativa ${tentativas}); nova em 2s..."
    sleep 2
done

exec uvicorn main:app --host 0.0.0.0 --port 8000
