#!/usr/bin/env bash
# ============================================================================
# Instalacao completa da P12 Distribuidora (banco + API + painel via Docker).
#
# O que faz:
#   1. Confere pre-requisitos (docker + docker compose rodando).
#   2. Cria o .env a partir do .env.example com SECRET_KEY_JWT gerada na hora.
#   3. Builda e sobe os 3 containers (db, backend, frontend).
#   4. Espera o sistema responder e valida painel + API.
#
# Uso (na raiz do repositorio):
#   ./instalar.sh
#
# Para o notebook-servidor da loja (celulares acessando pela rede local):
#   EXPOR_REDE=1 ./instalar.sh
# Sem isso o painel fica acessivel so na propria maquina (127.0.0.1).
#
# Rodar de novo e seguro: nao apaga dados do banco (volume persiste) e nao
# sobrescreve um .env ja existente.
# ============================================================================
set -euo pipefail

cd "$(dirname "$0")"

# --- 1. Pre-requisitos -------------------------------------------------------
if ! command -v docker >/dev/null 2>&1; then
    echo "ERRO: docker nao instalado. Instale com:" >&2
    echo "  curl -fsSL https://get.docker.com | sh" >&2
    echo "  sudo usermod -aG docker \$USER   # e relogue" >&2
    exit 1
fi

if docker compose version >/dev/null 2>&1; then
    COMPOSE="docker compose"
elif command -v docker-compose >/dev/null 2>&1; then
    COMPOSE="docker-compose"
else
    echo "ERRO: docker compose nao encontrado (plugin ou binario)." >&2
    exit 1
fi

if ! docker info >/dev/null 2>&1; then
    echo "ERRO: o daemon do Docker nao esta rodando (ou o usuario nao tem" >&2
    echo "permissao). Tente: sudo systemctl start docker" >&2
    exit 1
fi

# --- 2. .env com chave JWT forte --------------------------------------------
# A API se recusa a subir com SECRET_KEY_JWT ausente/fraca, entao a instalacao
# gera uma chave aleatoria de verdade em vez de deixar o placeholder do example.
if [ -f .env ]; then
    echo "-> .env ja existe; mantendo o atual."
else
    if command -v openssl >/dev/null 2>&1; then
        CHAVE="$(openssl rand -base64 48 | tr -d '\n=/+' )"
    else
        CHAVE="$(head -c 48 /dev/urandom | base64 | tr -d '\n=/+')"
    fi
    sed "s|^SECRET_KEY_JWT=.*|SECRET_KEY_JWT=\"${CHAVE}\"|" .env.example > .env
    echo "-> .env criado com SECRET_KEY_JWT gerada automaticamente."
fi

# --- 3. Exposicao na rede local (opcional) ----------------------------------
# O compose le PAINEL_BIND do .env para decidir onde publicar a porta 80.
# (Versoes antigas deste script usavam docker-compose.override.yml, que o
# compose SOMA em vez de substituir — a porta era aberta duas vezes e a
# subida falhava com "address already in use". Por isso o rm abaixo.)
rm -f docker-compose.override.yml
if [ "${EXPOR_REDE:-0}" = "1" ]; then
    BIND="0.0.0.0"
    echo "-> Painel sera exposto na rede local (porta 80 em todas as interfaces)."
else
    BIND="127.0.0.1"
    echo "-> Painel acessivel so nesta maquina. Para a rede local: EXPOR_REDE=1 ./instalar.sh"
fi
if grep -q '^PAINEL_BIND=' .env; then
    sed -i "s|^PAINEL_BIND=.*|PAINEL_BIND=${BIND}|" .env
else
    printf '\n# Interface onde o painel escuta (0.0.0.0 = rede local toda).\nPAINEL_BIND=%s\n' "$BIND" >> .env
fi

# --- 4. Build e subida -------------------------------------------------------
echo "-> Buildando e subindo containers (a primeira vez demora alguns minutos)..."
$COMPOSE up -d --build

# --- 5. Validacao ------------------------------------------------------------
# O entrypoint do backend ja tem retry proprio esperando o Postgres; aqui so
# esperamos a ponta final (nginx -> backend) responder.
echo -n "-> Esperando o sistema responder"
for i in $(seq 1 30); do
    if curl -sf -o /dev/null http://127.0.0.1/; then
        break
    fi
    if [ "$i" -eq 30 ]; then
        echo
        echo "ERRO: painel nao respondeu apos 60s. Veja os logs com:" >&2
        echo "  $COMPOSE logs" >&2
        exit 1
    fi
    echo -n "."
    sleep 2
done
echo " ok"

# API atraves do proxy do nginx: GET em /auth/login devolve 405 (rota e POST),
# o que prova que nginx -> backend esta de pe. 502/504 = backend ainda fora.
# Em maquina lenta o backend demora (Postgres inicializando + seed com retry),
# entao insistimos por ate 90s antes de declarar erro.
echo -n "-> Esperando a API responder"
STATUS="000"
for _ in $(seq 1 45); do
    STATUS="$(curl -s -o /dev/null -w '%{http_code}' -H 'Accept: application/json' http://127.0.0.1/auth/login || echo 000)"
    case "$STATUS" in
        502|504|000) echo -n "."; sleep 2 ;;
        *) break ;;
    esac
done
echo
case "$STATUS" in
    502|504|000)
        echo "ERRO: painel de pe mas a API nao respondeu apos 90s (HTTP $STATUS)." >&2
        echo "Veja o que o backend esta dizendo:  $COMPOSE logs backend" >&2
        exit 1 ;;
esac
echo "-> API respondendo (HTTP $STATUS em /auth/login)."

# --- 6. Resumo ---------------------------------------------------------------
IP_LOCAL="$(hostname -I 2>/dev/null | awk '{print $1}')"
echo
echo "============================================================"
echo " Instalacao concluida!"
echo
echo "   Painel:  http://127.0.0.1/"
if [ "${EXPOR_REDE:-0}" = "1" ] && [ -n "$IP_LOCAL" ]; then
    echo "   Na rede: http://${IP_LOCAL}/"
fi
echo "   Login inicial: admin / admin123  (TROQUE a senha!)"
echo
echo " Proximos passos no notebook-servidor da loja:"
echo "   - IP fixo para esta maquina no roteador."
echo "   - Notebook configurado para nao suspender com a tampa fechada."
echo "   - Backup diario: agende scripts/backup_banco.sh no cron"
echo "     (instrucoes no cabecalho do proprio script)."
echo "============================================================"
