#!/bin/sh
# Sobe o backend no container: roda o seed (idempotente — so cria o admin se o
# banco estiver vazio) e depois inicia o uvicorn.
#
# O retry existe porque o `depends_on` do compose so espera o container do
# Postgres INICIAR, nao ele estar pronto para aceitar conexoes.

# Chave JWT: se nao veio uma valida pelo ambiente/.env, o container cuida de
# si — gera uma chave forte na PRIMEIRA subida e guarda no volume /segredo,
# reutilizando-a dali em diante. Assim o sistema sobe sem configuracao
# nenhuma, sem precisar de chave fixa no codigo (que permitiria forjar login).
if [ "$(printf %s "${SECRET_KEY_JWT:-}" | wc -c)" -lt 32 ]; then
    ARQ_CHAVE="/segredo/chave_jwt"
    if [ ! -s "$ARQ_CHAVE" ]; then
        mkdir -p /segredo
        python -c "import secrets; print(secrets.token_urlsafe(48))" > "$ARQ_CHAVE"
        echo "Chave JWT gerada nesta primeira subida e guardada no volume."
    fi
    SECRET_KEY_JWT="$(cat "$ARQ_CHAVE")"
    export SECRET_KEY_JWT
fi

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
