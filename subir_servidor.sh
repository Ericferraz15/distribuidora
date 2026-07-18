#!/usr/bin/env bash
# ============================================================================
# Sobe o sistema no NOTEBOOK-SERVIDOR da loja — comando unico, a prova de erro.
#
#   ./subir_servidor.sh
#
# O que faz, nessa ordem:
#   1. Pede sudo sozinho se o Docker exigir (nao precisa digitar sudo).
#   2. LIMPA a porta 80: derruba containers antigos/orfaos e para servidores
#      web do sistema (apache/nginx) que estejam no caminho.
#   3. Chama o instalar.sh ja no modo rede local (EXPOR_REDE=1).
#
# Nao apaga os dados do banco: o volume do Postgres e preservado sempre.
# ============================================================================
set -euo pipefail

cd "$(dirname "$0")"

# --- 1. Sudo automatico ------------------------------------------------------
# Se o usuario nao tem acesso ao Docker (grupo docker), reexecuta como root.
if ! docker info >/dev/null 2>&1; then
    if [ "$(id -u)" -ne 0 ]; then
        echo "-> Docker precisa de permissao de root aqui; pedindo senha do sudo..."
        exec sudo bash "$0" "$@"
    fi
    # Ja e root e mesmo assim falhou: daemon parado. Tenta ligar.
    echo "-> Daemon do Docker parado; iniciando..."
    systemctl start docker
    sleep 3
    docker info >/dev/null 2>&1 || { echo "ERRO: Docker nao subiu. Veja: systemctl status docker" >&2; exit 1; }
fi

# --- 2. Limpeza da porta 80 --------------------------------------------------
echo "-> Limpando a porta 80..."

# Servidores web instalados no proprio notebook (fora do Docker).
for SVC in apache2 nginx httpd; do
    if command -v systemctl >/dev/null 2>&1 && systemctl is-active --quiet "$SVC" 2>/dev/null; then
        echo "   - Parando e desativando o servico '$SVC' do sistema (ocupava a porta 80)."
        systemctl disable --now "$SVC" 2>/dev/null || sudo systemctl disable --now "$SVC"
    fi
done

# Containers desta stack (inclusive de versoes antigas em outras pastas).
if docker compose version >/dev/null 2>&1; then COMPOSE="docker compose"; else COMPOSE="docker-compose"; fi
$COMPOSE down --remove-orphans >/dev/null 2>&1 || true

# Qualquer outro container ainda publicando a porta 80.
SOBRAS="$(docker ps -aq --filter publish=80)"
if [ -n "$SOBRAS" ]; then
    echo "   - Removendo containers antigos presos na porta 80."
    docker rm -f $SOBRAS >/dev/null
fi

echo "   Porta 80 livre."

# --- 3. Instalacao no modo rede local ---------------------------------------
EXPOR_REDE=1 ./instalar.sh
